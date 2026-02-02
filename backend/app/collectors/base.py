from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import CollectionLog


@dataclass
class RawArticle:
    """Raw article data from collectors."""
    title: str
    url: str
    content: str | None = None
    summary: str | None = None
    published_at: datetime | None = None
    source_category: str | None = None
    extra: dict[str, Any] | None = None


class BaseCollector(ABC):
    """Abstract base class for news collectors."""

    source_name: str = "unknown"

    def __init__(self, db: AsyncSession):
        self.db = db

    @abstractmethod
    async def fetch_articles(self) -> list[RawArticle]:
        """Fetch articles from the source."""
        pass

    async def get_last_checkpoint(self) -> datetime | None:
        """Get the last collection checkpoint for incremental fetching."""
        result = await self.db.execute(
            select(CollectionLog)
            .where(CollectionLog.source == self.source_name)
            .where(CollectionLog.status == "success")
            .order_by(CollectionLog.started_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()
        return log.last_article_time if log else None

    async def save_checkpoint(
        self,
        started_at: datetime,
        finished_at: datetime,
        status: str,
        articles_fetched: int,
        articles_new: int,
        articles_duplicate: int,
        last_article_time: datetime | None = None,
        error_message: str | None = None,
    ) -> CollectionLog:
        """Save collection log for tracking."""
        log = CollectionLog(
            source=self.source_name,
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
        await self.db.commit()
        return log
