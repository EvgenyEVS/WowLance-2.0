"""C4 Staffing slots: room_function_slots

Revision ID: 003_c4_room_function_slots
Revises: 002_c2_entitlements
Create Date: 2026-10-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_c4_room_function_slots"
down_revision: Union[str, Sequence[str], None] = "002_c2_entitlements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "room_function_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_key", sa.String(length=64), nullable=False),
        sa.Column("seat_index", sa.Integer(), nullable=False),
        sa.Column("level_min", sa.String(length=32), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="open",
            nullable=False,
        ),
        sa.Column("freelancer_sub", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "room_id",
            "role_key",
            "seat_index",
            name="uq_room_function_slot_seat",
        ),
    )
    op.create_index(
        "ix_room_function_slots_room_id",
        "room_function_slots",
        ["room_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_room_function_slots_room_id", table_name="room_function_slots")
    op.drop_table("room_function_slots")
