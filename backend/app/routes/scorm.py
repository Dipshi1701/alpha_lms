"""
SCORM Runtime Routes
--------------------
Three clearly separated layers:

  LAYER 1 — SCORM Launch / Resume API
    GET  /api/scorm/{course_id}/state
    Returns tl_sco_data — the exact shape the JS runtime reads before the iframe loads.

  LAYER 2 — SCORM Save APIs
    POST /api/scorm/{course_id}/commit   — called on LMSCommit()
    POST /api/scorm/{course_id}/finish   — called on LMSFinish()
    Accepts raw SCORM runtime payload from JS commitData().

  LAYER 3 — LMS Progress / Reporting APIs
    GET  /api/scorm/my-progress                  — all courses summary for current user
    GET  /api/scorm/{course_id}/progress-summary — one course detail report

Reporting endpoints return business/dashboard fields.
They are completely separate from the raw SCORM launch state.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Course, CourseAssignment, ScormInteraction, ScormProgress, User
from app.response import success_response
from app.security import get_current_user

router = APIRouter()


# ═══════════════════════════════════════════════════════════════
#  PYDANTIC SCHEMAS
# ═══════════════════════════════════════════════════════════════

class InteractionPayload(BaseModel):
    """One quiz interaction entry from the JS interactions[] array."""
    id:                Optional[str]                    = ""
    time:              Optional[str]                    = ""
    type:              Optional[str]                    = ""
    weighting:         Optional[str]                    = ""
    student_response:  Optional[str]                    = ""
    result:            Optional[str]                    = ""
    latency:           Optional[str]                    = ""
    correct_responses: Optional[List[Dict[str, Any]]]  = []


class ScormCommitPayload(BaseModel):
    """
    Raw SCORM runtime payload sent by JS commitData().

    JS field name  →  DB column
    ─────────────────────────────
    score          →  score_raw
    minscore       →  score_min
    maxscore       →  score_max
    scorm_exit     →  scorm_exit
    (all other fields map 1:1)
    """
    lesson_location: Optional[str]                   = ""
    suspend_data:    Optional[str]                   = ""
    lesson_status:   Optional[str]                   = ""
    total_time:      Optional[str]                   = ""
    session_time:    Optional[str]                   = ""   # only reliable on LMSFinish
    entry:           Optional[str]                   = ""
    credit:          Optional[str]                   = ""
    comments:        Optional[str]                   = ""
    scorm_exit:      Optional[str]                   = ""

    # JS sends: score / minscore / maxscore
    score:    Optional[str] = ""
    minscore: Optional[str] = ""
    maxscore: Optional[str] = ""

    interactions: Optional[List[InteractionPayload]] = []


# ═══════════════════════════════════════════════════════════════
#  SHARED HELPERS
# ═══════════════════════════════════════════════════════════════

def _check_access(db: Session, course_id: int, current_user: User) -> None:
    """Admins and Instructors always pass. Learners must be assigned to the course."""
    roles = {r.name for r in current_user.roles}
    if "Administrator" in roles or "Instructor" in roles:
        return
    assigned = (
        db.query(CourseAssignment)
        .filter(
            CourseAssignment.course_id == course_id,
            CourseAssignment.user_id   == current_user.id,
        )
        .first()
    )
    if not assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this course",
        )


def _get_or_create_progress(db: Session, course_id: int, user_id: int) -> ScormProgress:
    """
    Return the existing progress row or create a fresh one.
    Sets first_access_time on creation only.
    """
    progress = (
        db.query(ScormProgress)
        .filter(
            ScormProgress.course_id == course_id,
            ScormProgress.user_id   == user_id,
        )
        .first()
    )
    if not progress:
        now = datetime.utcnow()
        progress = ScormProgress(
            course_id=course_id,
            user_id=user_id,
            first_access_time=now,
        )
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def _compute_percent(lesson_status: str) -> int:
    """Translate lesson_status into a 0–100 progress percentage."""
    if lesson_status in ("completed", "passed", "failed"):
        return 100
    if lesson_status == "incomplete":
        return 50
    return 0


def _has_meaningful_progress(progress: ScormProgress) -> bool:
    """
    Returns True if the learner has real saved progress worth resuming.
    Used to decide 'ab-initio' vs 'resume' in the launch state.
    """
    has_suspend  = bool(progress.suspend_data   and progress.suspend_data.strip())
    has_location = bool(progress.lesson_location and progress.lesson_location.strip())
    has_status   = progress.lesson_status not in (None, "", "not attempted")
    return has_suspend or has_location or has_status


def _apply_raw_payload(progress: ScormProgress, payload: ScormCommitPayload) -> None:
    """
    Write raw SCORM runtime fields from the JS payload onto the progress row.

    Rules:
    - suspend_data is stored verbatim — never parsed, trimmed, or interpreted
    - lesson_location is stored as-is (SCO-defined bookmark string)
    - total_time is intentionally NOT set here — handled by the caller on finish
    - session_time is stored but not used in business logic
    - score/minscore/maxscore are mapped to score_raw/score_min/score_max
    """
    if payload.lesson_location is not None:
        progress.lesson_location = payload.lesson_location

    if payload.suspend_data is not None:
        progress.suspend_data = payload.suspend_data  # stored verbatim

    if payload.lesson_status:
        progress.lesson_status = payload.lesson_status[:32]

    # JS sends 'score', 'minscore', 'maxscore' → map to DB names
    if payload.score is not None:
        progress.score_raw = payload.score[:16]
    if payload.minscore is not None:
        progress.score_min = payload.minscore[:16]
    if payload.maxscore is not None:
        progress.score_max = payload.maxscore[:16]

    if payload.session_time:
        progress.session_time = payload.session_time[:32]

    if payload.entry:
        progress.entry = payload.entry[:16]

    if payload.credit:
        progress.credit = payload.credit[:16]

    if payload.comments:
        progress.comments = payload.comments

    if payload.scorm_exit:
        progress.scorm_exit = payload.scorm_exit[:16]


def _save_interactions(
    db: Session,
    progress: ScormProgress,
    interactions: List[InteractionPayload],
) -> None:
    """
    Replace all stored interactions for this progress row with the latest list.
    Called on every commit/finish so the table always reflects the current session state.
    """
    if not interactions:
        return

    # Delete the previous interaction records for this progress row
    db.query(ScormInteraction).filter(
        ScormInteraction.progress_id == progress.id
    ).delete()

    for i, inter in enumerate(interactions):
        db.add(ScormInteraction(
            progress_id            = progress.id,
            interaction_index      = i,
            interaction_id         = (inter.id or "")[:255],
            interaction_time       = (inter.time or "")[:32],
            interaction_type       = (inter.type or "")[:32],
            weighting              = (inter.weighting or "")[:16],
            student_response       = inter.student_response or "",
            result                 = (inter.result or "")[:32],
            latency                = (inter.latency or "")[:32],
            correct_responses_json = json.dumps(inter.correct_responses or []),
        ))


# ═══════════════════════════════════════════════════════════════
#  LAYER 1 — SCORM LAUNCH / RESUME API
#
#  GET /api/scorm/{course_id}/state
#
#  Returns tl_sco_data: the shape the JS runtime reads before
#  being assigned to window.tl_sco_data and the iframe loads.
#  Pure SCORM runtime state — no dashboard or reporting fields.
# ═══════════════════════════════════════════════════════════════

@router.get("/my-progress")
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a summary of all SCORM progress for the current user.
    Used by the learner's course list / dashboard view.

    Note: placed before /{course_id} routes to avoid route shadowing.
    """
    rows = db.query(ScormProgress).filter(ScormProgress.user_id == current_user.id).all()

    progress_map = {}
    for row in rows:
        progress_map[str(row.course_id)] = {
            "lesson_status":      row.lesson_status      or "not attempted",
            "progress_percent":   row.progress_percent   or 0,
            "score":              row.score_raw           or None,
            "completed_at":       row.completed_at.isoformat()       if row.completed_at       else None,
            "last_accessed_time": row.last_accessed_time.isoformat() if row.last_accessed_time else None,
        }

    return success_response("Progress loaded", progress_map)


