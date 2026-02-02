import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import async_session_maker

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_scheduler_started = False

# Timeout for each individual collector (seconds)
COLLECTOR_TIMEOUT = 30


async def collect_with_timeout(
    manager, source_name: str, timeout: int = COLLECTOR_TIMEOUT
):
    """Collect from a source with timeout protection."""
    try:
        return await asyncio.wait_for(
            manager.collect_from(source_name), timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Collector {source_name} timed out after {timeout}s")
        return []
    except Exception as e:
        logger.error(f"Collector {source_name} failed: {e}")
        return []


async def realtime_collection():
    """Execute news collection in real-time (every minute)."""
    from app.collectors.manager import CollectorManager, COLLECTORS

    logger.info(f"Starting realtime collection at {datetime.now(timezone.utc)}")

    async with async_session_maker() as db:
        manager = CollectorManager(db)

        # Collect from all sources with individual timeouts
        tasks = [
            collect_with_timeout(manager, source_name)
            for source_name in COLLECTORS.keys()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Gather new articles
        new_articles = []
        for i, result in enumerate(results):
            source_name = list(COLLECTORS.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Collection error for {source_name}: {result}")
            elif result:
                new_articles.extend(result)

        if new_articles:
            logger.info(
                f"Collected {len(new_articles)} new articles from {len(COLLECTORS)} sources"
            )


def start_scheduler():
    """Start the scheduler with realtime collection."""
    global _scheduler_started

    if _scheduler_started:
        logger.warning("Scheduler already started, skipping duplicate start")
        return

    if scheduler.running:
        logger.warning("Scheduler already running, skipping")
        return

    # Realtime collection: use interval from settings (in seconds)
    interval_seconds = settings.COLLECTION_INTERVAL_SECONDS
    scheduler.add_job(
        realtime_collection,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id="realtime_collection",
        replace_existing=True,
    )

    scheduler.start()
    _scheduler_started = True
    logger.info(
        f"Scheduler started: realtime collection every {interval_seconds} second(s)"
    )

    # Run immediately on startup
    asyncio.create_task(realtime_collection())


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler_started

    if scheduler.running:
        scheduler.shutdown(wait=False)
        _scheduler_started = False
        logger.info("Scheduler stopped")
