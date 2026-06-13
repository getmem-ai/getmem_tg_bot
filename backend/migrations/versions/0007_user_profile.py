"""add user profile fields (avatar + reply preferences)

Revision ID: 0007_user_profile
Revises: 0006_user_is_admin
Create Date: 2026-06-13
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_user_profile"
down_revision: Union[str, None] = "0006_user_is_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("reply_language", sa.String(length=8), nullable=True))
    op.add_column("users", sa.Column("reply_style", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("reply_length", sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "reply_length")
    op.drop_column("users", "reply_style")
    op.drop_column("users", "reply_language")
    op.drop_column("users", "avatar")
