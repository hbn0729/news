from datetime import datetime

from sqlalchemy import Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CleanupLog(Base):
    __tablename__ = "cleanup_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    cutoff_utc: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False)
    deleted_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_cleanup_started_at", "started_at", postgresql_using="btree"),
    )
