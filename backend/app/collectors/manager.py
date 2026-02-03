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
import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.registry import get_collector, get_collector_names
from app.services.article_persistence import ArticlePersistenceService
from app.services.collection_log_service import CollectionLogService

logger = logging.getLogger(__name__)


class CollectorManager:
    """Manages all news collectors."""

    def __init__(self, db: AsyncSession, *, log_session_maker=None):
        self.db = db
        self._log_session_maker = log_session_maker
        self.persistence = ArticlePersistenceService(db)
        self.logs = CollectionLogService(db)

    async def _rollback_quietly(self) -> None:
        try:
            await self.db.rollback()
        except Exception:
            pass

    async def _save_checkpoint_safely(
        self, source_name: str, *, commit: bool, **kwargs
    ) -> None:
        try:
            await self.logs.save_log(source=source_name, commit=commit, **kwargs)
        except Exception as e:
            logger.error(f"Failed to save collection log for {source_name}: {e}")

    async def _save_failure_log(self, source_name: str, **kwargs) -> None:
        if self._log_session_maker is None:
            await self._save_checkpoint_safely(source_name, commit=True, **kwargs)
            return

        try:
            async with self._log_session_maker() as session:
                logs = CollectionLogService(session)
                await logs.save_log(source=source_name, commit=True, **kwargs)
        except Exception as e:
            logger.error(f"Failed to save failure log for {source_name}: {e}")

    async def collect_from(self, source_name: str) -> list:
        """Collect articles from a specific source."""
        collector_class = get_collector(source_name)
        if collector_class is None:
            logger.error(f"Unknown collector: {source_name}")
            return []

        collector = collector_class()

        started_at = datetime.now(timezone.utc)
        articles_fetched = 0
        articles_new = 0
        articles_duplicate = 0
        last_article_time = None

        try:
            # Fetch raw articles
            raw_articles = await collector.fetch_articles()
            articles_fetched = len(raw_articles)
            checkpoint = await self.logs.get_last_checkpoint(source_name)

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
            articles_new = len(new_articles)
            articles_duplicate = duplicate_count
            last_article_time = max_published_at

            # Save collection log
            await self._save_checkpoint_safely(
                source_name,
                commit=False,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                status="success",
                articles_fetched=articles_fetched,
                articles_new=articles_new,
                articles_duplicate=articles_duplicate,
                last_article_time=last_article_time,
            )

            await self.db.commit()

            if new_articles:
                logger.info(
                    f"Collected from {source_name}: "
                    f"{len(new_articles)} new, {duplicate_count} duplicates"
                )
            return new_articles

        except asyncio.CancelledError:
            await self._rollback_quietly()
            raise
        except Exception as e:
            logger.error(f"Collection failed for {source_name}: {e}")
            await self._rollback_quietly()

            await self._save_failure_log(
                source_name,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                status="failed",
                articles_fetched=articles_fetched,
                articles_new=articles_new,
                articles_duplicate=articles_duplicate,
                last_article_time=last_article_time,
                error_message=str(e),
            )
            return []

    async def collect_all(self) -> dict[str, list]:
        """Collect from all registered sources."""
        results = {}
        for source_name in get_collector_names():
            results[source_name] = await self.collect_from(source_name)
        return results
