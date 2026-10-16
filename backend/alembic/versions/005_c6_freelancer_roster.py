"""C6 freelancer roster: freelancer_roster

Revision ID: 005_c6_freelancer_roster
Revises: 004_merge_c4_c5_heads
Create Date: 2026-10-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_c6_freelancer_roster"
down_revision: Union[str, Sequence[str], None] = "004_merge_c4_c5_heads"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "freelancer_roster",
        sa.Column("freelancer_sub", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column(
            "skills",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("level", sa.String(length=32), nullable=True),
        sa.Column(
            "source",
            sa.String(length=32),
            server_default="stub",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("freelancer_sub"),
    )


def downgrade() -> None:
    op.drop_table("freelancer_roster")
