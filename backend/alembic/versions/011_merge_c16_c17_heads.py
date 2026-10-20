"""Merge Alembic heads after C16 earnings + C17 member terminated.

Revision ID: 011_merge_c16_c17_heads
Revises: 010_c16_earnings, 010_c17_member_terminated
Create Date: 2026-10-20

"""

from typing import Sequence, Union

revision: str = "011_merge_c16_c17_heads"
down_revision: Union[str, Sequence[str], None] = (
    "010_c16_earnings",
    "010_c17_member_terminated",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
