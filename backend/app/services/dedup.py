import hashlib
import re
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.news import NewsArticle
from app.services.news_dedup.advanced_deduplicator import AdvancedDedupConfig, AdvancedDeduplicator
from app.services.news_dedup.chinese_synonym_engine import get_chinese_synonym_engine
from app.services.news_dedup.types import NewsText


class DeduplicationService:
    """Three-layer deduplication strategy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_url_exists(self, url: str) -> bool:
        """Layer 1: Exact URL deduplication."""
        result = await self.db.execute(
            select(NewsArticle.id).where(NewsArticle.url == url).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def check_hash_exists(self, content_hash: str) -> bool:
        """Layer 2: Content hash deduplication."""
        result = await self.db.execute(
            select(NewsArticle.id)
            .where(NewsArticle.content_hash == content_hash)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    def compute_content_hash(self, title: str, source: str) -> str:
        """Compute content fingerprint for deduplication."""
        normalized = self._normalize_title(title)
        return hashlib.sha256(f"{normalized}|{source}".encode()).hexdigest()

    def _normalize_title(self, title: str) -> str:
        """Normalize title: remove punctuation, spaces, convert to lowercase."""
        if not title:
            return ""
        # Remove common financial news tags like 【...】, [...], (口述), (图) etc.
        title = re.sub(r"[【\[\(].*?[】\]\)]", "", title)
        # Remove all non-word characters except Chinese characters
        # \w matches [a-zA-Z0-9_]
        title = re.sub(r"[^\w\u4e00-\u9fff]", "", title)
        return title.lower()

    async def is_duplicate(
        self, url: str, title: str, source: str, content: str = "", summary: str = ""
    ) -> tuple[bool, str]:
        """
        Check if article is duplicate.
        Returns (is_duplicate, content_hash).
        """
        if await self.check_url_exists(url):
            return True, ""

        content_hash = self.compute_content_hash(title, source)
        if await self.check_hash_exists(content_hash):
            return True, content_hash

        similar_articles = await self.find_similar_articles(
            NewsText(title=title, content=content or "", summary=summary or "")
        )
        if similar_articles:
            return True, content_hash

        return False, content_hash

    async def find_similar_articles(
        self, current: NewsText
    ) -> list[NewsArticle]:
        """
        Layer 3: Semantic similarity deduplication (cross-source).
        Uses semantic elements and synonym-enhanced similarity.
        """
        recent_limit = max(1, int(settings.DEDUP_RECENT_LIMIT))
        result = await self.db.execute(
            select(NewsArticle)
            .order_by(NewsArticle.published_at.desc())
            .limit(recent_limit)
        )
        recent_articles = result.scalars().all()
        
        synonym_engine = None
        if settings.DEDUP_ENABLE_SYNONYMS:
            data_dir = (
                Path(settings.DEDUP_SYNONYM_DATA_DIR)
                if settings.DEDUP_SYNONYM_DATA_DIR
                else Path(__file__).resolve().parents[1] / "data" / "chinese-synonyms"
            )
            synonym_engine = get_chinese_synonym_engine(
                str(data_dir), preferred_source=settings.DEDUP_SYNONYM_SOURCE
            )

        deduplicator = AdvancedDeduplicator(
            AdvancedDedupConfig(
                semantic_threshold=float(settings.DEDUP_SEMANTIC_THRESHOLD),
                synonym_threshold=float(settings.DEDUP_SYNONYM_THRESHOLD),
                enable_synonyms=bool(settings.DEDUP_ENABLE_SYNONYMS),
                synonym_source=str(settings.DEDUP_SYNONYM_SOURCE),
            ),
            synonym_engine=synonym_engine,
        )

        for article in recent_articles:
            candidate = NewsText(
                title=article.title,
                content=article.content or "",
                summary=article.summary or "",
            )
            result = deduplicator.compare(current, candidate)
            if result.is_duplicate:
                return [article]

        return []

    def _compute_similarity(self, s1: str, s2: str) -> float:
        """Compute character-level Jaccard similarity."""
        if not s1 or not s2:
            return 0.0

        set1 = set(s1)
        set2 = set(s2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0
