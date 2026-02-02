"""
Collector Registry - 采集器注册表

职责：
- 集中管理所有可用的采集器
- 便于添加/移除采集器

设计原则：
- 开闭原则：添加新采集器只需在此注册
"""

from typing import Type

from app.collectors.base import BaseCollector
from app.collectors.akshare_collector import (
    AkShareEastmoneyCollector,
    AkShareCLSCollector,
    ITJuziCollector,
)
from app.collectors.realtime_collector import (
    Jin10Collector,
    WallstreetCollector,
)
from app.collectors.rss_collector import (
    Kr36Collector,
    WSJBusinessCollector,
    WSJMarketsCollector,
    MarketWatchCollector,
    ZeroHedgeCollector,
    ETFTrendsCollector,
    WSJSocialEconomyCollector,
    BBCBusinessCollector,
)


# Registry of available collectors
COLLECTORS: dict[str, Type[BaseCollector]] = {
    # AkShare 数据源
    "eastmoney": AkShareEastmoneyCollector,
    "cls": AkShareCLSCollector,
    # 创投数据源
    "itjuzi": ITJuziCollector,
    # 实时快讯数据源
    "jin10": Jin10Collector,
    "wallstreet": WallstreetCollector,
    # RSS数据源 - 国内
    "36kr": Kr36Collector,
    # RSS数据源 - 美股
    "wsj_business": WSJBusinessCollector,
    "wsj_markets": WSJMarketsCollector,
    "marketwatch": MarketWatchCollector,
    "zerohedge": ZeroHedgeCollector,
    "etf_trends": ETFTrendsCollector,
    # RSS数据源 - 国际
    "wsj_social": WSJSocialEconomyCollector,
    "bbc_business": BBCBusinessCollector,
}


def get_collector_names() -> list[str]:
    """获取所有注册的采集器名称"""
    return list(COLLECTORS.keys())


def get_collector(name: str) -> Type[BaseCollector] | None:
    """根据名称获取采集器类"""
    return COLLECTORS.get(name)
