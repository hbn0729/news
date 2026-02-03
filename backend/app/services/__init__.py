"""
Services Layer - 业务逻辑层

设计原则：
- 每个服务负责单一领域
- 通过依赖注入解耦
- 与路由层分离
"""

from app.services.news_service import NewsService
from app.services.stats_service import StatsService
from app.services.stream_service import StreamService
from app.services.dedup import DeduplicationService
from app.services.cleanup_service import CleanupService
from app.services.collection_service import CollectionService
from app.services.scheduler import scheduler, start_scheduler, stop_scheduler

__all__ = [
    "NewsService",
    "StatsService",
    "StreamService",
    "DeduplicationService",
    "CleanupService",
    "CollectionService",
    "scheduler",
    "start_scheduler",
    "stop_scheduler",
]
