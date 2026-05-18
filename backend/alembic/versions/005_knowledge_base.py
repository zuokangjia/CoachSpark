"""knowledge base tables: KnowledgeDocument and KnowledgeChunk

Revision ID: 005_knowledge_base
Revises: 004_add_vector_column
Create Date: 2026-05-12

知识库表：KnowledgeDocument（文档元数据）和 KnowledgeChunk（文档分块 + 向量）
"""

from alembic import op
import sqlalchemy as sa


revision = "005_knowledge_base"
down_revision = "004_add_vector_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # KnowledgeDocument
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False, server_default="default-user"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="未分类"),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="markdown"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("ix_knowledge_documents_user", "user_id"),
        sa.Index("ix_knowledge_documents_category", "category"),
    )

    # KnowledgeChunk
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("parent_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("concepts", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("vector", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["knowledge_chunks.id"]),
        sa.Index("ix_knowledge_chunks_document", "document_id"),
        sa.Index("ix_knowledge_chunks_parent", "parent_id"),
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")