import datetime
import json
from sqlalchemy import select, desc
from sentinelstack.database import AsyncSessionLocal
from sentinelstack.ai.llm import get_llm_provider, LLMProvider
from sentinelstack.config import settings
from sentinelstack.cache import redis_client
from sentinelstack.incidents.models import Incident
from sentinelstack.aggregation.models import RequestMetric


class AIService:
    def __init__(self):
        # Initialize LLM backend based on environment
        api_key = getattr(settings, "OPENAI_API_KEY", "") or ""
        self.llm: LLMProvider = get_llm_provider(
            env=settings.ENV,
            api_key=api_key,
        )

    # ------------------------------------------------------------------
    # PUBLIC: System Status (used by /stats/status and the dashboard)
    # ------------------------------------------------------------------

    async def get_system_status(self) -> dict:
        """
        Single source-of-truth health check.
        1. Checks the Incident table for an active incident.
        2. If active → generates/fetches AI analysis and persists it to the DB.
        3. If healthy → returns summary.
        """
        async with AsyncSessionLocal() as db:
            # 1. Check for Active Incident
            stmt = (
                select(Incident)
                .where(Incident.status == "active")
                .order_by(desc(Incident.start_time))
                .limit(1)
            )
            incident = (await db.execute(stmt)).scalar_one_or_none()

            if not incident:
                return {
                    "health": "operational",
                    "summary": "All systems healthy. No active incidents.",
                    "details": None,
                }

            # 2. Incident found — fetch context metrics
            metrics_stmt = (
                select(RequestMetric)
                .where(RequestMetric.bucket_time >= incident.start_time)
                .order_by(desc(RequestMetric.bucket_time))
                .limit(10)  # Last 10 minutes of data
            )
            metrics = (await db.execute(metrics_stmt)).scalars().all()

            # 3. Check Redis cache first (TTL 5 min)
            cache_key = f"incident_analysis:{incident.id}"
            cached = await redis_client.get(cache_key)
            if cached:
                analysis = json.loads(cached)
            else:
                # 4. Generate fresh analysis (expensive — LLM call)
                analysis = await self._generate_analysis(incident, metrics)
                await redis_client.setex(cache_key, 300, json.dumps(analysis))

                # 5. Persist AI analysis back to the incident record
                #    so historical incidents retain their AI output permanently.
                if not incident.ai_summary:
                    incident.ai_summary = (
                        analysis.get("explanation")
                        or analysis.get("summary", "")
                    )
                    incident.ai_action_items = json.dumps(
                        analysis.get("mitigation_steps")
                        or analysis.get("action_items", [])
                    )
                    await db.commit()

            return {
                "health": "critical" if incident.severity == "critical" else "degraded",
                "summary": incident.description,
                "incident_id": incident.id,
                "analysis": analysis,
            }

    # ------------------------------------------------------------------
    # PUBLIC: Recent Traffic Analysis (used by GET /ai/insight)
    # ------------------------------------------------------------------

    async def analyze_recent_traffic(self, minutes: int = 15) -> dict:
        """
        Analyzes traffic patterns over the last N minutes regardless of
        whether an incident is active. Returns LLM-generated insights.
        Results are cached for 60 seconds to avoid redundant LLM calls.
        """
        cache_key = f"traffic_analysis:{minutes}m"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        async with AsyncSessionLocal() as db:
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
            stmt = (
                select(RequestMetric)
                .where(RequestMetric.bucket_time >= cutoff)
                .order_by(desc(RequestMetric.bucket_time))
            )
            metrics = (await db.execute(stmt)).scalars().all()

        if not metrics:
            return {
                "health": "operational",
                "summary": f"No traffic data in the last {minutes} minutes.",
                "details": None,
            }

        # Compute aggregate stats across all buckets
        total_reqs = sum(m.total_requests for m in metrics)
        total_errors = sum(m.total_errors for m in metrics)
        error_rate = (total_errors / total_reqs) if total_reqs > 0 else 0.0
        avg_latency = (
            sum(m.avg_latency_ms * m.total_requests for m in metrics) / total_reqs
            if total_reqs > 0
            else 0.0
        )

        context = {
            "window_minutes": minutes,
            "total_requests": total_reqs,
            "error_rate_percent": round(error_rate * 100, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "errors": [
                {
                    "path": m.path,
                    "count": m.total_errors,
                    "status": m.status_code,
                    "p95_latency_ms": m.p95_latency_ms,
                }
                for m in metrics
                if m.total_errors > 0
            ],
        }

        system_prompt = (
            "You are SentinelAI, an SRE assistant analyzing API traffic patterns. "
            "Summarize the traffic health, flag any concerns, and suggest proactive actions. "
            "Output JSON with keys: 'summary', 'analysis', 'action_items', 'severity'."
        )

        analysis = await self.llm.generate_insight(system_prompt, context)

        # Cache for 60s — short TTL since traffic conditions change quickly
        await redis_client.setex(cache_key, 60, json.dumps(analysis))

        return {
            "health": "degraded" if error_rate > 0.05 else "operational",
            "window_minutes": minutes,
            "stats": context,
            "analysis": analysis,
        }

    # ------------------------------------------------------------------
    # PRIVATE: LLM wrapper for incident-specific analysis
    # ------------------------------------------------------------------

    async def _generate_analysis(
        self, incident: Incident, metrics: list
    ) -> dict:
        """Asks the LLM to explain an incident using aggregated metrics."""
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
        ]

        system_prompt = (
            "You are SentinelAI, an automated SRE responder. "
            "An incident has been detected based on hard threshold rules. "
            "Explain the root cause based on the metrics provided.\n"
            "Output JSON with keys: 'explanation', 'affected_components', "
            "'likely_root_cause', 'mitigation_steps'."
        )

        context = {
            "incident_desc": incident.description,
            "start_time": incident.start_time.isoformat(),
            "recent_metrics": formatted_metrics,
        }

        try:
            return await self.llm.generate_insight(system_prompt, context)
        except Exception as e:
            return {
                "explanation": "AI Analysis Failed",
                "reason": str(e),
            }


# Global Instance
ai_service = AIService()