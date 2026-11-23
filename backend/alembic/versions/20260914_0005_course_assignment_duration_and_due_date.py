"""Add Course.assignment_duration_days and CourseAssignment.due_date

G012 -- course-level default assignment duration + learner-level due date.

* courses.assignment_duration_days: positive integer, NOT NULL. Existing
  courses are backfilled with 7 (one week) purely so the column can be
  added as NOT NULL -- this is a migration-compatibility default only, not
  a new business rule. Every course remains fully editable afterwards;
  admins can (and are expected to) review/set this value explicitly per
  course going forward via the course create/edit UI.
* course_assignments.due_date: nullable DateTime. Existing CourseAssignment
  rows are intentionally left NULL here -- there is no retroactive due-date
  calculation for assignments that predate this feature. Only assignments
  created after this migration ever get a due_date, and it is always
  computed from that specific row's own assigned_at (never a fixed date).

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Backward-compatibility default only (see module docstring) -- not a due
# date/duration business rule. Matches the Course.assignment_duration_days
# model-level default in app/models.py.
DEFAULT_ASSIGNMENT_DURATION_DAYS = 7


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    course_columns = {c["name"] for c in insp.get_columns("courses")}
    if "assignment_duration_days" not in course_columns:
        op.add_column(
            "courses",
            sa.Column(
                "assignment_duration_days",
                sa.Integer(),
                nullable=False,
                server_default=str(DEFAULT_ASSIGNMENT_DURATION_DAYS),
            ),
        )
        # Drop the server default once existing rows are backfilled -- new
        # inserts should always go through the app (which always supplies
        # an explicit value), not silently rely on a DB-level default.
        op.alter_column(
            "courses",
            "assignment_duration_days",
            existing_type=sa.Integer(),
            server_default=None,
            existing_nullable=False,
        )

    assignment_columns = {c["name"] for c in insp.get_columns("course_assignments")}
    if "due_date" not in assignment_columns:
        op.add_column("course_assignments", sa.Column("due_date", sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    assignment_columns = {c["name"] for c in insp.get_columns("course_assignments")}
    if "due_date" in assignment_columns:
        op.drop_column("course_assignments", "due_date")

    course_columns = {c["name"] for c in insp.get_columns("courses")}
    if "assignment_duration_days" in course_columns:
        op.drop_column("courses", "assignment_duration_days")
