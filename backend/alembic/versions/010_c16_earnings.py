"""C16 earnings: earnings_entries ledger table

Revision ID: 010_c16_earnings
Revises: 009_c14_meet_jitsi
Create Date: 2026-10-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_c16_earnings"
down_revision: Union[str, Sequence[str], None] = "009_c14_meet_jitsi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "earnings_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("freelancer_sub", sa.String(length=255), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(length=8),
            nullable=False,
            server_default="USD",
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="task_accepted",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["room_id"], ["rooms.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["room_tasks.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", name="uq_earnings_entries_task_id"),
    )
    op.create_index(
        "ix_earnings_entries_room_id", "earnings_entries", ["room_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_earnings_entries_room_id", table_name="earnings_entries")
    op.drop_table("earnings_entries")
