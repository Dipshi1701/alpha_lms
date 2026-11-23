"""Add groups, group_members, and group_managers tables

groups          — a named collection of learners (e.g. "Cohort A")
group_members   — learners (Users) who belong to a group
group_managers  — instructors (Users) who manage a group

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-14
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    table_names = set(insp.get_table_names())

    # ── groups ────────────────────────────────────────────────────────────────
    if "groups" not in table_names:
        op.create_table(
            "groups",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, unique=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        )
        table_names.add("groups")
    else:
        unique_names = {c["name"] for c in insp.get_unique_constraints("groups")}
        if "uq_groups_name" not in unique_names:
            op.create_unique_constraint("uq_groups_name", "groups", ["name"])

    # ── group_members (learners belonging to a group) ────────────────────────
    if "group_members" not in table_names:
        op.create_table(
            "group_members",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("added_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("group_id", "user_id", name="uq_group_members_group_id_user_id"),
        )
        table_names.add("group_members")
    else:
        unique_names = {c["name"] for c in insp.get_unique_constraints("group_members")}
        if "uq_group_members_group_id_user_id" not in unique_names:
            op.create_unique_constraint(
                "uq_group_members_group_id_user_id", "group_members", ["group_id", "user_id"]
            )

    # ── group_managers (instructors who manage a group) ──────────────────────
    if "group_managers" not in table_names:
        op.create_table(
            "group_managers",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("group_id", "user_id", name="uq_group_managers_group_id_user_id"),
        )
    else:
        unique_names = {c["name"] for c in insp.get_unique_constraints("group_managers")}
        if "uq_group_managers_group_id_user_id" not in unique_names:
            op.create_unique_constraint(
                "uq_group_managers_group_id_user_id", "group_managers", ["group_id", "user_id"]
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    table_names = set(insp.get_table_names())

    # Drop children before the parent table (FK dependency order).
    if "group_managers" in table_names:
        op.drop_table("group_managers")
    if "group_members" in table_names:
        op.drop_table("group_members")
    if "groups" in table_names:
        op.drop_table("groups")
