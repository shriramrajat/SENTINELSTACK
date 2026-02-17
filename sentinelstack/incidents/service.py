from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sentinelstack.aggregation.models import RequestMetric
from sentinelstack.incidents.models import Incident
from sentinelstack.ai.service import ai_service # Circular import risk handled later

# Threshold Configuration
ERROR_RATE_THRESHOLD = 0.05  # 5%
LATENCY_P95_THRESHOLD = 2000 # 2s (If we had p95 data, using avg for now > 500ms)
MIN_REQUESTS_FOR_ALERT = 50  # Don't alert on 1 error out of 2 requests

class IncidentService:
    async def check_thresholds(self, session: AsyncSession, bucket_time: datetime):
        """
        Run immediately after aggregation to detect anomalies.
        """
        # 1. Fetch Aggregated Metrics for this bucket
        stmt = select(RequestMetric).where(RequestMetric.bucket_time == bucket_time)
        result = await session.execute(stmt)
        metrics = result.scalars().all()
        
        if not metrics:
            return

        # 2. Calculate Gloabl Stats
        total_reqs = sum(m.total_requests for m in metrics)
        total_errors = sum(m.total_errors for m in metrics)
        
        # Avoid division by zero
        if total_reqs < MIN_REQUESTS_FOR_ALERT:
            # If volume is low, auto-resolve any active incidents? 
            # For v1, we just ignore checks.
            return

        error_rate = total_errors / total_reqs
        is_breaching = error_rate > ERROR_RATE_THRESHOLD
        
        # 3. Check for Active Incidents
        active_stmt = select(Incident).where(Incident.status == "active").limit(1)
        active_incident = (await session.execute(active_stmt)).scalar_one_or_none()

        # 4. State Machine Logic
        if is_breaching:
            if not active_incident:
                # NEW INCIDENT
                print(f"WARN:    Creating Incident! Error Rate: {error_rate:.2%}")
                new_incident = Incident(
                    status="active",
                    severity="critical" if error_rate > 0.2 else "high",
                    description=f"High Error Rate Detected: {error_rate:.1%}",
                    start_time=bucket_time,
                    affected_endpoints=",".join(set([m.path for m in metrics if m.total_errors > 0]))
                )
                session.add(new_incident)
                await session.commit()
                
                # Trigger AI Analysis (Async)
                # In production, this would be a separate queue message.
                # Here, we just let the background worker pick it up or fire & forget
                # For v1 simple, we do nothing. The Dashboard will see it.
                
            else:
                # ONGOING INCIDENT (Update stats if needed)
                pass
                
        else:
            if active_incident:
                # RESOLVE INCIDENT
                print(f"INFO:    Resolving Incident {active_incident.id}")
                active_incident.status = "resolved"
                active_incident.end_time = datetime.utcnow()
                active_incident.description += f" [Resolved. Final Error Rate: {error_rate:.1%}]"
                await session.commit()

# Global Instance
incident_service = IncidentService()
