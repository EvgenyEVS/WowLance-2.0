"""C2 EntitlementGranted: entitlements table

Revision ID: 002_c2_entitlements
Revises: 001_c1_founder_handoff
Create Date: 2026-10-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_c2_entitlements"
down_revision: Union[str, Sequence[str], None] = "001_c1_founder_handoff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entitlements",
        sa.Column("entitlement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("entitlement_id"),
    )
    op.create_index("ix_entitlements_room_id", "entitlements", ["room_id"])


def downgrade() -> None:
    op.drop_index("ix_entitlements_room_id", table_name="entitlements")
    op.drop_table("entitlements")
