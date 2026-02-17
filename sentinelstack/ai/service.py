import datetime
import json
from sqlalchemy import select, func, desc
from sentinelstack.database import AsyncSessionLocal
from sentinelstack.ai.llm import get_llm_provider, LLMProvider
from sentinelstack.config import settings
from sentinelstack.cache import redis_client
from sentinelstack.incidents.models import Incident
from sentinelstack.aggregation.models import RequestMetric

class AIService:
    def __init__(self):
        # Initialize LLM based on environment
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        self.llm: LLMProvider = get_llm_provider(
            env=settings.ENV,
            api_key=api_key
        )

    async def get_system_status(self) -> dict:
        """
        Single Source of Truth Check.
        1. Check specific Incident Table.
        2. If Incident -> Generate/Fetch Analysis.
        3. If Healthy -> Return Summary Stats.
        """
        async with AsyncSessionLocal() as db:
            # 1. Check for Active Incident
            stmt = select(Incident).where(Incident.status == "active").order_by(desc(Incident.start_time)).limit(1)
            incident = (await db.execute(stmt)).scalar_one_or_none()

            if not incident:
                return {
                    "health": "operational",
                    "summary": "All systems healthy. No active incidents.",
                    "details": None
                }

            # 2. Incident Found - Contextualize
            # Get metrics from the start of the incident
            metrics_stmt = (
                select(RequestMetric)
                .where(RequestMetric.bucket_time >= incident.start_time)
                .order_by(desc(RequestMetric.bucket_time))
                .limit(10) # Last 10 minutes of data
            )
            metrics = (await db.execute(metrics_stmt)).scalars().all()
            
            # 3. Check if Analysis Exists/Fresh
            # In a real system, we'd store the analysis in the DB to avoid re-generating.
            # Here we cache it effectively.
            cache_key = f"incident_analysis:{incident.id}"
            cached = await redis_client.get(cache_key)
            if cached:
                analysis = json.loads(cached)
            else:
                # 4. Generate Fresh Analysis (Expensive)
                analysis = await self._generate_analysis(incident, metrics)
                await redis_client.setex(cache_key, 300, json.dumps(analysis))

            return {
                "health": "critical" if incident.severity == "critical" else "degraded",
                "summary": incident.description,
                "incident_id": incident.id,
                "analysis": analysis
            }

    async def _generate_analysis(self, incident: Incident, metrics: list[RequestMetric]) -> dict:
        """
        Private: Asks LLM to explain the incident using aggregated metrics.
        """
        # Format Context
        formatted_metrics = []
        for m in metrics:
            formatted_metrics.append({
                "time": m.bucket_time.isoformat(),
                "path": m.path,
                "status": m.status_code,
                "errors": m.total_errors,
                "latency": m.avg_latency_ms
            })

        system_prompt = (
            "You are SentinelAI, an automated SRE responder. "
            "An incident has been detected based on hard rules. "
            "Explain the root cause based on the metrics provided.\n"
            "Output JSON with keys: 'explanation', 'affected_components', 'likely_root_cause', 'mitigation_steps'."
        )
        
        context = {
            "incident_desc": incident.description,
            "start_time": incident.start_time.isoformat(),
            "recent_metrics": formatted_metrics
        }

        try:
            return await self.llm.generate_insight(system_prompt, context)
        except Exception as e:
             return {
                "explanation": "AI Analysis Failed",
                "reason": str(e)
            }

# Global Instance
ai_service = AIService()