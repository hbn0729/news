"""
News Routes - 新闻相关API路由

职责：
- 新闻列表查询
- 单篇文章查询
- 文章状态更新
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_news_service
from app.config import settings
from app.schemas.news import (
    NewsArticleResponse,
    NewsArticleUpdate,
    PaginatedNews,
)
from app.services import NewsService

router = APIRouter(prefix="/news", tags=["news"])


@router.get("", response_model=PaginatedNews)
async def get_news(
    page: int = Query(1, ge=1),
    per_page: int = Query(default=None, ge=1, le=100),
    source: str | None = None,
    category: str | None = None,
    search: str | None = None,
    published_date: date | None = Query(default=None),
    starred_only: bool = False,
    unread_only: bool = False,
    service: NewsService = Depends(get_news_service),
):
    """Get paginated news list with filtering."""
    if per_page is None:
        per_page = settings.DEFAULT_PAGE_SIZE

    articles, total = await service.get_paginated_news(
        page=page,
        per_page=per_page,
        source=source,
        category=category,
        search=search,
        published_date=published_date,
        starred_only=starred_only,
        unread_only=unread_only,
    )

    return PaginatedNews(
        items=[NewsArticleResponse.model_validate(item) for item in articles],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 0,
    )


@router.get("/{article_id}", response_model=NewsArticleResponse)
async def get_article(
    article_id: UUID,
    service: NewsService = Depends(get_news_service),
):
    """Get a single article by ID."""
    article = await service.get_article_by_id(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return NewsArticleResponse.model_validate(article)


@router.patch("/{article_id}", response_model=NewsArticleResponse)
async def update_article(
    article_id: UUID,
    update_data: NewsArticleUpdate,
    service: NewsService = Depends(get_news_service),
):
    """Update article status (read/starred)."""
    article = await service.update_article_status(
        article_id=article_id,
        is_read=update_data.is_read,
        is_starred=update_data.is_starred,
    )

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return NewsArticleResponse.model_validate(article)


@router.post("/mark-all-read")
async def mark_all_read(
    source: str | None = None,
    service: NewsService = Depends(get_news_service),
):
    """Mark all articles as read."""
    count = await service.mark_all_as_read(source)
    return {"marked_read": count}
