"""add resume table

Revision ID: 002_add_resume_table
Revises: 001_migrate_closed_to_rejected
Create Date: 2026-04-04

"""

from alembic import op
import sqlalchemy as sa


revision = "002_add_resume_table"
down_revision = "001_migrate_closed_to_rejected"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resume",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(100), nullable=True, server_default=""),
        sa.Column("phone", sa.String(50), nullable=True, server_default=""),
        sa.Column("email", sa.String(255), nullable=True, server_default=""),
        sa.Column("summary", sa.Text, nullable=True, server_default=""),
        sa.Column("skills", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("education", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("work_experience", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("projects", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("certifications", sa.JSON, nullable=False, server_default="[]"),
        sa.Column(
            "updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("resume")
