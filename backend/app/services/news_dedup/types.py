from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NewsText:
    title: str
    content: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    is_duplicate: bool
    method: str | None
    similarity: float
    details: str

