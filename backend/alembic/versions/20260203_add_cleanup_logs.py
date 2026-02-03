"""add cleanup logs

Revision ID: 20260203_add_cleanup_logs
Revises: 
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260203_add_cleanup_logs"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cleanup_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cutoff_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("retention_days", sa.Integer(), nullable=False),
        sa.Column("deleted_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_cleanup_started_at", "cleanup_logs", ["started_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_cleanup_started_at", table_name="cleanup_logs")
    op.drop_table("cleanup_logs")
