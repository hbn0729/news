"""
Collection Routes - 采集相关API路由

职责：
- 手动触发采集
- 采集状态查询
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.collectors.manager import CollectorManager

router = APIRouter(tags=["collection"])


@router.post("/collect")
async def trigger_collection(
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger news collection."""
    manager = CollectorManager(db)

    if source:
        articles = await manager.collect_from(source)
        return {
            "source": source,
            "new_articles": len(articles),
        }
    else:
        results = await manager.collect_all()
        return {source_name: len(articles) for source_name, articles in results.items()}
