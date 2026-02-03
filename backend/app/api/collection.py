"""
Collection Routes - 采集相关API路由

职责：
- 手动触发采集
- 采集状态查询
"""

from fastapi import APIRouter, Depends
from app.api.deps import get_collection_service
from app.services.collection_service import CollectionService

router = APIRouter(tags=["collection"])


@router.post("/collect")
async def trigger_collection(
    source: str | None = None,
    service: CollectionService = Depends(get_collection_service),
):
    """Manually trigger news collection."""
    return await service.trigger(source=source)
