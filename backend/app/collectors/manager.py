"""
Collector Manager - 采集器管理

职责：
- 管理采集器注册表
- 协调采集流程
- 不直接处理数据持久化

设计原则：
- 单一职责：只管理采集，不处理持久化
- 开闭原则：新增采集器无需修改此文件
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import BaseCollector, RawArticle
from app.collectors.registry import COLLECTORS
from app.services.article_persistence import ArticlePersistenceService

logger = logging.getLogger(__name__)


class CollectorManager:
    """Manages all news collectors."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.persistence = ArticlePersistenceService(db)

    async def collect_from(self, source_name: str) -> list:
        """Collect articles from a specific source."""
        if source_name not in COLLECTORS:
            logger.error(f"Unknown collector: {source_name}")
            return []

        collector_class = COLLECTORS[source_name]
        collector = collector_class(self.db)

        started_at = datetime.now(timezone.utc)

        try:
            # Fetch raw articles
            raw_articles = await collector.fetch_articles()
            checkpoint = await collector.get_last_checkpoint()

            # Persist articles
            (
                new_articles,
                duplicate_count,
                max_published_at,
            ) = await self.persistence.persist_articles(
                raw_articles=raw_articles,
                source_name=collector.source_name,
                checkpoint=checkpoint,
            )

            # Save collection log
            await collector.save_checkpoint(
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                status="success",
                articles_fetched=len(raw_articles),
                articles_new=len(new_articles),
                articles_duplicate=duplicate_count,
                last_article_time=max_published_at,
            )

            if new_articles:
                logger.info(
                    f"Collected from {source_name}: "
                    f"{len(new_articles)} new, {duplicate_count} duplicates"
                )
            return new_articles

        except Exception as e:
            logger.error(f"Collection failed for {source_name}: {e}")
            await collector.save_checkpoint(
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                status="failed",
                articles_fetched=0,
                articles_new=0,
                articles_duplicate=0,
                error_message=str(e),
            )
            return []

    async def collect_all(self) -> dict[str, list]:
        """Collect from all registered sources."""
        results = {}
        for source_name in COLLECTORS:
            results[source_name] = await self.collect_from(source_name)
        return results
