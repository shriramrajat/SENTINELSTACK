import json
from datetime import datetime
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import asyncio
from sentinelstack.aggregation.models import RequestMetric
from sentinelstack.incidents.models import Incident
from sentinelstack.config import settings

# Threshold Configuration
ERROR_RATE_THRESHOLD = 0.05   # 5%
LATENCY_P95_THRESHOLD = 2000  # 2000ms (used once p95 data is reliable)
MIN_REQUESTS_FOR_ALERT = 50   # Don't alert on 1 error out of 2 requests


class IncidentService:
    async def check_thresholds(self, session: AsyncSession, bucket_time: datetime):
        """
        Run immediately after aggregation to detect anomalies.
        Creates, updates, or resolves incidents based on current error rate.
        """
        # 1. Fetch Aggregated Metrics for this bucket
        stmt = select(RequestMetric).where(RequestMetric.bucket_time == bucket_time)
        result = await session.execute(stmt)
        metrics = result.scalars().all()

        if not metrics:
            return

        # 2. Calculate Global Stats
        total_reqs = sum(m.total_requests for m in metrics)
        total_errors = sum(m.total_errors for m in metrics)

        # Avoid alerting on low-volume noise
        if total_reqs < MIN_REQUESTS_FOR_ALERT:
            return

        error_rate = total_errors / total_reqs
        is_breaching = error_rate > ERROR_RATE_THRESHOLD

        # 3. Check for Active Incident
        active_stmt = select(Incident).where(Incident.status == "active").limit(1)
        active_incident = (await session.execute(active_stmt)).scalar_one_or_none()

        # 4. State Machine Logic
        if is_breaching:
            if not active_incident:
                # NEW INCIDENT — create it and immediately trigger AI analysis
                print(f"WARN:    Creating Incident! Error Rate: {error_rate:.2%}")
                affected = ",".join(
                    {m.path for m in metrics if m.total_errors > 0}
                )
                new_incident = Incident(
                    status="active",
                    severity="critical" if error_rate > 0.2 else "high",
                    description=f"High Error Rate Detected: {error_rate:.1%}",
                    start_time=bucket_time,
                    affected_endpoints=affected,
                )
                session.add(new_incident)
                await session.commit()
                await session.refresh(new_incident)

                # Fire Webhook Alert asynchronously
                if settings.WEBHOOK_URL:
                    asyncio.create_task(self._fire_webhook(new_incident))

                # Trigger AI analysis synchronously and persist the result.
                # In a distributed system this would be a queue message; for v1
                # we run it inline since aggregation already runs in background.
                try:
                    from sentinelstack.ai.service import ai_service

                    formatted_metrics = [
                        {
                            "time": m.bucket_time.isoformat(),
                            "path": m.path,
                            "status": m.status_code,
                            "errors": m.total_errors,
                            "avg_latency_ms": m.avg_latency_ms,
                            "p95_latency_ms": m.p95_latency_ms,
                        }
                        for m in metrics
                        if m.total_errors > 0
                    ]
                    analysis = await ai_service._generate_analysis(
                        new_incident, formatted_metrics  # type: ignore[arg-type]
                    )
                    new_incident.ai_summary = (
                        analysis.get("explanation") or analysis.get("summary", "")
                    )
                    new_incident.ai_action_items = json.dumps(
                        analysis.get("mitigation_steps")
                        or analysis.get("action_items", [])
                    )
                    await session.commit()
                    print(
                        f"INFO:    AI analysis persisted for incident {new_incident.id}"
                    )
                except Exception as ai_err:
                    # AI failure must never crash the incident pipeline
                    print(f"WARN:    AI analysis failed for new incident: {ai_err}")

            else:
                # ONGOING INCIDENT — no action needed; dashboard reflects current state
                pass

        else:
            if active_incident:
                # RESOLVE INCIDENT
                print(f"INFO:    Resolving Incident {active_incident.id}")
                active_incident.status = "resolved"
                active_incident.end_time = datetime.utcnow()
                active_incident.description += (
                    f" [Resolved. Final Error Rate: {error_rate:.1%}]"
                )
                await session.commit()

    async def _fire_webhook(self, incident: Incident):
        """Send an asynchronous HTTP POST to the configured webhook URL."""
        payload = {
            "incident_id": incident.id,
            "status": incident.status,
            "severity": incident.severity,
            "description": incident.description,
            "start_time": incident.start_time.isoformat() if incident.start_time else None,
            "affected_endpoints": incident.affected_endpoints
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.WEBHOOK_URL,
                    json=payload,
                    timeout=5.0
                )
                print(f"INFO:    Webhook fired. Status: {response.status_code}")
        except Exception as e:
            print(f"WARN:    Failed to fire webhook: {e}")


# Global Instance
incident_service = IncidentService()
