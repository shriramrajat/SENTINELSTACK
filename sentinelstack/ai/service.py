import datetime
import json
from sqlalchemy import select, func, desc
from sentinelstack.database import AsyncSessionLocal
from sentinelstack.logging.models import RequestLog
from sentinelstack.ai.llm import get_llm_provider, LLMProvider
from sentinelstack.config import settings
from sentinelstack.cache import redis_client

class AIService:
    def __init__(self):
        # Initialize LLM based on environment
        # We use a factory pattern to switch between Mock and Real LLM
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        self.llm: LLMProvider = get_llm_provider(
            env=settings.ENV,
            api_key=api_key
        )

    async def get_raw_stats(self, minutes: int = 15) -> dict:
        """
        Database Layer: Aggregates raw SQL metrics.
        Returns pure data (Dict). No business logic.
        """
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
        
        async with AsyncSessionLocal() as db:
            # 1. Error Counts (Top 5)
            # Query: SELECT status, path, COUNT(*) FROM logs WHERE error=true ...
            errors_result = await db.execute(
                select(RequestLog.status_code, RequestLog.path, func.count(RequestLog.id))
                .where(RequestLog.timestamp >= cutoff)
                .where(RequestLog.error_flag == True)
                .group_by(RequestLog.status_code, RequestLog.path)
                .order_by(desc(func.count(RequestLog.id)))
                .limit(5)
            )
            
            # Format Errors First
            formatted_errors = [
                {"code": r[0], "path": r[1], "count": r[2]} 
                for r in errors_result.all()
            ]

            # 2. Total Request Volume (for context)
            total_result = await db.execute(
                select(func.count(RequestLog.id))
                .where(RequestLog.timestamp >= cutoff)
            )
            total = total_result.scalar() or 0

            # 3. Average Latency (approx)
            latency_result = await db.execute(
                select(func.avg(RequestLog.process_time))
                .where(RequestLog.timestamp >= cutoff)
            )
            val = latency_result.scalar()
            latency = float(val) if val else 0.0

            return {
                "period_minutes": minutes,
                "total_requests": total,
                "avg_latency_ms": round(latency * 1000, 2),
                "top_errors": formatted_errors
            }

    async def analyze_recent_traffic(self, minutes: int = 15) -> dict:
        """
        Core Logic:
        1. Check Cache (Don't query DB/LLM too often)
        2. Get Raw Stats from DB
        3. Send to LLM/Mock for Insight Generation
        """
        
        # 1. Cache Check
        # 5 min TTL to prevent spamming the expensive 'LLM'
        cache_key = f"ai_insight:{minutes}"
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            # Redis failure should not break the app
            pass

        # 2. Get Data form DB
        stats = await self.get_raw_stats(minutes)

        # 3. Construct Context for AI
        system_prompt = (
            "You are SentinelAI, an expert Site Reliability Engineer (SRE). "
            "Analyze the provided JSON metrics from an API Gateway.\n\n"
            "Your output MUST be a JSON object with these keys:\n"
            "- summary: A short 1-sentence headline.\n"
            "- analysis: A detailed paragraph explaining likely root causes.\n"
            "- action_items: A list of 3 specific technical recommendations.\n"
            "- severity: One of [critical, high, medium, low, info, healthy].\n"
        )
        
        context = {
            "metrics": stats,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        # 4. Generate Insight
        try:
            insight = await self.llm.generate_insight(system_prompt, context)
            
            # Merge raw stats with insight for the frontend
            final_result = {
                "ai_analysis": insight,
                "raw_metrics": stats
            }
            
            # Cache Result
            try:
                await redis_client.setex(cache_key, 300, json.dumps(final_result))
            except Exception:
                pass 
                
            return final_result
            
        except Exception as e:
            print(f"AI Service Error: {e}")
            # Fallback (don't cache failures)
            return {
                "ai_analysis": {
                    "summary": "AI Analysis Failed", 
                    "severity": "unknown",
                    "action_items": [],
                    "analysis": str(e)
                },
                "raw_metrics": stats
            }

# Global Instance
ai_service = AIService()
