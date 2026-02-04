import asyncio
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Import models and services
from app.database import Base
from app.config import settings
from app.models.news import NewsArticle
from app.services.dedup import DeduplicationService

# Use a separate test database or in-memory sqlite if possible
# For now, we'll mock the database or use a test engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

class TestDeduplicationService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Create in-memory sqlite engine for testing
        self.engine = create_async_engine(TEST_DATABASE_URL)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        self.session_maker = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        self.session = self.session_maker()
        settings.DEDUP_SYNONYM_DATA_DIR = "e:\\project\\news\\backend\\app\\data\\chinese-synonyms-test-missing"
        self.dedup_service = DeduplicationService(self.session)

    async def asyncTearDown(self):
        await self.session.close()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_normalize_title(self):
        # Test basic normalization
        self.assertEqual(self.dedup_service._normalize_title("【快讯】美股 全线 收高！"), "美股全线收高")
        self.assertEqual(self.dedup_service._normalize_title("Hello World!!!"), "helloworld")
        self.assertEqual(self.dedup_service._normalize_title(" (图) 华为发布新品 [官方] "), "华为发布新品")
        self.assertEqual(self.dedup_service._normalize_title(""), "")

    async def test_compute_content_hash(self):
        h1 = self.dedup_service.compute_content_hash("美股全线收高", "jin10")
        h2 = self.dedup_service.compute_content_hash("【快讯】 美股全线收高!!!", "jin10")
        self.assertEqual(h1, h2)
        
        h3 = self.dedup_service.compute_content_hash("美股全线收高", "eastmoney")
        self.assertNotEqual(h1, h3)

    async def test_layer1_url_dedup(self):
        url = "https://example.com/news/1"
        article = NewsArticle(
            title="Test News",
            url=url,
            source="test",
            published_at=datetime.now(timezone.utc),
            content_hash="hash1"
        )
        self.session.add(article)
        await self.session.commit()

        is_dup, _ = await self.dedup_service.is_duplicate(url, "Other Title", "other_source")
        self.assertTrue(is_dup)

    async def test_layer2_hash_dedup(self):
        title = "美股全线收高"
        source = "jin10"
        content_hash = self.dedup_service.compute_content_hash(title, source)
        
        article = NewsArticle(
            title=title,
            url="https://example.com/news/1",
            source=source,
            published_at=datetime.now(timezone.utc),
            content_hash=content_hash
        )
        self.session.add(article)
        await self.session.commit()

        # Same title and source, different URL
        is_dup, h = await self.dedup_service.is_duplicate("https://example.com/news/2", title, source)
        self.assertTrue(is_dup)
        self.assertEqual(h, content_hash)

    async def test_layer3_similarity_dedup(self):
        # Add an article using built-in dictionary words
        title1 = "苹果股价上涨，市值突破3万亿美元"
        article = NewsArticle(
            title=title1,
            url="https://example.com/news/1",
            source="jin10",
            published_at=datetime.now(timezone.utc),
            content_hash="hash1"
        )
        self.session.add(article)
        await self.session.commit()

        # Test highly similar title with synonyms
        # 苹果->苹果公司, 股价->股票价格, 上涨->走高, 市值->总市值, 突破->刷新
        title2 = "苹果公司股票价格走高，总市值刷新3万亿"
        print(f"DEBUG: settings.DEDUP_SEMANTIC_THRESHOLD={settings.DEDUP_SEMANTIC_THRESHOLD}")
        is_dup, _ = await self.dedup_service.is_duplicate("https://example.com/news/2", title2, "other_source")
        self.assertTrue(is_dup)

        # Test different title
        title3 = "微软营收下滑，利润低于预期"
        is_dup, _ = await self.dedup_service.is_duplicate("https://example.com/news/3", title3, "other_source")
        self.assertFalse(is_dup)

    async def test_layer3_synonym_enhanced_dedup(self):
        title1 = "苹果市值创新高"
        article = NewsArticle(
            title=title1,
            url="https://example.com/news/10",
            source="jin10",
            published_at=datetime.now(timezone.utc),
            content_hash="hash10"
        )
        self.session.add(article)
        await self.session.commit()

        title2 = "苹果市场价值创新高"
        is_dup, _ = await self.dedup_service.is_duplicate("https://example.com/news/11", title2, "other_source")
        self.assertTrue(is_dup)

    async def test_layer3_custom_synonym_dict_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp)
            (data_dir / "synonyms.json").write_text(
                json.dumps({"并购": ["收购"], "收购": ["并购"]}, ensure_ascii=False),
                encoding="utf-8",
            )
            settings.DEDUP_SYNONYM_DATA_DIR = str(data_dir)

            title1 = "微软并购初创公司"
            article = NewsArticle(
                title=title1,
                url="https://example.com/news/20",
                source="jin10",
                published_at=datetime.now(timezone.utc),
                content_hash="hash20",
            )
            self.session.add(article)
            await self.session.commit()

            title2 = "微软收购初创公司"
            is_dup, _ = await self.dedup_service.is_duplicate(
                "https://example.com/news/21", title2, "other_source"
            )
            self.assertTrue(is_dup)

    async def test_similarity_calculation(self):
        s1 = "abcdef"
        s2 = "abcefg"
        # normalize removes non-word characters. 'abcdef' and 'abcefg' are all word characters.
        # intersection: {a, b, c, d, e, f}, union: {a, b, c, d, e, f, g}
        # intersection size = 5 (a, b, c, e, f), union size = 7 (a, b, c, d, e, f, g)
        # Wait, s1 is {a,b,c,d,e,f}, s2 is {a,b,c,e,f,g}
        # intersection is {a,b,c,e,f}, which is 5 elements.
        # union is {a,b,c,d,e,f,g}, which is 7 elements.
        # 5/7 = 0.7142857142857143
        sim = self.dedup_service._compute_similarity(s1, s2)
        self.assertAlmostEqual(sim, 5/7)

if __name__ == "__main__":
    asyncio.run(unittest.main())
