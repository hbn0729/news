"""
Stream Routes - SSE实时推送路由

职责：
- SSE新闻流端点
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_stream_service
from app.services import StreamService
from app.schemas.news import NewsArticleResponse

router = APIRouter(tags=["stream"])


@router.get("/news/stream")
async def news_stream(
    service: StreamService = Depends(get_stream_service),
):
    """SSE endpoint for real-time news updates."""

    async def sse_generator():
        async for article in service.news_article_generator():
            data = NewsArticleResponse.model_validate(article).model_dump_json()
            yield f"data: {data}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
