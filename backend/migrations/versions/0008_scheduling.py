"""user timezone + scheduled tasks & runs

Revision ID: 0008_scheduling
Revises: 0007_user_profile
Create Date: 2026-06-14
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_scheduling"
down_revision: Union[str, None] = "0007_user_profile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "timezone", sa.String(length=48), nullable=False, server_default="UTC"
        ),
    )

    op.create_table(
        "scheduled_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("frequency", sa.String(length=16), nullable=False),
        sa.Column("times", sa.JSON(), nullable=False),
        sa.Column("weekdays", sa.JSON(), nullable=False),
        sa.Column(
            "enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_scheduled_tasks_user_id", "scheduled_tasks", ["user_id"])
    op.create_index(
        "ix_scheduled_tasks_next_run_at", "scheduled_tasks", ["next_run_at"]
    )

    op.create_table(
        "scheduled_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "task_id",
            sa.Integer(),
            sa.ForeignKey("scheduled_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fired_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("preview", sa.Text(), nullable=False, server_default=""),
    )
    op.create_index("ix_scheduled_runs_task_id", "scheduled_runs", ["task_id"])
    op.create_index("ix_scheduled_runs_user_id", "scheduled_runs", ["user_id"])
    op.create_index("ix_scheduled_runs_fired_at", "scheduled_runs", ["fired_at"])


def downgrade() -> None:
    op.drop_table("scheduled_runs")
    op.drop_table("scheduled_tasks")
    op.drop_column("users", "timezone")
