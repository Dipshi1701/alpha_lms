import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.models import Course, CourseAssignment, Role, User
from app.response import success_response
from app.routes.users import user_to_response
from app.schemas import (
    AssignCoursesBody, CourseAssignmentBrief, CourseCreate, CourseResponse,
    CourseUpdate, LaunchResponse, ScormUploadResponse, UserResponse,
)
from app.security import get_current_user, require_roles
from app.services import group_service as gs
from app.services.notification_service import notify_course_assigned
from app.utils.scorm_manifest import parse_scorm_package
from app.utils.scorm_zip import safe_extract_zip, validate_zip_bytes

router = APIRouter()


def course_dir(course_id: int) -> Path:
    return config.SCORM_STORAGE_PATH / str(course_id)


def get_assigned_ids(db: Session, course_id: int) -> list[int]:
    rows = db.query(CourseAssignment.user_id).filter(CourseAssignment.course_id == course_id).all()
    return [r[0] for r in rows]


def get_course_assignment_briefs(
    db: Session, course_id: int, *, current_user: Optional[User] = None
) -> list[CourseAssignmentBrief]:
    """
    Read view over the existing CourseAssignment rows for a course --
    powers duplicate-prevention + Assigned/Due/Source display in the UI
    (G012). Does not create a second assignment system: `source` is
    derived, not persisted (see group_service.resolve_assignment_source).

    If `current_user` currently holds the Learner role, the result is
    scoped to that learner's own row only, so a Learner calling
    /api/courses/me or GET /api/courses/{id} never sees another learner's
    assigned_at/due_date.
    """
    query = db.query(CourseAssignment).filter(CourseAssignment.course_id == course_id)
    if current_user is not None and "Learner" in {r.name for r in current_user.roles}:
        query = query.filter(CourseAssignment.user_id == current_user.id)
    rows = query.order_by(CourseAssignment.user_id).all()

    briefs: list[CourseAssignmentBrief] = []
    for row in rows:
        source, group_name = gs.resolve_assignment_source(
            db, course_id=course_id, user_id=row.user_id, assigned_at=row.assigned_at
        )
        briefs.append(
            CourseAssignmentBrief(
                user_id=row.user_id,
                assigned_at=row.assigned_at,
                due_date=row.due_date,
                source=source,
                source_group_name=group_name,
            )
        )
    return briefs


def course_to_response(db: Session, c: Course, current_user: Optional[User] = None) -> CourseResponse:
    data = CourseResponse.model_validate(c)
    data.assigned_user_ids = get_assigned_ids(db, c.id)
    data.learner_assignments = get_course_assignment_briefs(db, c.id, current_user=current_user)
    return data


def has_valid_scorm(c: Course) -> bool:
    return bool(c.scorm_launch_relative and c.scorm_package_sha256 and c.scorm_validated_at)


# ── Course endpoints ──────────────────────────────────────────────────────────

@router.get("")
def list_courses(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator", "Instructor")),
):
    """All courses for admin/instructor."""
    courses = db.query(Course).order_by(Course.id.desc()).all()
    payload = [course_to_response(db, c).model_dump() for c in courses]
    return success_response(message="Courses fetched successfully", data=payload)


@router.get("/me")
def my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Learner")),
):
    """Published courses assigned to the logged-in learner."""
    courses = (
        db.query(Course)
        .join(CourseAssignment, CourseAssignment.course_id == Course.id)
        .filter(CourseAssignment.user_id == current_user.id, Course.status == "Published")
        .order_by(Course.title)
        .all()
    )
    payload = [course_to_response(db, c, current_user).model_dump() for c in courses]
    return success_response(message="My courses fetched successfully", data=payload)


@router.get("/assignable-users")
def assignable_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator", "Instructor")),
):
    """All learner accounts (used to populate the assign-users dropdown)."""
    learners = (
        db.query(User)
        .join(User.roles)
        .filter(Role.name == "Learner")
        .order_by(User.id)
        .all()
    )
    payload = [user_to_response(u).model_dump() for u in learners]
    return success_response(message="Assignable users fetched successfully", data=payload)


