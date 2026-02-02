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

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle, CollectionLog


class StatsService:
    """统计服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview_stats(self) -> dict:
        """
        获取总览统计信息

        Returns:
            dict: 包含总数、未读、收藏、已过滤数量
        """
        # 总文章数
        total_result = await self.db.execute(select(func.count(NewsArticle.id)))
        total = total_result.scalar_one()

        # 未读数
        unread_result = await self.db.execute(
            select(func.count(NewsArticle.id)).where(NewsArticle.is_read == False)
        )
        unread = unread_result.scalar_one()

        # 收藏数
        starred_result = await self.db.execute(
            select(func.count(NewsArticle.id)).where(NewsArticle.is_starred == True)
        )
        starred = starred_result.scalar_one()

        # 已过滤数
        filtered_result = await self.db.execute(
            select(func.count(NewsArticle.id)).where(NewsArticle.is_filtered == True)
        )
        filtered = filtered_result.scalar_one()

        return {
            "total_articles": total,
            "unread": unread,
            "starred": starred,
            "filtered": filtered,
        }

    async def get_sources_with_counts(self) -> list[dict]:
        """
        获取所有来源及其文章数量

        Returns:
            list: [{"source": "xxx", "count": 123}, ...]
        """
        result = await self.db.execute(
            select(
                NewsArticle.source,
                func.count(NewsArticle.id).label("count"),
            )
            .where(NewsArticle.is_filtered == False)
            .group_by(NewsArticle.source)
        )
        sources = result.all()

        return [{"source": s.source, "count": s.count} for s in sources]

    async def get_categories_with_counts(self) -> list[dict]:
        """
        获取所有分类及其文章数量

        Returns:
            list: [{"category": "xxx", "count": 123}, ...]
        """
        result = await self.db.execute(
            select(
                NewsArticle.source_category.label("category"),
                func.count(NewsArticle.id).label("count"),
            )
            .where(NewsArticle.is_filtered == False)
            .where(NewsArticle.source_category.isnot(None))
            .group_by(NewsArticle.source_category)
        )
        categories = result.all()

        return [{"category": row.category, "count": row.count} for row in categories]

    async def get_collection_logs(self, limit: int = 20) -> list[CollectionLog]:
        """
        获取最近的采集日志

        Args:
            limit: 返回数量限制

        Returns:
            list: 采集日志列表
        """
        result = await self.db.execute(
            select(CollectionLog).order_by(CollectionLog.started_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
