from fastapi import APIRouter
from sentinelstack.ai.service import ai_service

router = APIRouter(prefix="/ai", tags=["AI Insights"])

@router.get("/insight")
async def get_insight(minutes: int = 15):
    return await ai_service.analyze_recent_traffic(minutes)
