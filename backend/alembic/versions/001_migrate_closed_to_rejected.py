"""migrate closed status to rejected

Revision ID: 001_migrate_closed_to_rejected
Revises:
Create Date: 2026-04-04

"""

from alembic import op


# revision identifiers
revision = "001_migrate_closed_to_rejected"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE companies SET status = 'rejected' WHERE status = 'closed'")


def downgrade():
    op.execute("UPDATE companies SET status = 'closed' WHERE status = 'rejected'")
