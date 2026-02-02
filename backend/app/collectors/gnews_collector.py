"""
Google News 财经新闻采集器

本模块使用内置的 gnews 库（位于 app.utils.gnews）来采集 Google News 财经新闻。
gnews 库源自 https://github.com/ranahaani/GNews，已集成到项目中以便更好的控制和维护。

注意：需要配置代理（HTTPS_PROXY 或 HTTP_PROXY）才能正常访问 Google News。
"""

import asyncio
import logging
import re
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import httpx

from app.collectors.base import BaseCollector, RawArticle

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)

# 财经金融相关主题
FINANCE_TOPICS = [
    "BUSINESS",
    "ECONOMY",
    "FINANCE",
    "PERSONAL FINANCE",
    "DIGITAL CURRENCIES",
]

# 财经金融关键词（中英文）
FINANCE_KEYWORDS = [
    "金融",
    "财经",
    "股票",
    "基金",
    "证券",
    "finance",
    "stock market",
    "investment",
]


def _decode_google_news_url(google_url: str) -> str:
    """
    解码 Google News 跳转链接，获取原始文章 URL。
    Google News URL 格式: https://news.google.com/rss/articles/BASE64_ENCODED_DATA
    """
    if not google_url or "news.google.com" not in google_url:
        return google_url

    try:
        # 方法1: 尝试从 URL 路径中提取 base64 编码的数据
        match = re.search(r"/articles/([^?]+)", google_url)
        if match:
            encoded = match.group(1)
            # Google 使用修改过的 base64，需要补齐 padding
            padding = 4 - len(encoded) % 4
            if padding != 4:
                encoded += "=" * padding

            try:
                decoded = base64.urlsafe_b64decode(encoded)
                # 在解码数据中查找 URL
                url_match = re.search(rb"https?://[^\x00-\x1f\x7f-\xff]+", decoded)
                if url_match:
                    return url_match.group(0).decode("utf-8", errors="ignore")
            except Exception:
                pass

        # 方法2: 通过 HTTP HEAD 请求获取重定向后的真实 URL
        try:
            resp = httpx.head(
                google_url,
                follow_redirects=True,
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            final_url = str(resp.url)
            if "news.google.com" not in final_url:
                return final_url
        except Exception:
            pass

    except Exception as e:
        logger.debug(f"Failed to decode Google News URL: {e}")

    return google_url


def _parse_published_date(pub_time_str: str | None) -> datetime:
    """解析发布时间字符串为 datetime 对象"""
    if isinstance(pub_time_str, str):
        try:
            pub_time = datetime.strptime(pub_time_str, "%a, %d %b %Y %H:%M:%S %Z")
            return pub_time.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _fetch_gnews_by_topic(
    topic: str, language: str, country: str, max_results: int
) -> list[dict]:
    """按主题获取新闻"""
    from app.utils.gnews import GNews
    from app.config import settings

    try:
        # 构建代理配置
        proxy = None
        if settings.HTTPS_PROXY:
            proxy = {"https": settings.HTTPS_PROXY}
        elif settings.HTTP_PROXY:
            proxy = {"http": settings.HTTP_PROXY}

        google_news = GNews(
            language=language,
            country=country,
            max_results=max_results,
            period="1d",  # 只获取最近1天的新闻
            proxy=proxy,
        )
        items = google_news.get_news_by_topic(topic)
        return items or []
    except Exception as e:
        logger.error(f"Error fetching topic {topic}: {e}")
        return []


def _fetch_gnews_by_keyword(
    keyword: str, language: str, country: str, max_results: int
) -> list[dict]:
    """按关键词搜索新闻"""
    from app.utils.gnews import GNews
    from app.config import settings

    try:
        # 构建代理配置
        proxy = None
        if settings.HTTPS_PROXY:
            proxy = {"https": settings.HTTPS_PROXY}
        elif settings.HTTP_PROXY:
            proxy = {"http": settings.HTTP_PROXY}

        google_news = GNews(
            language=language,
            country=country,
            max_results=max_results,
            period="1d",  # 只获取最近1天的新闻
            proxy=proxy,
        )
        items = google_news.get_news(keyword)
        return items or []
    except Exception as e:
        logger.error(f"Error fetching keyword {keyword}: {e}")
        return []


def _fetch_all_finance_news() -> list[dict]:
    """
    综合获取财经金融新闻：
    1. 中文财经主题新闻
    2. 英文财经主题新闻
    3. 关键词搜索新闻
    """
    all_items = []
    seen_urls = set()

    # 1. 中文财经主题 (China + Simplified Chinese)
    for topic in FINANCE_TOPICS[:3]:  # BUSINESS, ECONOMY, FINANCE
        items = _fetch_gnews_by_topic(topic, "zh-Hans", "CN", 15)
        for item in items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                item["_source_category"] = f"财经-{topic}"
                all_items.append(item)
                seen_urls.add(url)

    # 2. 英文国际财经新闻 (US + English)
    for topic in FINANCE_TOPICS[:2]:  # BUSINESS, ECONOMY
        items = _fetch_gnews_by_topic(topic, "en", "US", 10)
        for item in items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                item["_source_category"] = f"国际财经-{topic}"
                all_items.append(item)
                seen_urls.add(url)

    # 3. 中文关键词搜索
    for keyword in FINANCE_KEYWORDS[:4]:  # 金融, 财经, 股票, 基金
        items = _fetch_gnews_by_keyword(keyword, "zh-Hans", "CN", 10)
        for item in items:
            url = item.get("url", "")
            if url and url not in seen_urls:
                item["_source_category"] = f"搜索-{keyword}"
                all_items.append(item)
                seen_urls.add(url)

    # 4. 解析真实 URL
    resolved_items = []
    for item in all_items:
        url = item.get("url", "")
        if url:
            item["url"] = _decode_google_news_url(url)
        resolved_items.append(item)

    return resolved_items


class GNewsCollector(BaseCollector):
    """Google News 财经新闻采集器 - 需要配置代理才能正常工作"""

    source_name = "gnews"

    async def fetch_articles(self) -> list[RawArticle]:
        from app.config import settings

        # 检查是否配置了代理，未配置则跳过
        if not settings.HTTPS_PROXY and not settings.HTTP_PROXY:
            logger.info(
                "GNews collector skipped: no proxy configured (HTTPS_PROXY or HTTP_PROXY required)"
            )
            return []

        try:
            loop = asyncio.get_running_loop()

            # 在线程池中执行同步的 gnews 调用
            news_items = await loop.run_in_executor(_executor, _fetch_all_finance_news)

            if not news_items:
                logger.info("No news items fetched from GNews")
                return []

            articles = []
            for item in news_items:
                pub_time = _parse_published_date(item.get("published date"))

                title = item.get("title", "")
                url = item.get("url", "")

                if not title or not url:
                    continue

                # 跳过仍然是 Google News 跳转的 URL
                if "news.google.com" in url:
                    logger.debug(f"Skipping unresolved Google News URL: {title}")
                    continue

                source_category = item.get("_source_category", "国际财经")

                article = RawArticle(
                    title=title,
                    url=url,
                    content=item.get("description", ""),
                    published_at=pub_time,
                    source_category=source_category,
                )
                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from GNews (multi-topic)")
            return articles

        except Exception as e:
            logger.error(f"Error fetching from GNews: {e}")
            return []
