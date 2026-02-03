from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


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

    @abstractmethod
    async def fetch_articles(self) -> list[RawArticle]:
        """Fetch articles from the source."""
        pass
