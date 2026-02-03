from datetime import date, datetime
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle
from app.utils.timezone import local_day_bounds_utc


class NewsRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_paginated_news(
        self,
        *,
        page: int,
        per_page: int,
        source: str | None,
        category: str | None,
        search: str | None,
        published_date: date | None,
        starred_only: bool,
        unread_only: bool,
        tz_name_for_published_date: str,
    ) -> tuple[list[NewsArticle], int]:
        query = select(NewsArticle).where(NewsArticle.is_filtered == False)

        if source:
            query = query.where(NewsArticle.source == source)
        if category:
            query = query.where(NewsArticle.source_category == category)
        if search:
            query = query.where(NewsArticle.title.ilike(f"%{search}%"))
        if published_date:
            start_utc, end_utc = local_day_bounds_utc(published_date, tz_name_for_published_date)
            dt_for_filter = func.coalesce(NewsArticle.published_at, NewsArticle.collected_at)
            query = query.where(dt_for_filter >= start_utc, dt_for_filter < end_utc)
        if starred_only:
            query = query.where(NewsArticle.is_starred == True)
        if unread_only:
            query = query.where(NewsArticle.is_read == False)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self._db.execute(count_query)
        total = int(total_result.scalar_one() or 0)

        page_query = query.order_by(NewsArticle.published_at.desc())
        page_query = page_query.offset((page - 1) * per_page).limit(per_page)
        result = await self._db.execute(page_query)
        items = list(result.scalars().all())

        return items, total

    async def get_article_by_id(self, article_id: UUID) -> NewsArticle | None:
        result = await self._db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
        return result.scalar_one_or_none()

    async def mark_all_as_read(self, *, source: str | None) -> int:
        stmt = update(NewsArticle).where(NewsArticle.is_read == False)
        if source:
            stmt = stmt.where(NewsArticle.source == source)

        result = await self._db.execute(stmt.values(is_read=True))
        await self._db.commit()
        return result.rowcount or 0

    async def purge_before(self, *, cutoff_utc: datetime, keep_starred: bool = True) -> int:
        conditions = [NewsArticle.published_at < cutoff_utc]
        if keep_starred:
            conditions.append(NewsArticle.is_starred == False)

        stmt = delete(NewsArticle).where(*conditions)
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.rowcount or 0
