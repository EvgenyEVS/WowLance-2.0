"""C20 room chat: room_messages table

Revision ID: 012_c20_room_messages
Revises: 011_merge_c16_c17_heads
Create Date: 2026-10-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_c20_room_messages"
down_revision: Union[str, Sequence[str], None] = "011_merge_c16_c17_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "room_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_sub", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_room_messages_room_created_at",
        "room_messages",
        ["room_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_room_messages_room_created_at", table_name="room_messages")
    op.drop_table("room_messages")
