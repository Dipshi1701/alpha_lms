"""Add notifications table for in-app alerts

Revision ID: 0002
Revises: 0001
Create Date: 2025-05-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    table_names = set(insp.get_table_names())

    if "notifications" not in table_names:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("type", sa.String(64), nullable=False),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    else:
        index_names = {idx["name"] for idx in insp.get_indexes("notifications")}
        if "ix_notifications_user_id" not in index_names:
            op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "notifications" not in insp.get_table_names():
        return
    index_names = {idx["name"] for idx in insp.get_indexes("notifications")}
    if "ix_notifications_user_id" in index_names:
        op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
