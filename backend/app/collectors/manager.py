import logging
from datetime import datetime, timezone
from typing import Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.base import BaseCollector
from app.collectors.akshare_collector import (
    AkShareEastmoneyCollector,
    AkShareCLSCollector,
    ITJuziCollector,
)
from app.collectors.realtime_collector import (
    Jin10Collector,
    WallstreetCollector,
)
from app.collectors.rss_collector import (
    Kr36Collector,
    WSJBusinessCollector,
    WSJMarketsCollector,
    MarketWatchCollector,
    ZeroHedgeCollector,
    ETFTrendsCollector,
    WSJSocialEconomyCollector,
    BBCBusinessCollector,
)
from app.models.news import NewsArticle
from app.services.dedup import DeduplicationService

logger = logging.getLogger(__name__)

# Registry of available collectors - 扩展数据源
COLLECTORS: dict[str, Type[BaseCollector]] = {
    # AkShare 数据源
    "eastmoney": AkShareEastmoneyCollector,  # 东方财富
    "cls": AkShareCLSCollector,  # 财联社
    # 创投数据源
    "itjuzi": ITJuziCollector,  # IT桔子
    # 实时快讯数据源
    "jin10": Jin10Collector,  # 金十数据
    "wallstreet": WallstreetCollector,  # 华尔街见闻
    # RSS数据源 - 国内
    "36kr": Kr36Collector,  # 36氪
    # RSS数据源 - 美股
    "wsj_business": WSJBusinessCollector,  # 华尔街日报-经济
    "wsj_markets": WSJMarketsCollector,  # 华尔街日报-市场
    "marketwatch": MarketWatchCollector,  # MarketWatch
    "zerohedge": ZeroHedgeCollector,  # ZeroHedge
    "etf_trends": ETFTrendsCollector,  # ETF Trends
    # RSS数据源 - 国际
    "wsj_social": WSJSocialEconomyCollector,  # 华尔街日报-社会经济
    "bbc_business": BBCBusinessCollector,  # BBC全球经济
}


class CollectorManager:
    """Manages all news collectors."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dedup = DeduplicationService(db)

    async def collect_from(self, source_name: str) -> list[NewsArticle]:
        """Collect articles from a specific source."""
        if source_name not in COLLECTORS:
            logger.error(f"Unknown collector: {source_name}")
            return []

        collector_class = COLLECTORS[source_name]
        collector = collector_class(self.db)

        started_at = datetime.now(timezone.utc)
        new_articles = []
        duplicate_count = 0

        try:
            # Fetch raw articles
            raw_articles = await collector.fetch_articles()
            checkpoint = await collector.get_last_checkpoint()

            # Track max published_at from fetched articles
            max_published_at = None

            for raw in raw_articles:
                # Track max time from all fetched articles
                if raw.published_at:
                    if max_published_at is None or raw.published_at > max_published_at:
                        max_published_at = raw.published_at

                # Skip old articles if we have a checkpoint
                if checkpoint and raw.published_at and raw.published_at <= checkpoint:
                    continue

                # Skip empty titles
                if not raw.title or not raw.title.strip():
                    continue

                # Check for duplicates
                is_dup, content_hash = await self.dedup.is_duplicate(
                    raw.url, raw.title, collector.source_name
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
                    source=collector.source_name,
                    source_category=raw.source_category,
                    published_at=raw.published_at or datetime.now(timezone.utc),
                    content_hash=content_hash,
                )

                self.db.add(article)
                new_articles.append(article)

            await self.db.commit()

            # Save collection log
            finished_at = datetime.now(timezone.utc)

            await collector.save_checkpoint(
                started_at=started_at,
                finished_at=finished_at,
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

    async def collect_all(self) -> dict[str, list[NewsArticle]]:
        """Collect from all registered sources."""
        results = {}
        for source_name in COLLECTORS:
            results[source_name] = await self.collect_from(source_name)
        return results
