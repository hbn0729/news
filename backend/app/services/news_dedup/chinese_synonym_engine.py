from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


class ChineseSynonymEngine:
    def __init__(self, data_dir: Path, preferred_source: str = "multi"):
        self._data_dir = data_dir
        self._preferred_source = preferred_source
        self._synonyms_basic: dict[str, list[str]] = {}
        self._synonyms_narrow: dict[str, list[str]] = {}
        self._synonyms_broad: dict[str, list[str]] = {}
        self._load_data()

    def _load_data(self) -> None:
        files = {
            "basic": self._data_dir / "synonyms.json",
            "narrow": self._data_dir / "synonyms_expanded_narrow.json",
            "broad": self._data_dir / "synonyms_expanded_broad.json",
        }
        for kind, path in files.items():
            if not path.exists():
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            normalized: dict[str, list[str]] = {}
            for k, v in data.items():
                if not isinstance(k, str) or not isinstance(v, list):
                    continue
                values = [s for s in v if isinstance(s, str) and s]
                if values:
                    normalized[k] = values
            if kind == "basic":
                self._synonyms_basic = normalized
            elif kind == "narrow":
                self._synonyms_narrow = normalized
            elif kind == "broad":
                self._synonyms_broad = normalized

        if not (self._synonyms_basic or self._synonyms_narrow or self._synonyms_broad):
            self._init_builtin_dict()

    def _init_builtin_dict(self) -> None:
        self._synonyms_basic = {
            "苹果": ["Apple", "苹果公司"],
            "Apple": ["苹果", "苹果公司"],
            "谷歌": ["Google", "谷歌公司"],
            "Google": ["谷歌", "谷歌公司"],
            "微软": ["Microsoft", "微软公司"],
            "Microsoft": ["微软", "微软公司"],
            "上涨": ["涨", "上升", "攀升", "增长", "飙升", "走高"],
            "涨": ["上涨", "上升", "攀升", "增长", "走高"],
            "走高": ["上涨", "上升", "攀升", "增长", "飙升"],
            "下跌": ["跌", "下降", "下滑", "暴跌", "走低"],
            "跌": ["下跌", "下降", "下滑", "走低"],
            "走低": ["下跌", "下降", "下滑", "暴跌"],
            "发布": ["公布", "宣布", "推出", "发表"],
            "公布": ["发布", "宣布", "推出"],
            "股价": ["股票价格", "股值"],
            "市值": ["市场价值", "总市值"],
            "营收": ["营业收入", "收入", "销售额"],
        }

    def set_preferred_source(self, source: str) -> None:
        if source in {"basic", "narrow", "broad", "multi"}:
            self._preferred_source = source

    def has_word(self, word: str) -> bool:
        if not word:
            return False
        return (
            word in self._synonyms_basic
            or word in self._synonyms_narrow
            or word in self._synonyms_broad
        )

    @lru_cache(maxsize=50_000)
    def get_synonyms(
        self, word: str, limit: int = 10, source: str | None = None
    ) -> tuple[str, ...]:
        source = source or self._preferred_source
        if not word:
            return ()

        synonyms: list[str] = []
        if source == "basic":
            synonyms = self._synonyms_basic.get(word, [])
        elif source == "narrow":
            synonyms = self._synonyms_narrow.get(word, []) or self._synonyms_basic.get(
                word, []
            )
        elif source == "broad":
            synonyms = (
                self._synonyms_broad.get(word, [])
                or self._synonyms_narrow.get(word, [])
                or self._synonyms_basic.get(word, [])
            )
        elif source == "multi":
            synonyms = list(self._get_multi_source_synonyms(word))

        filtered: list[str] = []
        seen: set[str] = set()
        for s in synonyms:
            if not s or s == word or s in seen:
                continue
            seen.add(s)
            filtered.append(s)
            if len(filtered) >= limit:
                break

        return tuple(filtered)

    def _get_multi_source_synonyms(self, word: str) -> tuple[str, ...]:
        weights: dict[str, int] = {}
        for syn in self._synonyms_basic.get(word, []):
            weights[syn] = weights.get(syn, 0) + 3
        for syn in self._synonyms_narrow.get(word, []):
            weights[syn] = weights.get(syn, 0) + 2
        for syn in self._synonyms_broad.get(word, []):
            if 2 <= len(syn) <= 6:
                weights[syn] = weights.get(syn, 0) + 1

        if not weights:
            return ()

        sorted_synonyms = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
        return tuple(s for s, _ in sorted_synonyms)

    def are_synonyms(self, word1: str, word2: str, source: str | None = None) -> bool:
        if not word1 or not word2:
            return False
        if word1 == word2:
            return True
        syn1 = self.get_synonyms(word1, 50, source)
        if word2 in syn1:
            return True
        syn2 = self.get_synonyms(word2, 50, source)
        return word1 in syn2

    def get_similarity_score(
        self, word1: str, word2: str, source: str | None = None
    ) -> float:
        if not word1 or not word2:
            return 0.0
        if word1 == word2:
            return 1.0

        source = source or self._preferred_source
        if source == "multi":
            return self._get_multi_source_similarity(word1, word2)

        syn1 = set(self.get_synonyms(word1, 50, source))
        syn2 = set(self.get_synonyms(word2, 50, source))
        if word2 in syn1 or word1 in syn2:
            return 0.9
        if syn1 and syn2:
            common = syn1 & syn2
            if common:
                union = syn1 | syn2
                return len(common) / len(union) if union else 0.0
        return 0.0

    def _get_multi_source_similarity(self, word1: str, word2: str) -> float:
        weighted: list[float] = []
        for source in ("basic", "narrow", "broad"):
            score = self.get_similarity_score(word1, word2, source)
            if score <= 0:
                continue
            weight = 3 if source == "basic" else (2 if source == "narrow" else 1)
            weighted.append(score * weight)
        if not weighted:
            return 0.0
        return sum(weighted) / len(weighted) / 3


@lru_cache(maxsize=8)
def get_chinese_synonym_engine(data_dir: str, preferred_source: str = "multi") -> ChineseSynonymEngine:
    return ChineseSynonymEngine(Path(data_dir), preferred_source=preferred_source)
