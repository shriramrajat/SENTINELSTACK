from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sentinelstack.database import get_db
from sentinelstack.aggregation.models import RequestMetric
from sentinelstack.incidents.models import Incident
from sentinelstack.ai.service import ai_service
from sentinelstack.stats.service import stats_service

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/status")
async def get_system_status():
    """
    Returns the high-level health + AI analysis if an incident is active.
    This is the primary feed for the dashboard status indicator.
    """
    return await ai_service.get_system_status()


@router.get("/metrics")
async def get_metrics(minutes: int = 30, db: AsyncSession = Depends(get_db)):
    """
    Returns time-series data for frontend charts.
    Aggregates RequestMetric rows by bucket_time across all paths/methods.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)

    stmt = (
        select(RequestMetric)
        .where(RequestMetric.bucket_time >= cutoff)
        .order_by(RequestMetric.bucket_time)
    )
    result = await db.execute(stmt)
    metrics = result.scalars().all()

    # Aggregate by bucket_time to get global RPS + errors per minute
    aggregated: dict = {}
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


@router.get("/dashboard")
async def get_dashboard_stats(minutes: int = 60):
    """
    Returns high-level summary metrics for the specified time window.
    Includes: total_requests, error_rate_percent, avg_latency_ms, rpm.
    """
    return await stats_service.get_dashboard_metrics(minutes=minutes)


@router.get("/incidents")
async def get_recent_incidents(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """
    Returns the most recent incidents (both active and resolved).
    Enables the dashboard to populate real incident history instead of
    the hardcoded placeholder HTML.
    """
    stmt = (
        select(Incident)
        .order_by(desc(Incident.start_time))
        .limit(limit)
    )
    result = await db.execute(stmt)
    incidents = result.scalars().all()

    return {
        "incidents": [
            {
                "id": inc.id,
                "status": inc.status,
                "severity": inc.severity,
                "description": inc.description,
                "affected_endpoints": inc.affected_endpoints,
                "start_time": inc.start_time.isoformat() if inc.start_time else None,
                "end_time": inc.end_time.isoformat() if inc.end_time else None,
                "ai_summary": inc.ai_summary,
                "ai_action_items": inc.ai_action_items,
            }
            for inc in incidents
        ]
    }