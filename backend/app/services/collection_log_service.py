from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import CollectionLog


class CollectionLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_last_checkpoint(self, source: str) -> datetime | None:
        result = await self.db.execute(
            select(CollectionLog)
            .where(CollectionLog.source == source)
            .where(CollectionLog.status == "success")
            .order_by(CollectionLog.started_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()
        return log.last_article_time if log else None

    async def save_log(
        self,
        *,
        source: str,
        started_at: datetime,
        finished_at: datetime,
        status: str,
        articles_fetched: int,
        articles_new: int,
        articles_duplicate: int,
        last_article_time: datetime | None = None,
        error_message: str | None = None,
        commit: bool = True,
    ) -> CollectionLog:
        log = CollectionLog(
            source=source,
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            articles_fetched=articles_fetched,
            articles_new=articles_new,
            articles_duplicate=articles_duplicate,
            last_article_time=last_article_time,
            error_message=error_message,
        )
        self.db.add(log)

        if commit:
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()
                raise

        return log

