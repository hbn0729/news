import hashlib
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news import NewsArticle


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
        # Remove all non-word characters except Chinese
        title = re.sub(r"[^\w\u4e00-\u9fff]", "", title)
        return title.lower()

    async def is_duplicate(self, url: str, title: str, source: str) -> tuple[bool, str]:
        """
        Check if article is duplicate.
        Returns (is_duplicate, content_hash).
        """
        # Layer 1: URL check
        if await self.check_url_exists(url):
            return True, ""

        # Layer 2: Content hash check
        content_hash = self.compute_content_hash(title, source)
        if await self.check_hash_exists(content_hash):
            return True, content_hash

        return False, content_hash

    async def find_similar_articles(
        self, title: str, threshold: float = 0.85
    ) -> list[NewsArticle]:
        """
        Layer 3: Semantic similarity deduplication (cross-source).
        Uses simple character-level similarity for now.
        Can be enhanced with SimHash or MinHash later.
        """
        normalized = self._normalize_title(title)

        # Get recent articles for comparison
        result = await self.db.execute(
            select(NewsArticle)
            .order_by(NewsArticle.published_at.desc())
            .limit(100)
        )
        recent_articles = result.scalars().all()

        similar = []
        for article in recent_articles:
            article_normalized = self._normalize_title(article.title)
            similarity = self._compute_similarity(normalized, article_normalized)
            if similarity >= threshold:
                similar.append(article)

        return similar

    def _compute_similarity(self, s1: str, s2: str) -> float:
        """Compute character-level Jaccard similarity."""
        if not s1 or not s2:
            return 0.0

        set1 = set(s1)
        set2 = set(s2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0
