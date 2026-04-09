"""add persona v2 tables

Revision ID: 003_add_persona_v2_tables
Revises: 002_add_resume_table
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa


revision = "003_add_persona_v2_tables"
down_revision = "002_add_resume_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skill_taxonomy",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("external_refs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_name"),
    )

    op.create_table(
        "profile_evidence",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("dimension", sa.String(length=100), nullable=False),
        sa.Column("skill_name", sa.String(length=255), nullable=True),
        sa.Column("signal_type", sa.String(length=50), nullable=False),
        sa.Column("polarity", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("round_no", sa.Integer(), nullable=True),
        sa.Column("quote_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("event_time", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_evidence_user_event",
        "profile_evidence",
        ["user_id", "event_time"],
        unique=False,
    )
    op.create_index(
        "ix_profile_evidence_user_dimension",
        "profile_evidence",
        ["user_id", "dimension"],
        unique=False,
    )

    op.create_table(
        "user_skill_state",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("dimension", sa.String(length=100), nullable=False),
        sa.Column("skill_name", sa.String(length=255), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("trend", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("evidence_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_skill_state_user",
        "user_skill_state",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_skill_state_user_dimension",
        "user_skill_state",
        ["user_id", "dimension"],
        unique=False,
    )

    op.create_table(
        "user_profile_snapshot",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("summary", sa.JSON(), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("source_event_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_profile_snapshot_user_time",
        "user_profile_snapshot",
        ["user_id", "generated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_profile_snapshot_user_time", table_name="user_profile_snapshot")
    op.drop_table("user_profile_snapshot")

    op.drop_index("ix_user_skill_state_user_dimension", table_name="user_skill_state")
    op.drop_index("ix_user_skill_state_user", table_name="user_skill_state")
    op.drop_table("user_skill_state")

    op.drop_index("ix_profile_evidence_user_dimension", table_name="profile_evidence")
    op.drop_index("ix_profile_evidence_user_event", table_name="profile_evidence")
    op.drop_table("profile_evidence")

    op.drop_table("skill_taxonomy")
