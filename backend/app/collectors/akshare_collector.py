"""
AkShare & RSS Based Collectors

设计原则：
- 复用 GenericRSSCollector 基类
- 只需配置 URL 和解析参数
"""

import asyncio
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.collectors.base import BaseCollector, RawArticle
from app.collectors.rss_collector import GenericRSSCollector
from app.utils.timezone import parse_datetime

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=8)


# ============================================
# RSS-based collectors - 复用 GenericRSSCollector
# ============================================


class AkShareEastmoneyCollector(GenericRSSCollector):
    """东方财富财经新闻 - RSS方式"""

    source_name = "eastmoney"
    rss_url = "http://rss.eastmoney.com/rss_partener.xml"
    source_category = "财经"


class ITJuziCollector(GenericRSSCollector):
    """IT桔子创投快讯 - RSS方式"""

    source_name = "itjuzi"
    rss_url = "https://www.itjuzi.com/api/telegraph.xml"
    source_category = "创投"


# ============================================
# AkShare API-based collectors
# ============================================


def _fetch_cls_telegraph():
    """财联社电报 - 使用 stock_info_global_cls 接口"""
    import akshare as ak

    try:
        return ak.stock_info_global_cls()
    except Exception:
        return None


class AkShareCLSCollector(BaseCollector):
    """财联社电报采集器 - 使用 AkShare API"""

    source_name = "cls"

    async def fetch_articles(self) -> list[RawArticle]:
        try:
            loop = asyncio.get_running_loop()
            df = await loop.run_in_executor(_executor, _fetch_cls_telegraph)

            if df is None or df.empty:
                return []

            articles = []
            for idx, row in df.iterrows():
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

                # 生成唯一URL
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
