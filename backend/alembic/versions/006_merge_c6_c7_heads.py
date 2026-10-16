"""Merge Alembic heads C6 roster + C7 room tasks.

Revision ID: 006_merge_c6_c7_heads
Revises: 005_c6_freelancer_roster, 005_c7_room_tasks
Create Date: 2026-10-16

"""

from typing import Sequence, Union

revision: str = "006_merge_c6_c7_heads"
down_revision: Union[str, Sequence[str], None] = (
    "005_c6_freelancer_roster",
    "005_c7_room_tasks",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
