import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.news import NewsArticle

logger = logging.getLogger(__name__)

# Thread pool for sync AI SDK calls
_executor = ThreadPoolExecutor(max_workers=4)


class AIFilterService:
    """GLM-4 AI filtering service (optional module)."""

    def __init__(self):
        self.enabled = bool(settings.GLM_API_KEY)
        self.client = None

        if self.enabled:
            try:
                from zhipuai import ZhipuAI
                self.client = ZhipuAI(api_key=settings.GLM_API_KEY)
                logger.info("AI filtering enabled with GLM-4")
            except ImportError:
                logger.warning("zhipuai package not installed, AI filtering disabled")
                self.enabled = False
        else:
            logger.info("AI filtering disabled: GLM_API_KEY not configured")

    def _call_ai_sync(self, prompt: str) -> dict[str, Any]:
        """Synchronous AI call to be run in thread pool."""
        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=30,
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "quality_score": float(result.get("quality_score", 0.5)),
                "is_spam": bool(result.get("is_spam", False)),
                "category": result.get("category", "其他"),
                "keywords": result.get("keywords", []),
            }
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return self._default_result()

    async def process_article(self, article: NewsArticle) -> dict[str, Any]:
        """Process a single article with AI (non-blocking)."""
        if not self.enabled or not self.client:
            return self._default_result()

        prompt = f"""分析以下财经新闻，返回 JSON 格式结果：

标题：{article.title}
内容：{article.content[:500] if article.content else '无'}

请返回：
{{
  "quality_score": 0.0-1.0 (新闻质量/重要性评分),
  "is_spam": true/false (是否为广告/软文/无意义内容),
  "category": "宏观经济/公司财报/市场动态/政策法规/行业分析/其他",
  "keywords": ["关键词1", "关键词2", ...]
}}"""

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, self._call_ai_sync, prompt)

    def _default_result(self) -> dict[str, Any]:
        """Return default result when AI is disabled or fails."""
        return {
            "quality_score": 0.5,
            "is_spam": False,
            "category": "其他",
            "keywords": [],
        }

    async def batch_process(
        self, db: AsyncSession, articles: list[NewsArticle]
    ) -> int:
        """Process multiple articles in batch with concurrency."""
        if not self.enabled:
            return 0

        processed_count = 0
        unprocessed = [a for a in articles if not a.ai_processed]

        # Process in parallel with limited concurrency
        semaphore = asyncio.Semaphore(4)

        async def process_one(article: NewsArticle) -> bool:
            async with semaphore:
                try:
                    result = await self.process_article(article)
                    article.ai_quality_score = result["quality_score"]
                    article.ai_category = result["category"]
                    article.ai_keywords = result["keywords"]
                    article.is_filtered = result["is_spam"]
                    article.ai_processed = True
                    return True
                except Exception as e:
                    logger.error(f"Failed to process article {article.id}: {e}")
                    return False

        results = await asyncio.gather(
            *[process_one(a) for a in unprocessed],
            return_exceptions=True
        )

        processed_count = sum(1 for r in results if r is True)

        if processed_count > 0:
            await db.commit()

        logger.info(f"AI processed {processed_count}/{len(unprocessed)} articles")
        return processed_count
