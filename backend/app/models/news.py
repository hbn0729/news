import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Boolean, Float, Integer, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Content fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    url: Mapped[str] = mapped_column(String(2000), unique=True, nullable=False)

    # Source information
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    source_category: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Time handling (UTC)
    published_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    collected_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        default=lambda: datetime.now(timezone.utc),
    )

    # Deduplication
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    similarity_group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Status
    is_read: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), default=False
    )
    is_starred: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), default=False
    )
    is_filtered: Mapped[bool] = mapped_column(
        Boolean, server_default=text("false"), default=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("NOW()"),
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_news_published_at", "published_at", postgresql_using="btree"),
        Index("idx_news_source", "source"),
        Index("idx_news_content_hash", "content_hash"),
    )


class CollectionLog(Base):
    __tablename__ = "collection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    articles_fetched: Mapped[int] = mapped_column(Integer, default=0)
    articles_new: Mapped[int] = mapped_column(Integer, default=0)
    articles_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_article_time: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    checkpoint: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
