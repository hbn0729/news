"""
API Routes Aggregation

将所有路由模块聚合为统一的router
"""

from fastapi import APIRouter

from app.api.news import router as news_router
from app.api.stats import router as stats_router
from app.api.collection import router as collection_router
from app.api.stream import router as stream_router

router = APIRouter()

# 注册所有路由
router.include_router(news_router)
router.include_router(stats_router)
router.include_router(collection_router)
router.include_router(stream_router)
