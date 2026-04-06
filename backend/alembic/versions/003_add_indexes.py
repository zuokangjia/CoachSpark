"""add indexes on company_id and status for common query patterns

Revision ID: 003_add_indexes
Revises: 002_add_resume_table
Create Date: 2026-04-06

"""

from alembic import op

revision = "003_add_indexes"
down_revision = "002_add_resume_table"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("ix_interviews_company_id", "interviews", ["company_id"])
    op.create_index("ix_prep_plans_company_id", "prep_plans", ["company_id"])
    op.create_index("ix_offers_company_id", "offers", ["company_id"])
    op.create_index("ix_companies_status", "companies", ["status"])
    op.create_index(
        "ix_interviews_interview_date", "interviews", ["interview_date"]
    )


def downgrade():
    op.drop_index("ix_interviews_interview_date", table_name="interviews")
    op.drop_index("ix_companies_status", table_name="companies")
    op.drop_index("ix_offers_company_id", table_name="offers")
    op.drop_index("ix_prep_plans_company_id", table_name="prep_plans")
    op.drop_index("ix_interviews_company_id", table_name="interviews")
