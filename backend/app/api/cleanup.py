from fastapi import APIRouter, Depends, Query

from app.api.deps import get_cleanup_service
from app.schemas.cleanup import CleanupLogResponse, CleanupStatsResponse
from app.services import CleanupService

router = APIRouter(tags=["cleanup"])


@router.get("/cleanup-logs", response_model=list[CleanupLogResponse])
async def get_cleanup_logs(
    limit: int = Query(20, ge=1, le=100),
    service: CleanupService = Depends(get_cleanup_service),
):
    logs = await service.get_cleanup_logs(limit)
    return [CleanupLogResponse.model_validate(log) for log in logs]


@router.get("/cleanup-stats", response_model=CleanupStatsResponse)
async def get_cleanup_stats(
    service: CleanupService = Depends(get_cleanup_service),
):
    summary = await service.get_cleanup_summary()
    latest = summary["latest"]

    return CleanupStatsResponse(
        last_started_at=getattr(latest, "started_at", None),
        last_finished_at=getattr(latest, "finished_at", None),
        last_status=getattr(latest, "status", None),
        last_deleted_count=int(getattr(latest, "deleted_count", 0) or 0),
        last_duration_ms=summary["last_duration_ms"],
        last_cutoff_utc=getattr(latest, "cutoff_utc", None),
        last_retention_days=getattr(latest, "retention_days", None),
        last_error_message=getattr(latest, "error_message", None),
        total_runs=summary["total_runs"],
        total_deleted=summary["total_deleted"],
    )
