"""Add group_course_assignments table

group_course_assignments — links a Group to a Course it has been
collectively assigned. This is the Group -> Course assignment foundation
only: it does NOT create per-learner course_assignments rows for each
GroupMember; that expansion is a later milestone. There is no due_date
column, matching the existing course_assignments table which has none.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    table_names = set(insp.get_table_names())

    if "group_course_assignments" not in table_names:
        op.create_table(
            "group_course_assignments",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
            sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
            sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("assigned_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.UniqueConstraint(
                "group_id", "course_id", name="uq_group_course_assignments_group_id_course_id"
            ),
        )
    else:
        unique_names = {c["name"] for c in insp.get_unique_constraints("group_course_assignments")}
        if "uq_group_course_assignments_group_id_course_id" not in unique_names:
            op.create_unique_constraint(
                "uq_group_course_assignments_group_id_course_id",
                "group_course_assignments",
                ["group_id", "course_id"],
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    table_names = set(insp.get_table_names())
    if "group_course_assignments" in table_names:
        op.drop_table("group_course_assignments")
