import datetime
from sqlalchemy import select, func
from sentinelstack.database import AsyncSessionLocal
from sentinelstack.logging.models import RequestLog

class StatsService:
    async def get_dashboard_metrics(self, minutes: int = 60):
        try:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
            
            async with AsyncSessionLocal() as db:
                # 1. Total Requests
                result_total = await db.execute(
                    select(func.count(RequestLog.id)).where(RequestLog.timestamp >= cutoff)
                )
                total_requests = result_total.scalar() or 0
                
                # 2. Error Count
                result_error = await db.execute(
                    select(func.count(RequestLog.id))
                    .where(RequestLog.timestamp >= cutoff)
                    .where(RequestLog.error_flag == True)
                )
                error_count = result_error.scalar() or 0
                
                # 3. Average Latency
                result_latency = await db.execute(
                    select(func.avg(RequestLog.latency_ms)).where(RequestLog.timestamp >= cutoff)
                )
                avg_latency = result_latency.scalar() or 0.0
                
                # 4. Latency P95 (Approximate via SQL if supported, or simpler avg for v1)
                # For strict v1 fast implementation, we stick to Average.
                
                rpm = total_requests / minutes if minutes > 0 else 0
                
                return {
                    "window_minutes": minutes,
                    "total_requests": total_requests,
                    "error_rate_percent": round((error_count / total_requests * 100), 2) if total_requests > 0 else 0,
                    "avg_latency_ms": round(avg_latency, 2),
                    "rpm": round(rpm, 2)
                }
        except Exception as e:
            print(f"Stats Error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

stats_service = StatsService()