import datetime
from sqlalchemy import select, func, desc
from sentinelstack.database import AsyncSessionLocal
from sentinelstack.logging.models import RequestLog

class AIService:
    async def analyze_recent_traffic(self, minutes: int = 15) -> dict:
        """
        Analyzes traffic from the last N minutes and returns a summary insight.
        """
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes)
        insight = "System is operating normally."
        severity = "info"
        
        async with AsyncSessionLocal() as db:
            # 1. Fetch error counts grouped by status code and path
            # SELECT status_code, path, COUNT(*) FROM logs WHERE error=true GROUP BY status_code, path
            result = await db.execute(
                select(RequestLog.status_code, RequestLog.path, func.count(RequestLog.id))
                .where(RequestLog.timestamp >= cutoff)
                .where(RequestLog.error_flag == True)
                .group_by(RequestLog.status_code, RequestLog.path)
                .order_by(desc(func.count(RequestLog.id)))
                .limit(3)
            )
            
            top_errors = result.all() # List of (status, path, count)
            
            if not top_errors:
                return {"insight": "No recent errors detected. Systems Nominal.", "severity": "success"}

            # Heuristic Analysis (The "AI" part)
            primary_error = top_errors[0]
            code, path, count = primary_error
            
            if code == 429:
                insight = f"⚠️ High Traffic Alert: {count} requests rate-limited on {path}. Possible DDoS or aggressive scraping detected."
                severity = "warning"
            elif code == 500:
                insight = f"🚨 Critical Failure: {count} Internal Server Errors on {path}. Check application logs or database connectivity immediately."
                severity = "critical"
            elif code == 401 or code == 403:
                insight = f"🔒 Security Alert: {count} failed authentication attempts on {path}. Potential brute-force or credential stuffing."
                severity = "warning"
            elif code == 404:
                insight = f"🔍 Configuration Issue: {count} Not Found errors on {path}. Client might be accessing a deprecated endpoint."
                severity = "info"
            else:
                insight = f"Anomaly Detected: {count} errors ({code}) on {path}."
                severity = "warning"

            return {
                "insight": insight,
                "severity": severity,
                "details": [f"{r[2]}x {r[0]} on {r[1]}" for r in top_errors]
            }

ai_service = AIService()
