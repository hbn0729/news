from .advanced_deduplicator import AdvancedDeduplicator
from .chinese_synonym_engine import ChineseSynonymEngine, get_chinese_synonym_engine
from .types import NewsText, SimilarityResult

__all__ = [
    "AdvancedDeduplicator",
    "ChineseSynonymEngine",
    "get_chinese_synonym_engine",
    "NewsText",
    "SimilarityResult",
]

