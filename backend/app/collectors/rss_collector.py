"""Generic RSS feed collector - High cohesion, low coupling design"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from app.collectors.base import BaseCollector, RawArticle

logger = logging.getLogger(__name__)

# Thread pool for blocking RSS fetch operations
_executor = ThreadPoolExecutor(max_workers=8)


class RSSParser(ABC):
    """Abstract RSS parser - Strategy pattern for different RSS formats"""

    @abstractmethod
    def parse_items(self, root: ET.Element) -> list[ET.Element]:
        """Extract item elements from XML root"""
        pass

    @abstractmethod
    def parse_title(self, item: ET.Element) -> Optional[str]:
        """Extract title from item"""
        pass

    @abstractmethod
    def parse_link(self, item: ET.Element) -> Optional[str]:
        """Extract link from item"""
        pass

    @abstractmethod
    def parse_content(self, item: ET.Element) -> Optional[str]:
        """Extract content from item"""
        pass

    @abstractmethod
    def parse_pubdate(self, item: ET.Element) -> Optional[datetime]:
        """Extract publication date from item"""
        pass


class RSS20Parser(RSSParser):
    """Parser for RSS 2.0 format"""

    def parse_items(self, root: ET.Element) -> list[ET.Element]:
        return root.findall(".//item")

    def parse_title(self, item: ET.Element) -> Optional[str]:
        elem = item.find("title")
        if elem is not None and elem.text:
            return self._clean_cdata(elem.text.strip())
        return None

    def parse_link(self, item: ET.Element) -> Optional[str]:
        elem = item.find("link")
        if elem is not None and elem.text:
            return self._clean_cdata(elem.text.strip())
        return None

    def parse_content(self, item: ET.Element) -> Optional[str]:
        # Try multiple content fields
        for field in ["description", "content", "content:encoded"]:
            elem = item.find(field)
            if elem is not None and elem.text:
                content = self._clean_cdata(elem.text.strip())
                # Strip HTML tags
                content = re.sub(r"<[^>]+>", "", content)
                return content[:1000] if content else None
        return None

    def parse_pubdate(self, item: ET.Element) -> Optional[datetime]:
        elem = item.find("pubDate")
        if elem is not None and elem.text:
            return self._parse_datetime(elem.text.strip())
        return None

    @staticmethod
    def _clean_cdata(text: str) -> str:
        """Remove CDATA wrapper if present"""
        if text.startswith("<![CDATA[") and text.endswith("]]>"):
            return text[9:-3].strip()
        return text

    @staticmethod
    def _parse_datetime(date_str: str) -> Optional[datetime]:
        """Parse various datetime formats"""
        if not date_str:
            return None

        cleaned = date_str.strip()

        # RFC 822 / RFC 2822 with timezone info
        try:
            from email.utils import parsedate_to_datetime

            dt = parsedate_to_datetime(cleaned)
            if dt is not None:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return RSS20Parser._validate_and_fix_datetime(dt, date_str)
        except (TypeError, ValueError):
            pass

        # ISO 8601 variants
        try:
            dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return RSS20Parser._validate_and_fix_datetime(dt, date_str)
        except ValueError:
            pass

        # Common RSS date formats
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 822
            "%a, %d %b %Y %H:%M:%S",  # RFC 822 without timezone
            "%Y-%m-%d %H:%M:%S",  # ISO-like
            "%Y-%m-%dT%H:%M:%S%z",  # ISO 8601
            "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 UTC
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(cleaned, fmt)
                # Ensure timezone aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return RSS20Parser._validate_and_fix_datetime(dt, date_str)
            except ValueError:
                continue

        # Fallback to current time
        logger.warning(f"Could not parse date: {date_str}")
        return datetime.now(timezone.utc)

    @staticmethod
    def _validate_and_fix_datetime(dt: datetime, original_str: str) -> datetime:
        """
        Validate datetime and fix common issues like future dates.

        Some RSS feeds have incorrect years (e.g., 2026 instead of 2025).
        If the date is more than 1 day in the future, assume it's a year typo.
        """
        now = datetime.now(timezone.utc)
        diff = (dt - now).total_seconds()

        # If date is more than 1 day in the future, likely a year error
        if diff > 86400:  # 1 day = 86400 seconds
            # Try subtracting a year
            try:
                fixed_dt = dt.replace(year=dt.year - 1)
                # If this puts it in reasonable range (past or near future), use it
                new_diff = (fixed_dt - now).total_seconds()
                if -31536000 < new_diff <= 86400:  # Within past year to 1 day future
                    logger.warning(
                        f"Date '{original_str}' ({dt.isoformat()}) is in future. "
                        f"Corrected year from {dt.year} to {fixed_dt.year}"
                    )
                    return fixed_dt
            except ValueError:
                pass

            # If correction didn't work, use current time
            logger.warning(
                f"Date '{original_str}' ({dt.isoformat()}) is too far in future. "
                f"Using current time instead."
            )
            return now

        return dt


class AtomParser(RSSParser):
    """Parser for Atom format"""

    ATOM_NS = "{http://www.w3.org/2005/Atom}"

    def parse_items(self, root: ET.Element) -> list[ET.Element]:
        return root.findall(f".//{self.ATOM_NS}entry")

    def parse_title(self, item: ET.Element) -> Optional[str]:
        elem = item.find(f"{self.ATOM_NS}title")
        if elem is not None and elem.text:
            return elem.text.strip()
        return None

    def parse_link(self, item: ET.Element) -> Optional[str]:
        elem = item.find(f"{self.ATOM_NS}link")
        if elem is not None:
            return elem.get("href")
        return None

    def parse_content(self, item: ET.Element) -> Optional[str]:
        for field in [f"{self.ATOM_NS}content", f"{self.ATOM_NS}summary"]:
            elem = item.find(field)
            if elem is not None and elem.text:
                content = re.sub(r"<[^>]+>", "", elem.text.strip())
                return content[:1000] if content else None
        return None

    def parse_pubdate(self, item: ET.Element) -> Optional[datetime]:
        for field in [f"{self.ATOM_NS}published", f"{self.ATOM_NS}updated"]:
            elem = item.find(field)
            if elem is not None and elem.text:
                try:
                    return datetime.fromisoformat(
                        elem.text.strip().replace("Z", "+00:00")
                    )
                except ValueError:
                    pass
        return None


class GenericRSSCollector(BaseCollector):
    """
    Generic RSS collector with configurable parser
    High cohesion: All RSS-specific logic in one place
    Low coupling: Subclasses only need to set configuration
    """

    # Configuration - Override in subclasses
    rss_url: str = ""
    source_category: str = "财经"
    parser_class: type[RSSParser] = RSS20Parser

    def __init__(self, db):
        super().__init__(db)
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
        import httpx

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            resp = httpx.get(
                self.rss_url, headers=headers, timeout=15, follow_redirects=True
            )

            if resp.status_code != 200:
                logger.warning(f"{self.source_name} RSS returned {resp.status_code}")
                return []

            # Parse XML
            root = ET.fromstring(resp.content)

            # Extract items using configured parser
            items = self.parser.parse_items(root)

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
                            "published_at": pubdate or datetime.now(timezone.utc),
                        }
                    )

            return results

        except Exception as e:
            logger.error(f"Error parsing {self.source_name} RSS: {e}")
            return []


# Concrete RSS Collectors - Low coupling, only configuration


class Kr36Collector(GenericRSSCollector):
    """36氪 RSS"""

    source_name = "36kr"
    rss_url = "https://36kr.com/feed"
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
