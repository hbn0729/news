from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from .chinese_synonym_engine import ChineseSynonymEngine
from .types import NewsText, SimilarityResult


@dataclass(frozen=True, slots=True)
class AdvancedDedupConfig:
    semantic_threshold: float = 0.80
    synonym_threshold: float = 0.75
    enable_synonyms: bool = True
    synonym_source: str = "multi"
    max_synonyms_per_word: int = 10
    max_tokens: int = 30


class AdvancedDeduplicator:
    def __init__(self, config: AdvancedDedupConfig, synonym_engine: ChineseSynonymEngine | None):
        self._config = config
        self._synonym_engine = synonym_engine if config.enable_synonyms else None

    def compare(self, current: NewsText, candidate: NewsText) -> SimilarityResult:
        current_text = self._combine_text(current)
        cand_text = self._combine_text(candidate)

        current_sem = self._extract_semantic_elements(current_text)
        cand_sem = self._extract_semantic_elements(cand_text)
        semantic_sim = self._calculate_semantic_similarity(current_sem, cand_sem)
        if semantic_sim >= self._config.semantic_threshold:
            return SimilarityResult(
                is_duplicate=True,
                method="semantic_fingerprint",
                similarity=semantic_sim,
                details="语义要素匹配",
            )

        if self._synonym_engine is None:
            return SimilarityResult(
                is_duplicate=False,
                method=None,
                similarity=semantic_sim,
                details="未发现重复",
            )

        syn_sim = self._calculate_synonym_enhanced_similarity(current_text, cand_text)
        if syn_sim >= self._config.synonym_threshold:
            return SimilarityResult(
                is_duplicate=True,
                method="synonym_enhanced",
                similarity=syn_sim,
                details="同义词增强匹配",
            )

        return SimilarityResult(
            is_duplicate=False,
            method=None,
            similarity=max(semantic_sim, syn_sim),
            details="未发现重复",
        )

    def is_duplicate_against_candidates(
        self,
        current: NewsText,
        candidates: Iterable[NewsText],
    ) -> SimilarityResult:
        best: SimilarityResult | None = None
        for candidate in candidates:
            result = self.compare(current, candidate)
            if result.is_duplicate:
                best = result
                break

        return best or SimilarityResult(
            is_duplicate=False,
            method=None,
            similarity=0.0,
            details="未发现重复",
        )

    def exact_fingerprint(self, text: str) -> str:
        normalized = self._normalize_text(text)
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()

    def semantic_fingerprint(self, text: str) -> str:
        elements = self._extract_semantic_elements(text)
        flattened: list[str] = []
        for category in ("companies", "actions", "numbers", "themes"):
            values = ",".join(elements.get(category, ()))
            flattened.append(f"{category}:{values}")
        return hashlib.md5("|".join(flattened).encode("utf-8")).hexdigest()

    def _combine_text(self, news: NewsText) -> str:
        parts = [news.title, news.summary, news.content]
        return " ".join(p for p in parts if p)

    def _extract_semantic_elements(self, text: str) -> dict[str, tuple[str, ...]]:
        elements: dict[str, list[str]] = {
            "companies": [],
            "actions": [],
            "numbers": [],
            "themes": [],
        }

        company_patterns = [
            "苹果公司",
            "Apple",
            "苹果",
            "谷歌公司",
            "Google",
            "谷歌",
            "微软公司",
            "Microsoft",
            "微软",
            "特斯拉",
            "Tesla",
            "亚马逊",
            "Amazon",
            "脸书",
            "Facebook",
            "Meta",
            "阿里巴巴",
            "腾讯",
            "百度",
            "华为",
            "小米",
            "OPPO",
            "vivo",
        ]
        for company in company_patterns:
            if company and company in text:
                elements["companies"].append(self._get_canonical_form(company, "company"))

        action_patterns = [
            "上涨",
            "涨",
            "攀升",
            "增长",
            "飙升",
            "走高",
            "下跌",
            "跌",
            "下滑",
            "暴跌",
            "下降",
            "走低",
            "发布",
            "公布",
            "宣布",
            "推出",
            "发表",
            "收购",
            "并购",
            "投资",
            "融资",
            "突破",
            "刷新",
            "创下",
            "缩量",
            "放量",
        ]
        for action in action_patterns:
            if action and action in text:
                elements["actions"].append(self._get_canonical_form(action, "action"))

        numbers = re.findall(r"(\d+(?:\.\d+)?)[%％]?", text)
        if numbers:
            elements["numbers"] = list(dict.fromkeys(numbers).keys())

        theme_patterns = [
            "股价",
            "股票",
            "股值",
            "市值",
            "市场价值",
            "营收",
            "营业收入",
            "收入",
            "销售额",
            "利润",
            "净利润",
            "产品",
            "服务",
            "技术",
            "成交额",
            "成交量",
        ]
        for theme in theme_patterns:
            if theme and theme in text:
                elements["themes"].append(self._get_canonical_form(theme, "theme"))

        normalized: dict[str, tuple[str, ...]] = {}
        for key, values in elements.items():
            deduped_sorted = tuple(sorted(set(values)))
            normalized[key] = deduped_sorted
        return normalized

    def _get_canonical_form(self, word: str, category: str) -> str:
        if self._synonym_engine is None:
            return word

        canonical_words: dict[str, dict[str, list[str]]] = {
            "company": {
                "苹果": ["Apple", "苹果公司"],
                "谷歌": ["Google", "谷歌公司"],
                "微软": ["Microsoft", "微软公司"],
            },
            "action": {
                "上涨": ["涨", "攀升", "增长", "飙升", "走高"],
                "下跌": ["跌", "下滑", "暴跌", "下降", "走低"],
                "发布": ["公布", "宣布", "推出", "发表"],
                "突破": ["刷新", "创下"],
            },
            "theme": {
                "股价": ["股票", "股值"],
                "营收": ["营业收入", "收入", "销售额"],
                "市值": ["市场价值", "总市值"],
                "成交额": ["成交量"],
            },
        }
        group = canonical_words.get(category, {})
        for canonical, synonyms in group.items():
            if word == canonical or word in synonyms:
                return canonical
            if self._synonym_engine.are_synonyms(word, canonical, self._config.synonym_source):
                return canonical
        return word

    def _calculate_semantic_similarity(
        self, elements1: dict[str, tuple[str, ...]], elements2: dict[str, tuple[str, ...]]
    ) -> float:
        weights = {
            "companies": 0.4,
            "actions": 0.3,
            "numbers": 0.2,
            "themes": 0.1,
        }

        total_score = 0.0
        total_weight = 0.0
        for category, weight in weights.items():
            list1 = elements1.get(category, ())
            list2 = elements2.get(category, ())
            if list1 and list2:
                set1 = set(list1)
                set2 = set(list2)
                # Use Dice Coefficient: 2 * |A & B| / (|A| + |B|)
                # This is more forgiving for subset matches than Jaccard
                intersection = len(set1 & set2)
                total_len = len(set1) + len(set2)
                score = (2.0 * intersection) / total_len if total_len > 0 else 0.0
                
                total_score += score * weight
                total_weight += weight
            elif list1 or list2:
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    @lru_cache(maxsize=5_000)
    def _calculate_synonym_enhanced_similarity(self, text1: str, text2: str) -> float:
        if self._synonym_engine is None:
            return self._calculate_basic_similarity(text1, text2)

        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0

        similarities = {
            "exact": self._calculate_exact_similarity(tokens1, tokens2),
            "synonym": self._calculate_synonym_similarity(tokens1, tokens2),
            "semantic": self._calculate_semantic_similarity(
                self._extract_semantic_elements(text1), self._extract_semantic_elements(text2)
            ),
            "numeric": self._calculate_numeric_similarity(text1, text2),
            "structure": self._calculate_structural_similarity(text1, text2),
        }
        weights = {
            "exact": 0.3,
            "synonym": 0.4,
            "semantic": 0.15,
            "numeric": 0.1,
            "structure": 0.05,
        }
        return sum(similarities[k] * weights[k] for k in weights)

    def _calculate_synonym_similarity(self, tokens1: tuple[str, ...], tokens2: tuple[str, ...]) -> float:
        if self._synonym_engine is None:
            return 0.0
        
        def _one_way_similarity(t_source: tuple[str, ...], t_target: tuple[str, ...]) -> float:
            total_matches = 0.0
            for t1 in t_source:
                best = 0.0
                for t2 in t_target:
                    if t1 == t2:
                        score = 1.0
                    else:
                        score = self._synonym_engine.get_similarity_score(
                            t1, t2, self._config.synonym_source
                        )
                    if score > best:
                        best = score
                        if best >= 1.0:
                            break
                total_matches += best
            return total_matches / len(t_source) if t_source else 0.0

        sim1 = _one_way_similarity(tokens1, tokens2)
        sim2 = _one_way_similarity(tokens2, tokens1)
        return max(sim1, sim2)

    def _calculate_exact_similarity(self, tokens1: tuple[str, ...], tokens2: tuple[str, ...]) -> float:
        set1 = set(tokens1)
        set2 = set(tokens2)
        union = set1 | set2
        return len(set1 & set2) / len(union) if union else 0.0

    def _calculate_numeric_similarity(self, text1: str, text2: str) -> float:
        nums1 = set(re.findall(r"(\d+(?:\.\d+)?)[%％]?", text1))
        nums2 = set(re.findall(r"(\d+(?:\.\d+)?)[%％]?", text2))
        if not nums1 and not nums2:
            return 1.0
        if not nums1 or not nums2:
            return 0.0
        union = nums1 | nums2
        return len(nums1 & nums2) / len(union) if union else 0.0

    def _calculate_structural_similarity(self, text1: str, text2: str) -> float:
        len1 = len(text1)
        len2 = len(text2)
        if len1 == 0 and len2 == 0:
            return 1.0
        max_len = max(len1, len2)
        if max_len == 0:
            return 0.0
        return 1.0 - (abs(len1 - len2) / max_len)

    def _calculate_basic_similarity(self, text1: str, text2: str) -> float:
        tokens1 = self._tokenize(text1)
        tokens2 = self._tokenize(text2)
        if not tokens1 or not tokens2:
            return 0.0
        return self._calculate_exact_similarity(tokens1, tokens2)

    def _tokenize(self, text: str) -> tuple[str, ...]:
        normalized = self._normalize_text(text)
        tokens: list[str] = []
        max_total = self._config.max_tokens

        semantic = self._extract_semantic_elements(normalized)
        semantic_tokens: set[str] = set()
        for category in ("companies", "actions", "themes", "numbers"):
            semantic_tokens.update(semantic.get(category, ()))

        for t in semantic_tokens:
            tokens.append(t)
            if len(tokens) >= max_total:
                break

        if len(tokens) < max_total:
            for alnum in re.findall(r"[a-z0-9]{2,}", normalized):
                tokens.append(alnum)
                if len(tokens) >= max_total:
                    break

        for seq in re.findall(r"[\u4e00-\u9fff]+", normalized):
            if len(tokens) >= max_total:
                break

            if len(seq) <= 6:
                if seq in semantic_tokens or (
                    self._synonym_engine is not None and self._synonym_engine.has_word(seq)
                ):
                    tokens.append(seq)
                continue

            for n in (4, 3, 2):
                if len(tokens) >= max_total:
                    break
                for i in range(0, len(seq) - n + 1):
                    token = seq[i : i + n]
                    if token in semantic_tokens or (
                        self._synonym_engine is not None
                        and self._synonym_engine.has_word(token)
                    ):
                        tokens.append(token)
                    if len(tokens) >= max_total:
                        break

            for n in (4, 3, 2):
                if len(tokens) >= max_total:
                    break
                if len(seq) >= n:
                    tokens.append(seq[-n:])

        stopwords = {"的", "了", "在", "是", "和", "与", "或", "等", "今天", "昨天", "明天"}
        filtered: list[str] = []
        seen: set[str] = set()
        for t in tokens:
            if not t or t in stopwords or len(t) < 2:
                continue
            if t in seen:
                continue
            seen.add(t)
            filtered.append(t)
            if len(filtered) >= self._config.max_tokens:
                break
        return tuple(filtered)

    def _normalize_text(self, text: str) -> str:
        text = (text or "").lower()
        text = re.sub(r"\s+", " ", text).strip()
        text = text.replace("，", ",").replace("。", ".").replace("？", "?").replace("！", "!")
        text = text.replace("；", ";").replace("：", ":")
        return text
