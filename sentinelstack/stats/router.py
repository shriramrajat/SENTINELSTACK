from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sentinelstack.database import get_db
from sentinelstack.aggregation.models import RequestMetric
from sentinelstack.incidents.models import Incident
from sentinelstack.ai.service import ai_service

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("/status")
async def get_system_status():
    """
    Returns the high-level health + AI analysis if incident active.
    """
    return await ai_service.get_system_status()

@router.get("/metrics")
async def get_metrics(minutes: int = 30, db: AsyncSession = Depends(get_db)):
    """
    Returns time-series data for frontend charts.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    
    stmt = (
        select(RequestMetric)
        .where(RequestMetric.bucket_time >= cutoff)
        .order_by(RequestMetric.bucket_time)
    )
    result = await db.execute(stmt)
    metrics = result.scalars().all()
    
    # Transform for Chart.js
    # We need to aggregate by bucket_time across all paths/methods to get global RPS
    aggregated = {}
    
    for m in metrics:
        ts = m.bucket_time.isoformat()
        if ts not in aggregated:
            aggregated[ts] = {"total": 0, "errors": 0}
        aggregated[ts]["total"] += m.total_requests
        aggregated[ts]["errors"] += m.total_errors

    return {
        "timeseries": [
            {"time": k, "requests": v["total"], "errors": v["errors"]}
            for k, v in aggregated.items()
        ]
    }