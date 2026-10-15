"""C5 strategy proposals + snapshot history (active/superseded)

Revision ID: 003_c5_strategy_proposals
Revises: 002_c2_entitlements
Create Date: 2026-10-15

Parallel to C4's 003 if both land: merge alembic heads then.

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_c5_strategy_proposals"
down_revision: Union[str, Sequence[str], None] = "002_c2_entitlements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "strategy_snapshots",
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="active",
            nullable=False,
        ),
    )
    op.execute("UPDATE strategy_snapshots SET status = 'active' WHERE status IS NULL")
    op.drop_constraint("strategy_snapshots_room_id_key", "strategy_snapshots", type_="unique")
    op.create_index("ix_strategy_snapshots_room_id", "strategy_snapshots", ["room_id"])
    op.create_index(
        "uq_strategy_snapshots_one_active",
        "strategy_snapshots",
        ["room_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "strategy_proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("publication_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_version", sa.String(length=128), nullable=False),
        sa.Column("strategy_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("staffing_intent", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_sub", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("publication_id"),
    )
    op.create_index("ix_strategy_proposals_room_id", "strategy_proposals", ["room_id"])
    op.create_index(
        "uq_strategy_proposals_one_pending",
        "strategy_proposals",
        ["room_id"],
        unique=True,
        postgresql_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    op.drop_index("uq_strategy_proposals_one_pending", table_name="strategy_proposals")
    op.drop_index("ix_strategy_proposals_room_id", table_name="strategy_proposals")
    op.drop_table("strategy_proposals")
    op.drop_index("uq_strategy_snapshots_one_active", table_name="strategy_snapshots")
    op.drop_index("ix_strategy_snapshots_room_id", table_name="strategy_snapshots")
    op.create_unique_constraint(
        "strategy_snapshots_room_id_key", "strategy_snapshots", ["room_id"]
    )
    op.drop_column("strategy_snapshots", "status")
