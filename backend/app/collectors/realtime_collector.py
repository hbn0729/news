import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import hashlib

from app.collectors.base import BaseCollector, RawArticle

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4)


def _fetch_jin10():
    """金十数据快讯 - 需要特定 headers"""
    from app.utils.http_client import request

    try:
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "origin": "https://www.jin10.com",
            "referer": "https://www.jin10.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-app-id": "bVBF4FyRTn5NJF5n",
            "x-version": "1.0.0",
        }
        # 注意：不要设置 accept-encoding，让 httpx 自动处理
        resp = request(
            "GET",
            "https://flash-api.jin10.com/get_flash_list",
            params={"channel": "-8200", "vip": "1"},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("data", [])
    except Exception as e:
        logger.error(f"Jin10 fetch error: {e}")
    return []


def _fetch_wallstreet():
    """华尔街见闻"""
    from app.utils.http_client import request

    try:
        resp = request(
            "GET",
            "https://api-one.wallstcn.com/apiv1/content/lives",
            params={"channel": "global-channel", "limit": 50},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("items", [])
    except Exception as e:
        logger.error(f"Wallstreet fetch error: {e}")
    return []


class Jin10Collector(BaseCollector):
    """金十数据快讯采集器"""

    source_name = "jin10"

    async def fetch_articles(self) -> list[RawArticle]:
        try:
            loop = asyncio.get_running_loop()
            items = await loop.run_in_executor(_executor, _fetch_jin10)

            if not items:
                return []

            articles = []
            for item in items:
                content = item.get("data", {})
                title = content.get("content", "")

                if not title:
                    continue

                # 清理 HTML 标签
                title = title.replace("<b>", "").replace("</b>", "")
                title = title.replace("<br>", " ").replace("<br/>", " ")

                if len(title) > 200:
                    title = title[:200] + "..."

                pub_time = item.get("time", "")
                if pub_time:
                    try:
                        # 金十数据返回的是北京时间（CST, UTC+8）
                        pub_time = datetime.strptime(pub_time, "%Y-%m-%d %H:%M:%S")
                        # 正确标记为东八区时间
                        china_tz = timezone(timedelta(hours=8))
                        pub_time = pub_time.replace(tzinfo=china_tz)
                        pub_time = pub_time.astimezone(timezone.utc)
                    except ValueError:
                        pub_time = datetime.now(timezone.utc)
                else:
                    pub_time = datetime.now(timezone.utc)

                # 生成唯一 URL
                # 金十快讯没有独立详情页，使用快讯列表页锚点
                item_id = item.get("id", hashlib.md5(title.encode()).hexdigest()[:8])

                article = RawArticle(
                    title=title,
                    url=f"https://www.jin10.com/flash#{item_id}",
                    content=title,
                    published_at=pub_time,
                    source_category="快讯",
                )
                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from Jin10")
            return articles

        except Exception as e:
            logger.error(f"Error fetching from Jin10: {e}")
            return []


class WallstreetCollector(BaseCollector):
    """华尔街见闻采集器"""

    source_name = "wallstreet"

    async def fetch_articles(self) -> list[RawArticle]:
        try:
            loop = asyncio.get_running_loop()
            items = await loop.run_in_executor(_executor, _fetch_wallstreet)

            if not items:
                return []

            articles = []
            for item in items:
                title = item.get("content_text", "") or item.get("title", "")

                if not title:
                    continue

                pub_time = item.get("display_time", 0)
                if pub_time:
                    pub_time = datetime.fromtimestamp(pub_time, tz=timezone.utc)
                else:
                    pub_time = datetime.now(timezone.utc)

                item_id = item.get("id", "")

                # 华尔街见闻快讯没有独立页面，使用主站 URL
                # 如果有关联文章 URI 则使用文章页面
                uri = item.get("uri", "")
                if uri:
                    # 检查 uri 是否已经是完整 URL
                    if uri.startswith("http://") or uri.startswith("https://"):
                        url = uri
                    else:
                        url = f"https://wallstreetcn.com/{uri}"
                else:
                    # 快讯使用实时页面锚点
                    url = f"https://wallstreetcn.com/livenews#{item_id}"

                article = RawArticle(
                    title=title[:500] if len(title) > 500 else title,
                    url=url,
                    content=title,
                    published_at=pub_time,
                    source_category="快讯",
                )
                articles.append(article)

            logger.info(f"Fetched {len(articles)} articles from Wallstreet")
            return articles

        except Exception as e:
            logger.error(f"Error fetching from Wallstreet: {e}")
            return []
