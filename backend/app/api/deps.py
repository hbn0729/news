"""
API Dependencies - 依赖注入工厂

职责：
- 提供数据库会话
- 提供服务实例
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_maker
from app.services import (
    NewsService,
    StatsService,
    StreamService,
    CleanupService,
    CollectionService,
)


async def get_news_service(db: AsyncSession = Depends(get_db)) -> NewsService:
    """获取新闻服务实例"""
    return NewsService(db)


async def get_stats_service(db: AsyncSession = Depends(get_db)) -> StatsService:
    """获取统计服务实例"""
    return StatsService(db)


async def get_cleanup_service(db: AsyncSession = Depends(get_db)) -> CleanupService:
    return CleanupService(db)

async def get_collection_service(
    db: AsyncSession = Depends(get_db),
) -> CollectionService:
    return CollectionService(db, log_session_maker=async_session_maker)


def get_stream_service() -> StreamService:
    """获取流服务实例"""
    return StreamService(async_session_maker)
