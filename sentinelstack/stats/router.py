from fastapi import APIRouter
from sentinelstack.stats.service import stats_service

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/dashboard")
async def get_dashboard(minutes: int = 60):
    return await stats_service.get_dashboard_metrics(minutes)