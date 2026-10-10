"""C1 FounderHandoff: users, rooms, strategy_snapshots

Revision ID: 001_c1_founder_handoff
Revises:
Create Date: 2026-10-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_c1_founder_handoff"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("sub", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("sub"),
    )
    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("founder_sub", sa.String(length=255), nullable=False),
        sa.Column("handoff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "staffing_unlocked",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["founder_sub"], ["users.sub"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("handoff_id"),
    )
    op.create_index("ix_rooms_founder_sub", "rooms", ["founder_sub"])
    op.create_index("ix_rooms_handoff_id", "rooms", ["handoff_id"], unique=True)

    op.create_table(
        "strategy_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy_version", sa.String(length=128), nullable=False),
        sa.Column("strategy_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("documents", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("staffing_intent", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("commercial", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id"),
    )


def downgrade() -> None:
    op.drop_table("strategy_snapshots")
    op.drop_index("ix_rooms_handoff_id", table_name="rooms")
    op.drop_index("ix_rooms_founder_sub", table_name="rooms")
    op.drop_table("rooms")
    op.drop_table("users")