@router.post("")
def create_course(
    body: CourseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator", "Instructor")),
):
    if body.status == "Published":
        raise HTTPException(
            status_code=400,
            detail="Create the course as Draft first, upload a SCORM package, then publish.",
        )
    c = Course(
        title=body.title.strip(),
        description=(body.description or "").strip() or None,
        category=body.category.strip() or "General",
        code=body.code.strip() if body.code else None,
        price=body.price.strip() if body.price else None,
        status="Draft",
        content_type="scorm12",
        assignment_duration_days=body.assignment_duration_days,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    payload = course_to_response(db, c).model_dump()
    return success_response(message="Course created successfully", data=payload, status_code=status.HTTP_201_CREATED)


@router.get("/{course_id}")
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    roles = {r.name for r in current_user.roles}
    if "Learner" in roles:
        assigned = db.query(CourseAssignment).filter(
            CourseAssignment.course_id == course_id,
            CourseAssignment.user_id == current_user.id,
        ).first()
        if c.status != "Published" or not assigned:
            raise HTTPException(status_code=403, detail="Not allowed")
    payload = course_to_response(db, c, current_user).model_dump()
    return success_response(message="Course fetched successfully", data=payload)


@router.patch("/{course_id}")
def update_course(
    course_id: int,
    body: CourseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator", "Instructor")),
):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    if body.title is not None:
        c.title = body.title.strip()
    if body.description is not None:
        c.description = body.description.strip() or None
    if body.category is not None:
        c.category = body.category.strip()
    if body.code is not None:
        c.code = body.code.strip() or None
    if body.price is not None:
        c.price = body.price.strip() or None
    if body.status in ("Draft", "Published"):
        if body.status == "Published" and not has_valid_scorm(c):
            raise HTTPException(status_code=400, detail="Upload a SCORM package before publishing")
        c.status = body.status
    if body.assignment_duration_days is not None:
        # PART 11: the course stays editable at any time; this only affects
        # NEW CourseAssignment rows created from now on -- existing
        # assigned_at/due_date values are never recalculated.
        c.assignment_duration_days = body.assignment_duration_days
    db.commit()
    db.refresh(c)
    payload = course_to_response(db, c).model_dump()
    return success_response(message="Course updated successfully", data=payload)


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator", "Instructor")),
):
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(c)
    db.commit()
    d = course_dir(course_id)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
    return success_response(message="Course deleted successfully", data={"course_id": course_id})


@router.post("/{course_id}/assign")
def assign_course(
    course_id: int,
    body: AssignCoursesBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator", "Instructor")),
):
    """
    Set the desired learner user_ids for a course to exactly `body.user_ids`.

    G012: unlike the previous delete-all/recreate-all implementation, this
    only touches rows that actually change:
      * a user no longer in the desired set -> their CourseAssignment row
        is deleted (this IS the existing supported unassign flow -- PART 12).
      * a user already assigned who remains in the desired set -> their row
        (assigned_at, due_date, assigned_by_id) is left completely
        untouched. This matters even more now than before: it protects
        group-derived CourseAssignment rows that happen to be included in
        the desired set (e.g. because the caller pre-fills the request
        with the course's current assignees, as the frontend does), and it
        stops assigned_at/due_date from being silently reset every time
        this endpoint is called again for the same course.
      * a genuinely new user -> a fresh CourseAssignment row is created
        with assigned_at = now and due_date computed from that same
        assigned_at and the course's *current* assignment_duration_days.
    """
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")

    existing_rows = db.query(CourseAssignment).filter(CourseAssignment.course_id == course_id).all()
    existing_by_user = {r.user_id: r for r in existing_rows}
    existing_ids = set(existing_by_user.keys())
    desired_ids = set(body.user_ids)

    new_user_ids = desired_ids - existing_ids
    removed_user_ids = existing_ids - desired_ids

    for uid in removed_user_ids:
        db.delete(existing_by_user[uid])

    assigned_at = datetime.utcnow()
    for uid in new_user_ids:
        db.add(
            CourseAssignment(
                course_id=course_id,
                user_id=uid,
                assigned_at=assigned_at,
                due_date=gs.compute_due_date(c, assigned_at),
                assigned_by_id=current_user.id,
            )
        )

    if new_user_ids:
        notify_course_assigned(db, user_ids=list(new_user_ids), course=c)
    db.commit()
    return success_response(
        message="Course assignments updated successfully",
        data={"course_id": course_id, "user_ids": sorted(desired_ids)},
    )


