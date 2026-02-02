import asyncio
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.collectors.base import BaseCollector, RawArticle
from app.utils.timezone import parse_datetime

logger = logging.getLogger(__name__)

# Thread pool for sync library calls
_executor = ThreadPoolExecutor(max_workers=8)


def _fetch_eastmoney_rss():
    """东方财富财经新闻 - 使用RSS feed"""
    import httpx
    import xml.etree.ElementTree as ET
    from datetime import datetime

    try:
        url = "http://rss.eastmoney.com/rss_partener.xml"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        resp = httpx.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Eastmoney RSS returned {resp.status_code}")
            return []

        # Parse XML
        root = ET.fromstring(resp.content)

        # Find all item elements
        items = []
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            desc_elem = item.find("description")

            if title_elem is None or link_elem is None:
                continue

            title = title_elem.text or ""
            link = link_elem.text or ""

            # Clean CDATA if present
            if title.startswith("<![CDATA["):
                title = title[9:-3]
            if link.startswith("<![CDATA["):
                link = link[9:-3]

            # Parse pubDate
            pub_time = None
            if pub_date_elem is not None and pub_date_elem.text:
                try:
                    # Format: Sun, 01 Feb 2026 17:30:46 +0800
                    pub_time = datetime.strptime(
                        pub_date_elem.text[:25], "%a, %d %b %Y %H:%M:%S"
                    )
                    pub_time = pub_time.replace(tzinfo=timezone.utc)
                except ValueError:
                    pub_time = datetime.now(timezone.utc)
            else:
                pub_time = datetime.now(timezone.utc)

            # Get description as content
            content = None
            if desc_elem is not None and desc_elem.text:
                content = desc_elem.text
                if content.startswith("<![CDATA["):
                    content = content[9:-3]
                # Strip HTML tags for cleaner content
                import re

                content = re.sub(r"<[^>]+>", "", content)
                content = content[:500]  # Limit length

            items.append(
                {
                    "title": title,
                    "url": link,
                    "content": content,
                    "published_at": pub_time,
                }
            )

        return items
    except Exception as e:
        logger.error(f"Error fetching Eastmoney RSS: {e}")
        return []


def _fetch_cls_telegraph():
    """财联社电报 - 使用 stock_info_global_cls 接口"""
    import akshare as ak

    try:
        return ak.stock_info_global_cls()
    except Exception:
        return None


def _fetch_sina_finance():
    """新浪财经新闻"""
    import akshare as ak

    try:
        return ak.stock_news_em()
    except Exception:
        return None


def _fetch_eastmoney_ggzjl():
    """东方财富个股资金流"""
    import akshare as ak

    try:
        return ak.stock_individual_fund_flow_rank(indicator="今日")
    except Exception:
        return None


class AkShareEastmoneyCollector(BaseCollector):
    """东方财富财经新闻采集器 - 使用RSS feed"""

    source_name = "eastmoney"

    async def fetch_articles(self) -> list[RawArticle]:
        try:
            loop = asyncio.get_running_loop()
            items = await loop.run_in_executor(_executor, _fetch_eastmoney_rss)

            if not items:
                return []

            articles = []
            for item in items:
                article = RawArticle(
                    title=item["title"],
                    url=item["url"],
                    content=item["content"],
                    published_at=item["published_at"],
                    source_category="财经",
                )
                if article.title and article.url:
                    articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from Eastmoney RSS")
            return articles

        except Exception as e:
            logger.error(f"Error fetching from Eastmoney: {e}")
            return []


class AkShareCLSCollector(BaseCollector):
    """财联社电报采集器 - 使用 stock_info_global_cls 接口"""

    source_name = "cls"

    async def fetch_articles(self) -> list[RawArticle]:
        try:
            loop = asyncio.get_running_loop()
            df = await loop.run_in_executor(_executor, _fetch_cls_telegraph)

            if df is None or df.empty:
                return []

            articles = []
            for idx, row in df.iterrows():
                # 新接口列名: ['标题', '内容', '发布日期', '发布时间']
                title = str(row.get("标题", ""))

                if not title:
                    continue

                # 组合发布日期和时间
                pub_date = str(row.get("发布日期", ""))
                pub_time_str = str(row.get("发布时间", ""))
                if pub_date and pub_time_str:
                    datetime_str = f"{pub_date} {pub_time_str}"
                    pub_time = parse_datetime(datetime_str, self.source_name)
                else:
                    pub_time = datetime.now(timezone.utc)

                # 财联社快讯没有独立页面，使用快讯首页
                # 生成唯一URL：使用发布时间戳作为锚点避免去重过滤
                time_anchor = pub_time.strftime("%Y%m%d%H%M%S")
                title_hash = hashlib.md5(title.encode()).hexdigest()[:8]
                url = f"https://www.cls.cn/telegraph#{time_anchor}-{title_hash}"

                content = str(row.get("内容", "")) if "内容" in row else None

                article = RawArticle(
                    title=title,
                    url=url,
                    content=content,
                    published_at=pub_time,
                    source_category="快讯",
                )
                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from CLS")
            return articles

        except Exception as e:
            logger.error(f"Error fetching from CLS: {e}")
            return []
