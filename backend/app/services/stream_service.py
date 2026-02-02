"""
Stream Service - SSE实时推送服务

职责：
- 管理SSE连接
- 实时新闻推送
- 游标管理（增量推送）

设计原则：
- 单一职责：只处理实时流相关逻辑
- 独立运行：不依赖请求上下文，使用独立数据库会话
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.news import NewsArticle
from app.schemas.news import NewsArticleResponse


class StreamService:
    """SSE流服务"""

    def __init__(self, session_maker: async_sessionmaker):
        """
        初始化流服务

        Args:
            session_maker: 异步会话工厂，用于创建独立的数据库会话
        """
        self.session_maker = session_maker

    async def news_event_generator(
        self,
        poll_interval: float = 10.0,
    ) -> AsyncGenerator[str, None]:
        """
        生成SSE事件流

        使用游标机制实现增量推送，避免重复发送。

        Args:
            poll_interval: 轮询间隔（秒）

        Yields:
            str: SSE格式的事件数据
        """
        last_id: UUID | None = None
        last_collected_at: datetime | None = None

        while True:
            async with self.session_maker() as db:
                # 构建游标查询
                query = (
                    select(NewsArticle)
                    .where(NewsArticle.is_filtered == False)
                    .order_by(NewsArticle.collected_at.asc(), NewsArticle.id.asc())
                    .limit(20)
                )

                # 应用游标条件
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

                    # 更新游标
                    last_collected_at = article.collected_at
                    last_id = article.id

            await asyncio.sleep(poll_interval)
