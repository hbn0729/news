"""
Collector Registry - 采集器注册表

职责：
- 集中管理所有可用的采集器
- 便于添加/移除采集器

设计原则：
- 开闭原则：添加新采集器只需在此注册
"""

from importlib import import_module
from typing import Type

from app.collectors.base import BaseCollector


_COLLECTOR_SPECS: dict[str, str] = {
    # AkShare 数据源
    "eastmoney": "app.collectors.akshare_collector:AkShareEastmoneyCollector",
    "cls": "app.collectors.akshare_collector:AkShareCLSCollector",
    # 创投数据源
    "itjuzi": "app.collectors.akshare_collector:ITJuziCollector",
    # 实时快讯数据源
    "jin10": "app.collectors.realtime_collector:Jin10Collector",
    "wallstreet": "app.collectors.realtime_collector:WallstreetCollector",
    # RSS数据源 - 国内
    "36kr": "app.collectors.rss_collector:Kr36Collector",
    # RSS数据源 - 美股
    "wsj_business": "app.collectors.rss_collector:WSJBusinessCollector",
    "wsj_markets": "app.collectors.rss_collector:WSJMarketsCollector",
    "marketwatch": "app.collectors.rss_collector:MarketWatchCollector",
    "zerohedge": "app.collectors.rss_collector:ZeroHedgeCollector",
    "etf_trends": "app.collectors.rss_collector:ETFTrendsCollector",
    # RSS数据源 - 国际
    "wsj_social": "app.collectors.rss_collector:WSJSocialEconomyCollector",
    "bbc_business": "app.collectors.rss_collector:BBCBusinessCollector",
}

COLLECTORS = _COLLECTOR_SPECS
_collector_cache: dict[str, Type[BaseCollector]] = {}


def get_collector_names() -> list[str]:
    """获取所有注册的采集器名称"""
    return list(_COLLECTOR_SPECS.keys())


def get_collector(name: str) -> Type[BaseCollector] | None:
    """根据名称获取采集器类"""
    cached = _collector_cache.get(name)
    if cached is not None:
        return cached

    spec = _COLLECTOR_SPECS.get(name)
    if not spec:
        return None

    module_path, _, attr_name = spec.rpartition(":")
    if not module_path or not attr_name:
        return None

    try:
        module = import_module(module_path)
        collector_cls = getattr(module, attr_name)
        if not isinstance(collector_cls, type) or not issubclass(collector_cls, BaseCollector):
            return None
    except Exception:
        return None

    _collector_cache[name] = collector_cls
    return collector_cls
