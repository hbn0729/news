"""
Article Persistence Service - 文章持久化服务

职责：
- 文章去重检查
- 文章保存到数据库

设计原则：
- 单一职责：只处理持久化
- 与采集逻辑解耦
"""

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import RawArticle
from app.models.news import NewsArticle
from app.services.dedup import DeduplicationService


class ArticlePersistenceService:
    """文章持久化服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dedup = DeduplicationService(db)

    async def persist_articles(
        self,
        raw_articles: list[RawArticle],
        source_name: str,
        checkpoint: datetime | None = None,
    ) -> tuple[list[NewsArticle], int, datetime | None]:
        """
        持久化文章列表

        Args:
            raw_articles: 原始文章列表
            source_name: 来源名称
            checkpoint: 上次采集时间点

        Returns:
            tuple: (new_articles, duplicate_count, max_published_at)
        """
        collected_fallback_at = datetime.now(timezone.utc)
        new_articles = []
        duplicate_count = 0
        max_published_at = None

        for raw in raw_articles:
            published_at = raw.published_at or collected_fallback_at

            # Track max time from all fetched articles
            if max_published_at is None or published_at > max_published_at:
                max_published_at = published_at

            # Skip old articles if we have a checkpoint
            if checkpoint and published_at <= checkpoint:
                continue

            # Skip empty titles
            if not raw.title or not raw.title.strip():
                continue

            # Check for duplicates
            is_dup, content_hash = await self.dedup.is_duplicate(
                raw.url, raw.title, source_name, content=raw.content or "", summary=raw.summary or ""
            )

            if is_dup:
                duplicate_count += 1
                continue

            # Create article
            article = NewsArticle(
                title=raw.title.strip(),
                url=raw.url,
                content=raw.content,
                summary=raw.summary,
                source=source_name,
                source_category=raw.source_category,
                published_at=published_at,
                content_hash=content_hash,
            )

            self.db.add(article)
            new_articles.append(article)

        return new_articles, duplicate_count, max_published_at