@router.post("/{course_id}/scorm/upload")
async def upload_scorm(
    course_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator", "Instructor")),
    file: UploadFile = File(...),
):
    """Upload and extract a SCORM .zip package for a course."""
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip")

    content = await file.read()
    try:
        validate_zip_bytes(content, config.SCORM_MAX_ZIP_BYTES)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")

    base = course_dir(course_id)
    if base.exists():
        shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True, exist_ok=True)

    zip_path = base / "package.zip"
    zip_path.write_bytes(content)
    unpacked = base / "unpacked"

    try:
        filename_map = safe_extract_zip(zip_path, unpacked)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    parsed = parse_scorm_package(unpacked, base, filename_map)
    if not parsed:
        raise HTTPException(
            status_code=400,
            detail="Invalid SCORM package: imsmanifest.xml not found or no launch resource defined.",
        )

    c.scorm_zip_name = file.filename
    c.scorm_launch_relative = parsed.launch_relative_stored
    c.scorm_imsmanifest_relative = parsed.imsmanifest_relative
    c.scorm_manifest_title = parsed.manifest_title
    c.scorm_manifest_identifier = parsed.manifest_identifier
    c.scorm_schema_version = parsed.schema_version
    c.scorm_package_bytes = len(content)
    c.scorm_package_sha256 = hashlib.sha256(content).hexdigest()
    c.scorm_validated_at = datetime.utcnow()

    # Store SCORM runtime metadata extracted from the manifest
    # These are returned to the JS runtime via GET /api/scorm/{id}/state
    c.scorm_datafromlms     = parsed.datafromlms     or ""
    c.scorm_masteryscore    = parsed.masteryscore     or ""
    c.scorm_maxtimeallowed  = parsed.maxtimeallowed   or ""
    c.scorm_timelimitaction = parsed.timelimitaction  or ""

    db.commit()
    db.refresh(c)

    launch_url = f"api/scorm-content/{course_id}/{parsed.launch_relative_stored}"
    payload = ScormUploadResponse(
        message="SCORM package uploaded successfully",
        scorm_zip_name=c.scorm_zip_name,
        scorm_launch_relative=c.scorm_launch_relative,
        launch_url=launch_url,
        scorm_manifest_title=c.scorm_manifest_title,
        scorm_package_sha256=c.scorm_package_sha256,
        scorm_package_bytes=c.scorm_package_bytes,
    )
    return success_response(message="SCORM package uploaded successfully", data=payload.model_dump())


@router.get("/{course_id}/launch")
def launch_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the URL to open the SCORM player for a course."""
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    if not has_valid_scorm(c):
        raise HTTPException(status_code=400, detail="No SCORM content uploaded for this course")
    roles = {r.name for r in current_user.roles}
    if "Learner" in roles:
        if c.status != "Published":
            raise HTTPException(status_code=403, detail="Course is not published")
        assigned = db.query(CourseAssignment).filter(
            CourseAssignment.course_id == course_id,
            CourseAssignment.user_id == current_user.id,
        ).first()
        if not assigned:
            raise HTTPException(status_code=403, detail="You are not assigned to this course")
    payload = LaunchResponse(launch_url=f"/scorm-content/{course_id}/{c.scorm_launch_relative}")
    return success_response(message="Launch URL generated successfully", data=payload.model_dump())
