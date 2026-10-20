"""C19 CRM deal-status: nullable deal_* columns on room_leads

Revision ID: 012_c19_crm_deal_status
Revises: 011_merge_c16_c17_heads
Create Date: 2026-10-20

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_c19_crm_deal_status"
down_revision: Union[str, Sequence[str], None] = "011_merge_c16_c17_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "room_leads",
        sa.Column("deal_status", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "room_leads",
        sa.Column("deal_amount", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "room_leads",
        sa.Column("deal_currency", sa.String(length=8), nullable=True),
    )
    op.add_column(
        "room_leads",
        sa.Column(
            "deal_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("room_leads", "deal_updated_at")
    op.drop_column("room_leads", "deal_currency")
    op.drop_column("room_leads", "deal_amount")
    op.drop_column("room_leads", "deal_status")
