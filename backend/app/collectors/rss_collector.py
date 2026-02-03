"""Generic RSS feed collector - High cohesion, low coupling design"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.collectors.base import BaseCollector, RawArticle
from app.collectors.rss_parsers import RSS20Parser, RSSParser

logger = logging.getLogger(__name__)

# Thread pool for blocking RSS fetch operations
_executor = ThreadPoolExecutor(max_workers=8)


class GenericRSSCollector(BaseCollector):
    """
    Generic RSS collector with configurable parser
    High cohesion: All RSS-specific logic in one place
    Low coupling: Subclasses only need to set configuration
    """

    # Configuration - Override in subclasses
    rss_url: str | list[str] = ""
    source_category: str = "财经"
    parser_class: type[RSSParser] = RSS20Parser

    def __init__(self):
        try:
            self.parser = self.parser_class(source_name=self.source_name)
        except TypeError:
            self.parser = self.parser_class()

    async def fetch_articles(self) -> list[RawArticle]:
        """Fetch and parse RSS feed"""
        try:
            loop = asyncio.get_running_loop()
            items = await loop.run_in_executor(_executor, self._fetch_rss)

            if not items:
                return []

            articles = []
            for item_data in items:
                if not item_data["title"] or not item_data["url"]:
                    continue

                article = RawArticle(
                    title=item_data["title"],
                    url=item_data["url"],
                    content=item_data["content"],
                    published_at=item_data["published_at"],
                    source_category=self.source_category,
                )
                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from {self.source_name} RSS")
            return articles

        except Exception as e:
            logger.error(f"Error fetching from {self.source_name}: {e}")
            return []

    def _fetch_rss(self) -> list[dict]:
        """Fetch and parse RSS feed (blocking operation)"""
        from app.utils.http_client import request

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        urls = (
            [self.rss_url]
            if isinstance(self.rss_url, str)
            else list(self.rss_url)
            if isinstance(self.rss_url, Iterable)
            else []
        )

        for url in urls:
            try:
                resp = request(
                    "GET",
                    url,
                    headers=headers,
                    timeout=15,
                    follow_redirects=True,
                )

                if resp.status_code != 200:
                    logger.warning(
                        f"{self.source_name} RSS returned {resp.status_code}: {url}"
                    )
                    continue

                try:
                    root = ET.fromstring(resp.content)
                except ET.ParseError as e:
                    hint = ""
                    try:
                        preview = resp.content[:4096].decode("utf-8", "ignore")
                        if "请完成下列验证后继续" in preview or "拼图" in preview:
                            hint = " (可能被验证码/反爬拦截)"
                    except Exception:
                        pass
                    logger.warning(
                        f"{self.source_name} RSS XML parse failed{hint}: {url} {e}"
                    )
                    continue

                items = self.parser.parse_items(root)
                if not items:
                    continue

                results = []
                for item in items:
                    title = self.parser.parse_title(item)
                    link = self.parser.parse_link(item)
                    content = self.parser.parse_content(item)
                    pubdate = self.parser.parse_pubdate(item)

                    if title and link:
                        results.append(
                            {
                                "title": title,
                                "url": link,
                                "content": content,
                                "published_at": pubdate,
                            }
                        )

                if results:
                    return results

            except Exception as e:
                logger.warning(f"Error fetching/parsing {self.source_name} RSS: {url} {e}")
                continue

        return []


# Concrete RSS Collectors - Low coupling, only configuration


class Kr36Collector(GenericRSSCollector):
    """36氪 RSS"""

    source_name = "36kr"
    rss_url = [
        "https://36kr.com/feed-article",
        "https://36kr.com/feed",
    ]
    source_category = "科技"


class WSJBusinessCollector(GenericRSSCollector):
    """华尔街日报 - 经济"""

    source_name = "wsj_business"
    rss_url = "https://feeds.content.dowjones.io/public/rss/WSJcomUSBusiness"
    source_category = "美股"


class WSJMarketsCollector(GenericRSSCollector):
    """华尔街日报 - 市场"""

    source_name = "wsj_markets"
    rss_url = "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain"
    source_category = "美股"


class MarketWatchCollector(GenericRSSCollector):
    """MarketWatch美股"""

    source_name = "marketwatch"
    rss_url = "https://www.marketwatch.com/rss/topstories"
    source_category = "美股"


class ZeroHedgeCollector(GenericRSSCollector):
    """ZeroHedge华尔街新闻"""

    source_name = "zerohedge"
    rss_url = "https://feeds.feedburner.com/zerohedge/feed"
    source_category = "美股"


class ETFTrendsCollector(GenericRSSCollector):
    """ETF Trends"""

    source_name = "etf_trends"
    rss_url = "https://www.etftrends.com/feed/"
    source_category = "美股"


class WSJSocialEconomyCollector(GenericRSSCollector):
    """华尔街日报 - 社会经济"""

    source_name = "wsj_social"
    rss_url = "https://feeds.content.dowjones.io/public/rss/socialeconomyfeed"
    source_category = "国际"


class BBCBusinessCollector(GenericRSSCollector):
    """BBC全球经济"""

    source_name = "bbc_business"
    rss_url = "http://feeds.bbci.co.uk/news/business/rss.xml"
    source_category = "国际"
