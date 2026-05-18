"""SCORM full runtime schema

Adds:
  - New columns on courses       (scorm_datafromlms, scorm_masteryscore, scorm_maxtimeallowed, scorm_timelimitaction)
  - New columns on scorm_progress (score_min, score_max, entry, lesson_mode, scorm_exit, credit,
                                   comments, comments_from_lms, first_access_time, last_accessed_time)
  - Widen scorm_progress columns  (lesson_location TEXT, suspend_data TEXT, total_time VARCHAR(32), session_time VARCHAR(32))
  - New table: scorm_interactions

Revision ID: 0001
Revises:
Create Date: 2025-04-17 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. New columns on `courses` ──────────────────────────────────────────
    # SCORM runtime metadata extracted from imsmanifest.xml.
    # Returned to the JS runtime in tl_sco_data via GET /api/scorm/{id}/state.
    op.add_column("courses", sa.Column("scorm_datafromlms",     sa.Text(),        nullable=True))
    op.add_column("courses", sa.Column("scorm_masteryscore",    sa.String(16),    nullable=True))
    op.add_column("courses", sa.Column("scorm_maxtimeallowed",  sa.String(32),    nullable=True))
    op.add_column("courses", sa.Column("scorm_timelimitaction", sa.String(64),    nullable=True))

    # ── 2. New columns on `scorm_progress` ───────────────────────────────────
    # score_min / score_max — JS sends minscore/maxscore, mapped to these columns
    op.add_column("scorm_progress", sa.Column("score_min",         sa.String(16),    nullable=True))
    op.add_column("scorm_progress", sa.Column("score_max",         sa.String(16),    nullable=True))

    # SCORM runtime state fields
    op.add_column("scorm_progress", sa.Column("entry",             sa.String(16),    nullable=True, server_default="ab-initio"))
    op.add_column("scorm_progress", sa.Column("lesson_mode",       sa.String(16),    nullable=True, server_default="normal"))
    op.add_column("scorm_progress", sa.Column("scorm_exit",        sa.String(16),    nullable=True))
    op.add_column("scorm_progress", sa.Column("credit",            sa.String(16),    nullable=True, server_default="credit"))
    op.add_column("scorm_progress", sa.Column("comments",          sa.Text(),        nullable=True))
    op.add_column("scorm_progress", sa.Column("comments_from_lms", sa.Text(),        nullable=True))

    # Reporting / access timestamps
    op.add_column("scorm_progress", sa.Column("first_access_time",  sa.DateTime(),   nullable=True))
    op.add_column("scorm_progress", sa.Column("last_accessed_time", sa.DateTime(),   nullable=True))

    # ── 3. Widen existing `scorm_progress` columns ───────────────────────────
    # lesson_location: String(1024)  →  Text
    # suspend_data:    already Text  (no change needed, stays as-is)
    # total_time:      String(16)    →  String(32)
    # session_time:    String(16)    →  String(32)
    op.alter_column(
        "scorm_progress", "lesson_location",
        existing_type=sa.String(1024),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "scorm_progress", "total_time",
        existing_type=sa.String(16),
        type_=sa.String(32),
        existing_nullable=True,
        server_default="0000:00:00.00",
    )
    op.alter_column(
        "scorm_progress", "session_time",
        existing_type=sa.String(16),
        type_=sa.String(32),
        existing_nullable=True,
    )

    # ── 4. Create new `scorm_interactions` table ─────────────────────────────
    # One row per quiz interaction per progress record.
    # Populated from the interactions[] array sent by JS commitData().
    op.create_table(
        "scorm_interactions",
        sa.Column("id",                     sa.Integer(),   primary_key=True, autoincrement=True),
        sa.Column("progress_id",            sa.Integer(),   sa.ForeignKey("scorm_progress.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interaction_index",      sa.Integer(),   nullable=False),
        sa.Column("interaction_id",         sa.String(255), nullable=True),
        sa.Column("interaction_time",       sa.String(32),  nullable=True),
        sa.Column("interaction_type",       sa.String(32),  nullable=True),
        sa.Column("weighting",              sa.String(16),  nullable=True),
        sa.Column("student_response",       sa.Text(),      nullable=True),
        sa.Column("result",                 sa.String(32),  nullable=True),
        sa.Column("latency",                sa.String(32),  nullable=True),
        sa.Column("correct_responses_json", sa.Text(),      nullable=True),
        sa.Column("created_at",             sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at",             sa.DateTime(),  nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_scorm_interactions_progress_id", "scorm_interactions", ["progress_id"])


def downgrade() -> None:
    # ── Reverse in the opposite order ────────────────────────────────────────

    # 4. Drop scorm_interactions
    op.drop_index("ix_scorm_interactions_progress_id", "scorm_interactions")
    op.drop_table("scorm_interactions")

    # 3. Restore original column sizes
    op.alter_column(
        "scorm_progress", "lesson_location",
        existing_type=sa.Text(),
        type_=sa.String(1024),
        existing_nullable=True,
    )
    op.alter_column(
        "scorm_progress", "total_time",
        existing_type=sa.String(32),
        type_=sa.String(16),
        existing_nullable=True,
    )
    op.alter_column(
        "scorm_progress", "session_time",
        existing_type=sa.String(32),
        type_=sa.String(16),
        existing_nullable=True,
    )

    # 2. Remove new scorm_progress columns
    for col in [
        "last_accessed_time", "first_access_time",
        "comments_from_lms", "comments",
        "credit", "scorm_exit", "lesson_mode", "entry",
        "score_max", "score_min",
    ]:
        op.drop_column("scorm_progress", col)

    # 1. Remove new courses columns
    for col in ["scorm_timelimitaction", "scorm_maxtimeallowed", "scorm_masteryscore", "scorm_datafromlms"]:
        op.drop_column("courses", col)
