"""Initial synthetic facility schema."""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "facilities",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("borrower", sa.String(100), nullable=False),
        sa.Column("industry", sa.String(50), nullable=False),
        sa.Column("geography", sa.String(50), nullable=False),
        sa.Column("rating", sa.String(8), nullable=False),
        sa.Column("pd", sa.Numeric(12, 10), nullable=False),
        sa.Column("lgd", sa.Numeric(12, 10), nullable=False),
        sa.Column("ead", sa.Numeric(20, 2), nullable=False),
        sa.CheckConstraint("pd >= 0 AND pd <= 1", name="valid_pd"),
        sa.CheckConstraint("lgd >= 0 AND lgd <= 1", name="valid_lgd"),
        sa.CheckConstraint("ead >= 0", name="valid_ead"),
    )
    op.create_index("ix_facilities_industry", "facilities", ["industry"])


def downgrade():
    op.drop_table("facilities")
