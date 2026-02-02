"""Initial migration

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # Create news_articles table
    op.create_table(
        'news_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('summary', sa.String(1000), nullable=True),
        sa.Column('url', sa.String(2000), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('source_category', sa.String(50), nullable=True),
        sa.Column('published_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('collected_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('similarity_group_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ai_quality_score', sa.Float(), nullable=True),
        sa.Column('ai_category', sa.String(50), nullable=True),
        sa.Column('ai_keywords', postgresql.JSONB(), nullable=True),
        sa.Column('ai_processed', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('is_starred', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('is_filtered', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.UniqueConstraint('content_hash'),
    )

    # Create indexes
    op.create_index('idx_news_published_at', 'news_articles', ['published_at'])
    op.create_index('idx_news_source', 'news_articles', ['source'])
    op.create_index('idx_news_content_hash', 'news_articles', ['content_hash'])
    op.create_index(
        'idx_news_ai_score',
        'news_articles',
        ['ai_quality_score'],
        postgresql_where=sa.text("NOT is_filtered")
    )

    # Create collection_logs table
    op.create_table(
        'collection_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('articles_fetched', sa.Integer(), server_default=sa.text("0")),
        sa.Column('articles_new', sa.Integer(), server_default=sa.text("0")),
        sa.Column('articles_duplicate', sa.Integer(), server_default=sa.text("0")),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('last_article_time', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('checkpoint', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('collection_logs')
    op.drop_index('idx_news_ai_score', 'news_articles')
    op.drop_index('idx_news_content_hash', 'news_articles')
    op.drop_index('idx_news_source', 'news_articles')
    op.drop_index('idx_news_published_at', 'news_articles')
    op.drop_table('news_articles')
