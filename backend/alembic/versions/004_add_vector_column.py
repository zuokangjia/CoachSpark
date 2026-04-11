"""add vector column to profile_evidence

Revision ID: 004_add_vector_column
Revises: 003_add_persona_v2_tables
Create Date: 2026-04-12

为 ProfileEvidence 表新增 vector 列，为 PostgreSQL+pgvector 迁移做准备。
当前 SQLite 环境下存 JSON 列表，pgvector 环境下可直接利用列存储和向量索引。
"""

from alembic import op
import sqlalchemy as sa


revision = "004_add_vector_column"
down_revision = "003_add_persona_v2_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profile_evidence",
        sa.Column("vector", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("profile_evidence", "vector")
