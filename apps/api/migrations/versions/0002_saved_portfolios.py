"""Add immutable synthetic portfolio snapshots without changing seed facilities."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "saved_portfolios",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("csv_text", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(32), nullable=False),
        sa.UniqueConstraint("digest", name="uq_saved_portfolios_digest"),
        sa.CheckConstraint("row_count >= 1 AND row_count <= 1000", name="valid_row_count"),
    )


def downgrade():
    op.drop_table("saved_portfolios")
