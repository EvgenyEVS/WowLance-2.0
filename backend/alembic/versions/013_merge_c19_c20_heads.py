"""Merge Alembic heads after C19 CRM deal-status + C20 room messages.

Revision ID: 013_merge_c19_c20_heads
Revises: 012_c19_crm_deal_status, 012_c20_room_messages
Create Date: 2026-10-21

"""

from typing import Sequence, Union

revision: str = "013_merge_c19_c20_heads"
down_revision: Union[str, Sequence[str], None] = (
    "012_c19_crm_deal_status",
    "012_c20_room_messages",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
