from __future__ import annotations

import asyncio
import logging

from app.collectors.manager import CollectorManager

logger = logging.getLogger(__name__)


class CollectionRunner:
    def __init__(
        self,
        *,
        session_maker,
        max_concurrency: int,
        collector_timeout: int,
    ):
        self._session_maker = session_maker
        self._max_concurrency = max_concurrency
        self._collector_timeout = collector_timeout
        self._semaphore = asyncio.Semaphore(self._max_concurrency)
        self._running_tasks: dict[str, asyncio.Task[list]] = {}
        self._last_window_started: dict[str, int] = {}

    def ensure_scheduled(self, source_name: str, window_id: int) -> str:
        existing = self._running_tasks.get(source_name)
        if existing is not None and not existing.done():
            self._last_window_started[source_name] = window_id
            return "already_running"

        if self._last_window_started.get(source_name) == window_id:
            return "already_scheduled"

        self._last_window_started[source_name] = window_id

        task = asyncio.create_task(self._guarded_collect(source_name))
        self._running_tasks[source_name] = task
        task.add_done_callback(lambda _t, sn=source_name: self._running_tasks.pop(sn, None))
        return "started"

    async def _run_one(self, source_name: str) -> list:
        async with self._session_maker() as db:
            manager = CollectorManager(db, log_session_maker=self._session_maker)
            return await asyncio.wait_for(
                manager.collect_from(source_name), timeout=self._collector_timeout
            )

    async def _guarded_collect(self, source_name: str) -> list:
        loop = asyncio.get_running_loop()
        start = loop.time()
        try:
            async with self._semaphore:
                try:
                    results = await self._run_one(source_name)
                    duration_ms = int((loop.time() - start) * 1000)
                    logger.info(
                        f"Collector {source_name} finished: items={len(results)} duration_ms={duration_ms}"
                    )
                    return results
                except asyncio.TimeoutError:
                    duration_ms = int((loop.time() - start) * 1000)
                    logger.warning(
                        f"Collector {source_name} timed out after {self._collector_timeout}s duration_ms={duration_ms}"
                    )
                    return []
        except asyncio.CancelledError:
            duration_ms = int((loop.time() - start) * 1000)
            logger.warning(f"Collector {source_name} cancelled duration_ms={duration_ms}")
            raise
        except Exception as e:
            duration_ms = int((loop.time() - start) * 1000)
            logger.error(f"Collector {source_name} failed duration_ms={duration_ms}: {e}")
            return []

    async def run_all(self, source_names: list[str]) -> dict[str, list]:
        tasks = [self._guarded_collect(source_name) for source_name in source_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: dict[str, list] = {}
        for i, result in enumerate(results):
            source_name = source_names[i]
            if isinstance(result, Exception):
                logger.error(f"Collection error for {source_name}: {result}")
                output[source_name] = []
            else:
                output[source_name] = result

        return output
