import asyncio
from datetime import datetime, timezone
from uuid import UUID
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_maker
from app.models.news import NewsArticle, CollectionLog
from app.schemas.news import (
    NewsArticleResponse,
    NewsArticleUpdate,
    PaginatedNews,
    CollectionLogResponse,
)
from app.config import settings
from app.collectors.manager import CollectorManager

router = APIRouter()


@router.get("/news", response_model=PaginatedNews)
async def get_news(
    page: int = Query(1, ge=1),
    per_page: int = Query(default=None, ge=1, le=100),
    source: str | None = None,
    category: str | None = None,
    min_quality: float | None = Query(default=None, ge=0.0, le=1.0),
    search: str | None = None,
    starred_only: bool = False,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Get paginated news list with filtering."""
    # Use settings defaults
    if per_page is None:
        per_page = settings.DEFAULT_PAGE_SIZE
    if min_quality is None:
        min_quality = settings.AI_QUALITY_THRESHOLD

    # Base query - exclude filtered articles
    query = select(NewsArticle).where(NewsArticle.is_filtered == False)

    # Apply filters
    if source:
        query = query.where(NewsArticle.source == source)
    if category:
        query = query.where(NewsArticle.ai_category == category)
    if min_quality > 0:
        query = query.where(
            (NewsArticle.ai_quality_score >= min_quality)
            | (NewsArticle.ai_quality_score.is_(None))
        )
    if search:
        query = query.where(NewsArticle.title.ilike(f"%{search}%"))
    if starred_only:
        query = query.where(NewsArticle.is_starred == True)
    if unread_only:
        query = query.where(NewsArticle.is_read == False)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Paginate
    query = query.order_by(NewsArticle.published_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedNews(
        items=[NewsArticleResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page if total > 0 else 0,
    )


@router.get("/news/stream")
async def news_stream():
    """SSE endpoint for real-time news updates using cursor-based watermark."""

    async def event_generator() -> AsyncGenerator[str, None]:
        last_id: UUID | None = None
        last_collected_at: datetime | None = None

        while True:
            # Use a fresh session for each query to avoid connection pool exhaustion
            async with async_session_maker() as db:
                # Build cursor-based query
                query = (
                    select(NewsArticle)
                    .where(NewsArticle.is_filtered == False)
                    .order_by(NewsArticle.collected_at.asc(), NewsArticle.id.asc())
                    .limit(20)
                )

                # Apply cursor if we have one
                if last_collected_at is not None and last_id is not None:
                    query = query.where(
                        (NewsArticle.collected_at > last_collected_at)
                        | (
                            (NewsArticle.collected_at == last_collected_at)
                            & (NewsArticle.id > last_id)
                        )
                    )

                result = await db.execute(query)
                new_articles = result.scalars().all()

                for article in new_articles:
                    data = NewsArticleResponse.model_validate(article).model_dump_json()
                    yield f"data: {data}\n\n"
                    # Update cursor
                    last_collected_at = article.collected_at
                    last_id = article.id

            await asyncio.sleep(10)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/news/{article_id}", response_model=NewsArticleResponse)
async def get_article(
    article_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single article by ID."""
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return NewsArticleResponse.model_validate(article)


@router.patch("/news/{article_id}", response_model=NewsArticleResponse)
async def update_article(
    article_id: UUID,
    update_data: NewsArticleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update article status (read/starred)."""
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if update_data.is_read is not None:
        article.is_read = update_data.is_read
    if update_data.is_starred is not None:
        article.is_starred = update_data.is_starred

    await db.commit()
    await db.refresh(article)

    return NewsArticleResponse.model_validate(article)


@router.post("/news/mark-all-read")
async def mark_all_read(
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Mark all articles as read using bulk update."""
    stmt = update(NewsArticle).where(NewsArticle.is_read == False)

    if source:
        stmt = stmt.where(NewsArticle.source == source)

    stmt = stmt.values(is_read=True)
    result = await db.execute(stmt)
    await db.commit()

    return {"marked_read": result.rowcount}


@router.get("/sources")
async def get_sources(db: AsyncSession = Depends(get_db)):
    """Get list of available news sources with counts."""
    result = await db.execute(
        select(
            NewsArticle.source,
            func.count(NewsArticle.id).label("count"),
        )
        .where(NewsArticle.is_filtered == False)
        .group_by(NewsArticle.source)
    )
    sources = result.all()

    return [{"source": s.source, "count": s.count} for s in sources]


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get list of AI categories with counts."""
    result = await db.execute(
        select(
            NewsArticle.ai_category,
            func.count(NewsArticle.id).label("count"),
        )
        .where(NewsArticle.is_filtered == False)
        .where(NewsArticle.ai_category.isnot(None))
        .group_by(NewsArticle.ai_category)
    )
    categories = result.all()

    return [{"category": c.ai_category, "count": c.count} for c in categories]


@router.post("/collect")
async def trigger_collection(
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger news collection."""
    manager = CollectorManager(db)

    if source:
        articles = await manager.collect_from(source)
        return {
            "source": source,
            "new_articles": len(articles),
        }
    else:
        results = await manager.collect_all()
        return {source_name: len(articles) for source_name, articles in results.items()}


@router.get("/collection-logs", response_model=list[CollectionLogResponse])
async def get_collection_logs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get recent collection logs."""
    result = await db.execute(
        select(CollectionLog).order_by(CollectionLog.started_at.desc()).limit(limit)
    )
    logs = result.scalars().all()

    return [CollectionLogResponse.model_validate(log) for log in logs]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get overall statistics."""
    # Total articles
    total_result = await db.execute(select(func.count(NewsArticle.id)))
    total = total_result.scalar_one()

    # Unread count
    unread_result = await db.execute(
        select(func.count(NewsArticle.id)).where(NewsArticle.is_read == False)
    )
    unread = unread_result.scalar_one()

    # Starred count
    starred_result = await db.execute(
        select(func.count(NewsArticle.id)).where(NewsArticle.is_starred == True)
    )
    starred = starred_result.scalar_one()

    # Filtered count
    filtered_result = await db.execute(
        select(func.count(NewsArticle.id)).where(NewsArticle.is_filtered == True)
    )
    filtered = filtered_result.scalar_one()

    # AI processed count
    ai_processed_result = await db.execute(
        select(func.count(NewsArticle.id)).where(NewsArticle.ai_processed == True)
    )
    ai_processed = ai_processed_result.scalar_one()

    return {
        "total_articles": total,
        "unread": unread,
        "starred": starred,
        "filtered": filtered,
        "ai_processed": ai_processed,
    }
