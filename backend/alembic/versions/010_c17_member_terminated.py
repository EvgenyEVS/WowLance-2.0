"""C17 member termination: room_terminations journal table

Revision ID: 010_c17_member_terminated
Revises: 009_c14_meet_jitsi
Create Date: 2026-10-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_c17_member_terminated"
down_revision: Union[str, Sequence[str], None] = "009_c14_meet_jitsi"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "room_terminations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "room_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("freelancer_sub", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "terminated_by_sub",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "slot_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_room_terminations_room_id",
        "room_terminations",
        ["room_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_room_terminations_room_id", table_name="room_terminations")
    op.drop_table("room_terminations")