@router.get("/{course_id}/state")
def get_launch_state(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns tl_sco_data for the SCORM runtime JS.
    Frontend assigns this to window.tl_sco_data before loading the runtime and the iframe.

    This endpoint returns ONLY raw SCORM runtime state.
    Dashboard/reporting fields are served by /progress-summary.
    """
    _check_access(db, course_id, current_user)

    # Fetch course for LMS-configured metadata (datafromlms, masteryscore, etc.)
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Fetch or create the learner's progress row
    progress = _get_or_create_progress(db, course_id, current_user.id)

    # Decide resume mode: only resume if there is meaningful saved progress
    entry = "resume" if _has_meaningful_progress(progress) else "ab-initio"

    return success_response("Launch state loaded", {
        # ── Learner identity ─────────────────────────────────────────────────
        # Read by cmi.core.student_id and cmi.core.student_name in the JS runtime
        "student_id":   str(current_user.id),
        "student_name": current_user.full_name or current_user.email or "",

        # ── Resumable runtime state ──────────────────────────────────────────
        "lesson_location": progress.lesson_location or "",
        "suspend_data":    progress.suspend_data    or "",
        "lesson_status":   progress.lesson_status   or "not attempted",
        "score_raw":       progress.score_raw       or "",
        "total_time":      progress.total_time      or "0000:00:00.00",
        "entry":           entry,

        # ── LMS-configured course metadata (from imsmanifest.xml) ────────────
        "datafromlms":     course.scorm_datafromlms     or "",
        "masteryscore":    course.scorm_masteryscore     or "",
        "maxtimeallowed":  course.scorm_maxtimeallowed   or "",
        "timelimitaction": course.scorm_timelimitaction  or "",

        # ── Fixed LMS-controlled defaults ────────────────────────────────────
        "lesson_mode":       progress.lesson_mode       or "normal",
        "comments_from_lms": progress.comments_from_lms or "",
    })


# ═══════════════════════════════════════════════════════════════
#  LAYER 2 — SCORM SAVE APIs
#
#  POST /api/scorm/{course_id}/commit   — LMSCommit()
#  POST /api/scorm/{course_id}/finish   — LMSFinish()
#
#  Accept the raw JSON payload sent by JS commitData().
#  Persist it faithfully with minimal business logic.
# ═══════════════════════════════════════════════════════════════

@router.post("/{course_id}/commit")
def commit_state(
    course_id: int,
    payload: ScormCommitPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Persist mid-session SCORM state.
    Called by the JS runtime on every LMSCommit().

    total_time is NOT updated here — only updated on finish.
    The JS sends accumulated total_time at the end of the session via LMSFinish.
    """
    _check_access(db, course_id, current_user)
    progress = _get_or_create_progress(db, course_id, current_user.id)

    _apply_raw_payload(progress, payload)

    # Derive reporting fields
    progress.progress_percent   = _compute_percent(progress.lesson_status or "")
    progress.last_accessed_time = datetime.utcnow()
    progress.last_commit_at     = datetime.utcnow()

    _save_interactions(db, progress, payload.interactions or [])
    db.commit()

    return success_response("Progress saved", {
        "saved":            True,
        "lesson_status":    progress.lesson_status    or "not attempted",
        "progress_percent": progress.progress_percent,
    })


@router.post("/{course_id}/finish")
def finish_state(
    course_id: int,
    payload: ScormCommitPayload = ScormCommitPayload(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Finalize the SCORM session.
    Called by the JS runtime on LMSFinish().

    total_time is updated here — JS sends the final accumulated value.
    completed_at is stamped when lesson_status reaches a terminal state.
    """
    _check_access(db, course_id, current_user)
    progress = _get_or_create_progress(db, course_id, current_user.id)

    _apply_raw_payload(progress, payload)

    # Update total_time on finish — the JS sends the final accumulated value here
    if payload.total_time:
        progress.total_time = payload.total_time[:32]

    # Derive reporting fields
    progress.progress_percent   = _compute_percent(progress.lesson_status or "")
    progress.last_accessed_time = datetime.utcnow()
    progress.last_commit_at     = datetime.utcnow()

    # Stamp completed_at only when reaching a terminal status for the first time
    if progress.lesson_status in ("completed", "passed", "failed"):
        if not progress.completed_at:
            progress.completed_at = datetime.utcnow()

    _save_interactions(db, progress, payload.interactions or [])
    db.commit()

    return success_response("Session finished", {
        "saved":            True,
        "lesson_status":    progress.lesson_status    or "not attempted",
        "progress_percent": progress.progress_percent,
    })


# ═══════════════════════════════════════════════════════════════
#  LAYER 3 — LMS PROGRESS / REPORTING APIs
#
#  GET /api/scorm/{course_id}/progress-summary
#
#  Returns business/dashboard-friendly data for one course.
#  Completely separate from the raw SCORM launch state.
# ═══════════════════════════════════════════════════════════════

@router.get("/{course_id}/progress-summary")
def get_progress_summary(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns a detailed progress summary for one course.
    Used by admin/instructor reporting or the learner's course detail page.

    Returns business-friendly shape — NOT raw SCORM launch state.
    """
    _check_access(db, course_id, current_user)

    progress = (
        db.query(ScormProgress)
        .filter(
            ScormProgress.course_id == course_id,
            ScormProgress.user_id   == current_user.id,
        )
        .first()
    )

    def time_to_seconds(t: str | None) -> int:
        """Parse a SCORM time string (HH:MM:SS or HHHH:MM:SS.SS) into total seconds."""
        if not t:
            return 0
        try:
            parts = t.split(":")
            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + int(float(s))
        except Exception:
            pass
        return 0

    def safe_float(val: str | None) -> float | None:
        if not val:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    # Learner has never opened this course
    if not progress:
        return success_response("Progress summary loaded", {
            "course_progress": {
                "total_time_seconds":    0,
                "score":                 None,
                "completion_status":     "not attempted",
                "completion_date":       None,
                "completion_percentage": 0,
                "last_viewed_course_id": course_id,
            },
            "unit_progress": {
                "total_time_seconds": 0,
                "status":             "not attempted",
                "score":              None,
                "completion_date":    None,
                "first_access_time":  None,
                "last_accessed_time": None,
            },
        })

    return success_response("Progress summary loaded", {
        "course_progress": {
            "total_time_seconds":    time_to_seconds(progress.total_time),
            "score":                 safe_float(progress.score_raw),
            "completion_status":     progress.lesson_status    or "not attempted",
            "completion_date":       progress.completed_at.isoformat()       if progress.completed_at       else None,
            "completion_percentage": progress.progress_percent or 0,
            "last_viewed_course_id": course_id,
        },
        "unit_progress": {
            "total_time_seconds": time_to_seconds(progress.session_time),
            "status":             progress.lesson_status   or "not attempted",
            "score":              safe_float(progress.score_raw),
            "completion_date":    progress.completed_at.isoformat()       if progress.completed_at       else None,
            "first_access_time":  progress.first_access_time.isoformat()  if progress.first_access_time  else None,
            "last_accessed_time": progress.last_accessed_time.isoformat() if progress.last_accessed_time else None,
        },
    })
