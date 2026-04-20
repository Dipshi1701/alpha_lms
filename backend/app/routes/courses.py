import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import config
from app.database import get_db
from app.models import Course, CourseAssignment, Role, User
from app.response import success_response
from app.routes.users import user_to_response
from app.schemas import (
    AssignCoursesBody, CourseCreate, CourseResponse,
    CourseUpdate, LaunchResponse, ScormUploadResponse, UserResponse,
)
from app.security import get_current_user, require_roles
from app.utils.scorm_manifest import parse_scorm_package
from app.utils.scorm_zip import safe_extract_zip, validate_zip_bytes

router = APIRouter()


def course_dir(course_id: int) -> Path:
    return config.SCORM_STORAGE_PATH / str(course_id)


def get_assigned_ids(db: Session, course_id: int) -> list[int]:
    rows = db.query(CourseAssignment.user_id).filter(CourseAssignment.course_id == course_id).all()
    return [r[0] for r in rows]


def course_to_response(db: Session, c: Course) -> CourseResponse:
    data = CourseResponse.model_validate(c)
    data.assigned_user_ids = get_assigned_ids(db, c.id)
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
    payload = [course_to_response(db, c).model_dump() for c in courses]
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
    payload = course_to_response(db, c).model_dump()
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
    """Replace all learner assignments for a course with the given user_ids list."""
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    db.query(CourseAssignment).filter(CourseAssignment.course_id == course_id).delete()
    for uid in set(body.user_ids):
        db.add(CourseAssignment(course_id=course_id, user_id=uid, assigned_by_id=current_user.id))
    db.commit()
    return success_response(
        message="Course assignments updated successfully",
        data={"course_id": course_id, "user_ids": sorted(set(body.user_ids))},
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
        safe_extract_zip(zip_path, unpacked)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    parsed = parse_scorm_package(unpacked, base)
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
    db.commit()
    db.refresh(c)

    launch_url = f"/scorm-content/{course_id}/{parsed.launch_relative_stored}"
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
