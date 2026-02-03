"""
Scheduler Service - 定时任务调度

职责：
- 管理定时采集任务
- 并发执行采集器

设计原则：
- 独立运行：不依赖请求上下文
- 容错性：单个采集器失败不影响其他
"""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import async_session_maker
from app.collectors.registry import get_collector_names
from app.services.collection_runner import CollectionRunner
from app.services.cleanup_service import CleanupService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(
    job_defaults={
        "coalesce": True,
        "max_instances": 1,
        "misfire_grace_time": settings.COLLECTION_INTERVAL_SECONDS,
    }
)
_scheduler_started = False

# Timeout for each individual collector (seconds)
COLLECTOR_TIMEOUT = 30
_runner = CollectionRunner(
    session_maker=async_session_maker,
    max_concurrency=settings.COLLECTION_MAX_CONCURRENCY,
    collector_timeout=COLLECTOR_TIMEOUT,
)


async def realtime_collection():
    """Execute news collection in real-time."""
    now = datetime.now(timezone.utc)
    source_names = get_collector_names()
    interval_seconds = settings.COLLECTION_INTERVAL_SECONDS
    window_id = int(now.timestamp() // interval_seconds)

    started = 0
    already_running = 0
    already_scheduled = 0
    for source_name in source_names:
        result = _runner.ensure_scheduled(source_name, window_id)
        if result == "started":
            started += 1
        elif result == "already_running":
            already_running += 1
        else:
            already_scheduled += 1

    logger.info(
        f"Realtime collection window={window_id} interval={interval_seconds}s "
        f"sources={len(source_names)} started={started} running={already_running} "
        f"deduped={already_scheduled}"
    )


async def daily_cleanup():
    async with async_session_maker() as session:
        cleanup_service = CleanupService(session)
        result = await cleanup_service.run_cleanup(
            retention_days=settings.NEWS_RETENTION_DAYS,
            tz_name=settings.CLEANUP_TIMEZONE,
        )

    logger.info(
        f"Daily cleanup finished at {datetime.now(timezone.utc)}: deleted {result['deleted']} article(s), status={result['status']}"
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

    interval_seconds = settings.COLLECTION_INTERVAL_SECONDS
    scheduler.add_job(
        realtime_collection,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id="realtime_collection",
        replace_existing=True,
    )
    scheduler.add_job(
        daily_cleanup,
        trigger=CronTrigger(hour=0, minute=0, timezone=settings.CLEANUP_TIMEZONE),
        id="daily_cleanup",
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
