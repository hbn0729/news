"""
News Service - 新闻相关业务逻辑

职责：
- 新闻的CRUD操作
- 查询过滤与分页
- 文章状态更新

设计原则：
- 单一职责：只处理新闻相关业务
- 依赖注入：通过构造函数接收数据库会话
- 与路由层解耦：不依赖FastAPI特定类型
"""

from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle
from app.config import settings


class NewsService:
    """新闻业务服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_paginated_news(
        self,
        page: int = 1,
        per_page: int | None = None,
        source: str | None = None,
        category: str | None = None,
        search: str | None = None,
        starred_only: bool = False,
        unread_only: bool = False,
    ) -> tuple[list[NewsArticle], int]:
        """
        获取分页新闻列表

        Returns:
            tuple: (articles, total_count)
        """
        if per_page is None:
            per_page = settings.DEFAULT_PAGE_SIZE

        # 基础查询 - 排除被过滤的文章
        query = select(NewsArticle).where(NewsArticle.is_filtered == False)

        # 应用筛选条件
        if source:
            query = query.where(NewsArticle.source == source)
        if category:
            query = query.where(NewsArticle.source_category == category)
        if search:
            query = query.where(NewsArticle.title.ilike(f"%{search}%"))
        if starred_only:
            query = query.where(NewsArticle.is_starred == True)
        if unread_only:
            query = query.where(NewsArticle.is_read == False)

        # 计算总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询
        query = query.order_by(NewsArticle.published_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)

        result = await self.db.execute(query)
        articles = list(result.scalars().all())

        return articles, total

    async def get_article_by_id(self, article_id: UUID) -> NewsArticle | None:
        """根据ID获取单篇文章"""
        result = await self.db.execute(
            select(NewsArticle).where(NewsArticle.id == article_id)
        )
        return result.scalar_one_or_none()

    async def update_article_status(
        self,
        article_id: UUID,
        is_read: bool | None = None,
        is_starred: bool | None = None,
    ) -> NewsArticle | None:
        """
        更新文章状态（已读/收藏）

        Returns:
            更新后的文章，如果不存在返回None
        """
        article = await self.get_article_by_id(article_id)
        if not article:
            return None

        if is_read is not None:
            article.is_read = is_read
        if is_starred is not None:
            article.is_starred = is_starred

        await self.db.commit()
        await self.db.refresh(article)
        return article

    async def mark_all_as_read(self, source: str | None = None) -> int:
        """
        批量标记为已读

        Args:
            source: 可选，只标记特定来源

        Returns:
            受影响的文章数量
        """
        stmt = update(NewsArticle).where(NewsArticle.is_read == False)

        if source:
            stmt = stmt.where(NewsArticle.source == source)

        stmt = stmt.values(is_read=True)
        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount
