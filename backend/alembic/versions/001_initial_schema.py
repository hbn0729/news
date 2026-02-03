"""initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP


revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create news_articles table
    op.create_table(
        "news_articles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("summary", sa.String(length=1000), nullable=True),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("source_category", sa.String(length=50), nullable=True),
        sa.Column("published_at", TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "collected_at",
            TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("similarity_group_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "is_starred", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "is_filtered", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "created_at",
            TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # Create unique constraints
    op.create_unique_constraint("uq_news_articles_url", "news_articles", ["url"])
    op.create_unique_constraint(
        "uq_news_articles_content_hash", "news_articles", ["content_hash"]
    )

    # Create indexes for news_articles
    op.create_index(
        "idx_news_published_at",
        "news_articles",
        ["published_at"],
        postgresql_using="btree",
    )
    op.create_index("idx_news_source", "news_articles", ["source"])
    op.create_index("idx_news_content_hash", "news_articles", ["content_hash"])

    # Create collection_logs table
    op.create_table(
        "collection_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("started_at", TIMESTAMP(timezone=True), nullable=False),
        sa.Column("finished_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("articles_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("articles_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "articles_duplicate", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("last_article_time", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("checkpoint", JSONB, nullable=True),
    )

    # Create cleanup_logs table
    op.create_table(
        "cleanup_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("started_at", TIMESTAMP(timezone=True), nullable=False),
        sa.Column("finished_at", TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cutoff_utc", TIMESTAMP(timezone=True), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("deleted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # Create index for cleanup_logs
    op.create_index(
        "idx_cleanup_started_at",
        "cleanup_logs",
        ["started_at"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    # Drop cleanup_logs
    op.drop_index("idx_cleanup_started_at", table_name="cleanup_logs")
    op.drop_table("cleanup_logs")

    # Drop collection_logs
    op.drop_table("collection_logs")

    # Drop news_articles
    op.drop_index("idx_news_content_hash", table_name="news_articles")
    op.drop_index("idx_news_source", table_name="news_articles")
    op.drop_index("idx_news_published_at", table_name="news_articles")
    op.drop_constraint("uq_news_articles_content_hash", "news_articles", type_="unique")
    op.drop_constraint("uq_news_articles_url", "news_articles", type_="unique")
    op.drop_table("news_articles")
