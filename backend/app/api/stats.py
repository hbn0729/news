"""
Stats Routes - 统计相关API路由

职责：
- 统计信息
- 来源列表
- 分类列表
- 采集日志
"""

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_stats_service
from app.schemas.news import CollectionLogResponse
from app.services import StatsService

router = APIRouter(tags=["stats"])


@router.get("/sources")
async def get_sources(
    service: StatsService = Depends(get_stats_service),
):
    """Get list of available news sources with counts."""
    return await service.get_sources_with_counts()


@router.get("/categories")
async def get_categories(
    service: StatsService = Depends(get_stats_service),
):
    """Get list of categories with counts."""
    return await service.get_categories_with_counts()


@router.get("/stats")
async def get_stats(
    service: StatsService = Depends(get_stats_service),
):
    """Get overall statistics."""
    return await service.get_overview_stats()


@router.get("/collection-logs", response_model=list[CollectionLogResponse])
async def get_collection_logs(
    limit: int = Query(20, ge=1, le=100),
    service: StatsService = Depends(get_stats_service),
):
    """Get recent collection logs."""
    logs = await service.get_collection_logs(limit)
    return [CollectionLogResponse.model_validate(log) for log in logs]
