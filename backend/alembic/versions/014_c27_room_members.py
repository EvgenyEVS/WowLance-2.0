"""C27 room membership roles

Revision ID: 014_c27_room_members
Revises: 013_merge_c19_c20_heads
Create Date: 2026-10-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "014_c27_room_members"
down_revision: Union[str, Sequence[str], None] = "013_merge_c19_c20_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "room_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_sub", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "user_sub", name="uq_room_members_room_user"),
    )
    op.create_index("ix_room_members_room_id", "room_members", ["room_id"])


def downgrade() -> None:
    op.drop_index("ix_room_members_room_id", table_name="room_members")
    op.drop_table("room_members")
