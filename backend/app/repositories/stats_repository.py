from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle, CollectionLog


class StatsRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def overview(self) -> dict:
        total_result = await self._db.execute(select(func.count(NewsArticle.id)))
        total = int(total_result.scalar_one() or 0)

        unread_result = await self._db.execute(
            select(func.count(NewsArticle.id)).where(NewsArticle.is_read == False)
        )
        unread = int(unread_result.scalar_one() or 0)

        starred_result = await self._db.execute(
            select(func.count(NewsArticle.id)).where(NewsArticle.is_starred == True)
        )
        starred = int(starred_result.scalar_one() or 0)

        filtered_result = await self._db.execute(
            select(func.count(NewsArticle.id)).where(NewsArticle.is_filtered == True)
        )
        filtered = int(filtered_result.scalar_one() or 0)

        return {
            "total_articles": total,
            "unread": unread,
            "starred": starred,
            "filtered": filtered,
        }

    async def sources_with_counts(self) -> list[dict]:
        result = await self._db.execute(
            select(
                NewsArticle.source,
                func.count(NewsArticle.id).label("count"),
            )
            .where(NewsArticle.is_filtered == False)
            .group_by(NewsArticle.source)
        )
        sources = result.all()
        return [{"source": s.source, "count": int(s.count)} for s in sources]

    async def categories_with_counts(self) -> list[dict]:
        result = await self._db.execute(
            select(
                NewsArticle.source_category.label("category"),
                func.count(NewsArticle.id).label("count"),
            )
            .where(NewsArticle.is_filtered == False)
            .where(NewsArticle.source_category.isnot(None))
            .group_by(NewsArticle.source_category)
        )
        categories = result.all()
        return [{"category": row.category, "count": int(row.count)} for row in categories]

    async def collection_logs(self, *, limit: int) -> list[CollectionLog]:
        result = await self._db.execute(
            select(CollectionLog).order_by(CollectionLog.started_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
