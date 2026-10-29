"""Preserve legacy snapshots while introducing workspace-scoped deduplication."""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("saved_portfolios") as batch:
        batch.add_column(sa.Column("workspace_id", sa.String(36), nullable=False,
                                   server_default="local"))
        batch.drop_constraint("uq_saved_portfolios_digest", type_="unique")
        batch.create_unique_constraint("uq_saved_workspace_digest", ["workspace_id", "digest"])


def downgrade():
    # Collapsing private workspaces into the legacy shared catalog would disclose data.
    count = op.get_bind().scalar(sa.text(
        "SELECT COUNT(*) FROM saved_portfolios WHERE workspace_id <> 'local'"
    ))
    if count:
        raise RuntimeError("Cannot downgrade while private workspace snapshots exist")
    with op.batch_alter_table("saved_portfolios") as batch:
        batch.drop_constraint("uq_saved_workspace_digest", type_="unique")
        batch.drop_column("workspace_id")
        batch.create_unique_constraint("uq_saved_portfolios_digest", ["digest"])
