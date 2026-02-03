"""
Stats Service - 统计与元数据服务

职责：
- 新闻统计信息
- 来源列表查询
- 分类列表查询

设计原则：
- 单一职责：只处理统计和聚合查询
- 高内聚：所有统计相关逻辑集中在此
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import CollectionLog
from app.repositories.stats_repository import StatsRepository


class StatsService:
    """统计服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._repo = StatsRepository(db)

    async def get_overview_stats(self) -> dict:
        """
        获取总览统计信息

        Returns:
            dict: 包含总数、未读、收藏、已过滤数量
        """
        return await self._repo.overview()

    async def get_sources_with_counts(self) -> list[dict]:
        """
        获取所有来源及其文章数量

        Returns:
            list: [{"source": "xxx", "count": 123}, ...]
        """
        return await self._repo.sources_with_counts()

    async def get_categories_with_counts(self) -> list[dict]:
        """
        获取所有分类及其文章数量

        Returns:
            list: [{"category": "xxx", "count": 123}, ...]
        """
        return await self._repo.categories_with_counts()

    async def get_collection_logs(self, limit: int = 20) -> list[CollectionLog]:
        """
        获取最近的采集日志

        Args:
            limit: 返回数量限制

        Returns:
            list: 采集日志列表
        """
        return await self._repo.collection_logs(limit=limit)
