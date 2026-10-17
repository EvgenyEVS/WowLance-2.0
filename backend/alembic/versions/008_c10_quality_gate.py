"""C10 quality gate: proof/review columns on room_tasks

Revision ID: 008_c10_quality_gate
Revises: 007_c9_hot_leads
Create Date: 2026-10-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_c10_quality_gate"
down_revision: Union[str, Sequence[str], None] = "007_c9_hot_leads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "room_tasks", sa.Column("proof_uri", sa.String(length=2048), nullable=True)
    )
    op.add_column("room_tasks", sa.Column("proof_note", sa.Text(), nullable=True))
    op.add_column(
        "room_tasks",
        sa.Column("reviewed_by_sub", sa.String(length=255), nullable=True),
    )
    op.add_column("room_tasks", sa.Column("review_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("room_tasks", "review_note")
    op.drop_column("room_tasks", "reviewed_by_sub")
    op.drop_column("room_tasks", "proof_note")
    op.drop_column("room_tasks", "proof_uri")
