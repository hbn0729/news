from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class NewsArticleBase(BaseModel):
    title: str = Field(..., max_length=500)
    content: str | None = None
    summary: str | None = Field(None, max_length=1000)
    url: str = Field(..., max_length=2000)
    source: str = Field(..., max_length=100)
    source_category: str | None = Field(None, max_length=50)
    published_at: datetime


class NewsArticleCreate(NewsArticleBase):
    content_hash: str = Field(..., max_length=64)


class NewsArticleUpdate(BaseModel):
    is_read: bool | None = None
    is_starred: bool | None = None


class NewsArticleResponse(NewsArticleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collected_at: datetime
    content_hash: str
    similarity_group_id: UUID | None = None
    is_read: bool = False
    is_starred: bool = False
    is_filtered: bool = False
    created_at: datetime


class PaginatedNews(BaseModel):
    items: list[NewsArticleResponse]
    total: int
    page: int
    per_page: int
    pages: int


class CollectionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    started_at: datetime
    finished_at: datetime | None
    status: str | None
    articles_fetched: int
    articles_new: int
    articles_duplicate: int
    error_message: str | None
