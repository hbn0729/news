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

from datetime import date, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle
from app.config import settings
from app.repositories.news_repository import NewsRepository


class NewsService:
    """新闻业务服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._repo = NewsRepository(db)

    async def get_paginated_news(
        self,
        page: int = 1,
        per_page: int | None = None,
        source: str | None = None,
        category: str | None = None,
        search: str | None = None,
        published_date: date | None = None,
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
        return await self._repo.get_paginated_news(
            page=page,
            per_page=per_page,
            source=source,
            category=category,
            search=search,
            published_date=published_date,
            starred_only=starred_only,
            unread_only=unread_only,
            tz_name_for_published_date="Asia/Shanghai",
        )

    async def get_article_by_id(self, article_id: UUID) -> NewsArticle | None:
        """根据ID获取单篇文章"""
        return await self._repo.get_article_by_id(article_id)

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
        return await self._repo.mark_all_as_read(source=source)

    async def purge_old_news(self, cutoff_utc: datetime) -> int:
        return await self._repo.purge_before(cutoff_utc=cutoff_utc, keep_starred=True)
