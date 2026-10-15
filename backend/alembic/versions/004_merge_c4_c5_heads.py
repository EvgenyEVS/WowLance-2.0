"""Merge Alembic heads C4 slots + C5 strategy proposals.

Revision ID: 004_merge_c4_c5_heads
Revises: 003_c4_room_function_slots, 003_c5_strategy_proposals
Create Date: 2026-10-15

"""

from typing import Sequence, Union

revision: str = "004_merge_c4_c5_heads"
down_revision: Union[str, Sequence[str], None] = (
    "003_c4_room_function_slots",
    "003_c5_strategy_proposals",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
