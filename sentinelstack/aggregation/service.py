import asyncio
import datetime
from sqlalchemy import select, func, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from sentinelstack.database import AsyncSessionLocal
from sentinelstack.logging.models import RequestLog
from sentinelstack.aggregation.models import RequestMetric

class AggregationService:
    def __init__(self):
        self.is_running = False

    async def aggregate_last_period(self, session: AsyncSession, period_minutes: int = 1):
        """
        Aggregates logs from the implementation period into the metrics table.
        This handles the heavy lifting so dashboards don't have to.
        """
        now = datetime.datetime.utcnow()
        # Round down to nearest minute to get a clean bucket
        bucket_end = now.replace(second=0, microsecond=0)
        bucket_start = bucket_end - datetime.timedelta(minutes=period_minutes)

        try:
            # 1. Check if we already aggregated this bucket (Idempotency)
            # In a real distributed system, use Redis Lock here.
            stmt_check = select(RequestMetric).where(RequestMetric.bucket_time == bucket_start).limit(1)
            existing = await session.execute(stmt_check)
            if existing.scalar():
                # print(f"DEBUG:   Metrics for {bucket_start} already exist. Skipping.")
                return

            # 2. Perform Segregated Aggregation (Group By)
            # We calculate stats per (method, path, status) group
            stmt = (
                select(
                    RequestLog.method,
                    RequestLog.path,
                    RequestLog.status_code,
                    func.count(RequestLog.id).label("count"),
                    func.sum(case((RequestLog.error_flag == True, 1), else_=0)).label("errors"),
                    func.avg(RequestLog.latency_ms).label("avg_latency")
                )
                .where(RequestLog.timestamp >= bucket_start)
                .where(RequestLog.timestamp < bucket_end)
                .group_by(RequestLog.method, RequestLog.path, RequestLog.status_code)
            )

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                return

            # 3. Bulk Insert Metrics
            metrics_to_insert = []
            for row in rows:
                metrics_to_insert.append(RequestMetric(
                    bucket_time=bucket_start,
                    method=row.method,
                    path=row.path,
                    status_code=row.status_code,
                    total_requests=row.count,
                    total_errors=row.errors or 0, # Handle None from SUM
                    avg_latency_ms=float(row.avg_latency) if row.avg_latency else 0.0,
                    p95_latency_ms=0.0 # Placeholder for advanced calc
                ))

            session.add_all(metrics_to_insert)
            await session.commit()
            print(f"INFO:    Aggregated {len(metrics_to_insert)} metric groups for {bucket_start}")
            
            # 4. Trigger Incident Check
            from sentinelstack.incidents.service import incident_service
            await incident_service.check_thresholds(session, bucket_start)

        except Exception as e:
            print(f"ERROR:   Aggregation failed: {e}")
            await session.rollback()

    async def worker(self):
        """Background task that triggers aggregation every minute."""
        self.is_running = True
        print("INFO:    Aggregation Worker Started")
        
        while self.is_running:
            # Sleep first to align with next minute boundary
            now = datetime.datetime.utcnow()
            next_minute = (now + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)
            delay = (next_minute - now).total_seconds() + 2 # +2s buffer
            
            await asyncio.sleep(delay)
            
            async with AsyncSessionLocal() as db:
                await self.aggregate_last_period(db)

# Global Instance
aggregation_service = AggregationService()
