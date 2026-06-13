"""add user moderation fields: banned, limit_override

Revision ID: 0004_user_moderation
Revises: 0003_user_role
Create Date: 2026-06-13
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_user_moderation"
down_revision: Union[str, None] = "0003_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "banned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column("users", sa.Column("limit_override", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "limit_override")
    op.drop_column("users", "banned")
