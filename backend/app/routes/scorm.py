"""
SCORM Runtime Routes
--------------------
Handles saving and loading SCORM 1.2 progress per user per course.

Endpoints:
  GET  /api/scorm/my-progress         -> Map of {course_id: progress} for current user
  GET  /api/scorm/{course_id}/state   -> Load saved state (used to resume a session)
  POST /api/scorm/{course_id}/commit  -> Save state (called on LMSCommit)
  POST /api/scorm/{course_id}/finish  -> Finalize session (called on LMSFinish)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CourseAssignment, ScormProgress, User
from app.response import success_response
from app.security import get_current_user

router = APIRouter()


# ── Pydantic schema ──────────────────────────────────────────────────────────

class CommitPayload(BaseModel):
    lesson_location: Optional[str] = ""
    suspend_data: Optional[str] = ""
    lesson_status: Optional[str] = ""
    score_raw: Optional[str] = ""
    session_time: Optional[str] = ""
    total_time: Optional[str] = ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _check_access(db: Session, course_id: int, current_user: User) -> None:
    """Allow admins/instructors always; learners only if assigned."""
    roles = {r.name for r in current_user.roles}
    if "Administrator" in roles or "Instructor" in roles:
        return
    assigned = (
        db.query(CourseAssignment)
        .filter(
            CourseAssignment.course_id == course_id,
            CourseAssignment.user_id == current_user.id,
        )
        .first()
    )
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this course",
        )


def _get_or_create_progress(db: Session, course_id: int, user_id: int) -> ScormProgress:
    progress = (
        db.query(ScormProgress)
        .filter(ScormProgress.course_id == course_id, ScormProgress.user_id == user_id)
        .first()
    )
    if not progress:
        progress = ScormProgress(course_id=course_id, user_id=user_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def _compute_percent(lesson_status: str) -> int:
    """Map lesson_status to a 0-100 progress percent."""
    if lesson_status in ("completed", "passed", "failed"):
        return 100
    if lesson_status == "incomplete":
        return 50
    return 0


def _apply_payload(progress: ScormProgress, payload: CommitPayload) -> None:
    """Write payload fields onto the progress row (only non-None / non-empty)."""
    if payload.lesson_location is not None:
        progress.lesson_location = payload.lesson_location[:1024]
    if payload.suspend_data is not None:
        progress.suspend_data = payload.suspend_data[:4096]
    if payload.lesson_status:
        progress.lesson_status = payload.lesson_status[:32]
    if payload.score_raw is not None:
        progress.score_raw = payload.score_raw[:16]
    if payload.session_time:
        progress.session_time = payload.session_time[:16]
    if payload.total_time:
        progress.total_time = payload.total_time[:16]


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/my-progress")
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns a dict of { course_id_str: { lesson_status, progress_percent } } for the current user."""
    rows = db.query(ScormProgress).filter(ScormProgress.user_id == current_user.id).all()
    progress_map = {
        str(row.course_id): {
            "lesson_status": row.lesson_status or "not attempted",
            "progress_percent": row.progress_percent or 0,
            "last_commit_at": row.last_commit_at.isoformat() if row.last_commit_at else None,
        }
        for row in rows
    }
    return success_response("Progress loaded", progress_map)


@router.get("/{course_id}/state")
def get_state(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Load saved SCORM state. Frontend uses this to seed window.API values before the iframe loads."""
    _check_access(db, course_id, current_user)
    progress = _get_or_create_progress(db, course_id, current_user.id)

    # If the learner has previously started, tell SCORM to resume; otherwise start fresh.
    entry = (
        "ab-initio"
        if progress.lesson_status in (None, "not attempted", "")
        else "resume"
    )

    return success_response(
        "State loaded",
        {
            "lesson_location": progress.lesson_location or "",
            "suspend_data": progress.suspend_data or "",
            "lesson_status": progress.lesson_status or "not attempted",
            "score_raw": progress.score_raw or "",
            "total_time": progress.total_time or "00:00:00",
            "progress_percent": progress.progress_percent or 0,
            "entry": entry,
        },
    )


@router.post("/{course_id}/commit")
def commit_state(
    course_id: int,
    payload: CommitPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Persist SCORM runtime values. Called by the frontend on every LMSCommit."""
    _check_access(db, course_id, current_user)
    progress = _get_or_create_progress(db, course_id, current_user.id)

    _apply_payload(progress, payload)
    progress.progress_percent = _compute_percent(progress.lesson_status or "")
    progress.last_commit_at = datetime.utcnow()

    db.commit()

    return success_response("Progress saved", {"progress_percent": progress.progress_percent})


@router.post("/{course_id}/finish")
def finish_state(
    course_id: int,
    payload: CommitPayload = CommitPayload(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Finalize the SCORM session. Called by the frontend on LMSFinish."""
    _check_access(db, course_id, current_user)
    progress = _get_or_create_progress(db, course_id, current_user.id)

    _apply_payload(progress, payload)
    progress.progress_percent = _compute_percent(progress.lesson_status or "")
    progress.last_commit_at = datetime.utcnow()

    if progress.lesson_status in ("completed", "passed", "failed"):
        progress.completed_at = datetime.utcnow()

    db.commit()

    return success_response(
        "Session finished",
        {
            "lesson_status": progress.lesson_status,
            "progress_percent": progress.progress_percent,
        },
    )
