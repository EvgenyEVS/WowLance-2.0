"""C14 meet: meeting_url stub column on rooms

Revision ID: 009_c14_meet_jitsi
Revises: 008_c10_quality_gate
Create Date: 2026-10-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_c14_meet_jitsi"
down_revision: Union[str, Sequence[str], None] = "008_c10_quality_gate"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rooms", sa.Column("meeting_url", sa.String(length=2048), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("rooms", "meeting_url")
