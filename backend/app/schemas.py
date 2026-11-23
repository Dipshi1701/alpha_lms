from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserBrief(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserBrief
    roles: List[str]


class MeResponse(BaseModel):
    user: UserBrief
    roles: List[str]


# ── Users ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: str  # Must be: Administrator, Instructor, or Learner


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    roles: List[str]
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)


# ── Courses ───────────────────────────────────────────────────────────────────

class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(default="General", max_length=100)
    code: Optional[str] = Field(default=None, max_length=64)
    price: Optional[str] = Field(default=None, max_length=32)
    status: str = Field(default="Draft")
    # G012: days a learner gets from THEIR OWN assignment date, not a fixed
    # due date and not based on course creation date. Defaults to 7 to
    # match the backward-compatible column default (see migration 0005);
    # ge=1 rejects 0/negative values (and non-integers) at the API layer.
    assignment_duration_days: int = Field(default=7, ge=1)


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = None
    price: Optional[str] = None
    status: Optional[str] = None
    # Editable at any time (courses are never "locked" after first
    # assignment -- see PART 11). Only affects NEW CourseAssignment rows
    # created after the change; existing due dates are never recalculated.
    assignment_duration_days: Optional[int] = Field(default=None, ge=1)


class CourseAssignmentBrief(BaseModel):
    """
    A read view over one existing CourseAssignment row for a course --
    powers duplicate-prevention + Assigned/Due/Source display in the UI
    (G012). This does NOT introduce a second assignment system: `source`
    is derived (not persisted) by group_service.resolve_assignment_source,
    see its docstring for exactly how.
    """

    user_id: int
    assigned_at: datetime
    due_date: Optional[datetime] = None
    source: str  # "individual" | "group"
    source_group_name: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    code: Optional[str]
    price: Optional[str]
    status: str
    content_type: str
    assignment_duration_days: int
    scorm_zip_name: Optional[str]
    scorm_launch_relative: Optional[str]
    scorm_imsmanifest_relative: Optional[str]
    scorm_manifest_title: Optional[str]
    scorm_manifest_identifier: Optional[str]
    scorm_schema_version: Optional[str]
    scorm_package_bytes: Optional[int]
    scorm_package_sha256: Optional[str]
    scorm_validated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    assigned_user_ids: List[int] = []
    # Named `learner_assignments` (not `assignments`) to avoid colliding
    # with the Course.assignments SQLAlchemy relationship attribute (which
    # holds raw CourseAssignment ORM rows, not CourseAssignmentBrief) when
    # this schema is built via model_validate(course, from_attributes=True).
    # Scoped to the caller's own row when they are a Learner (never leaks
    # another learner's assignment info) -- see
    # routes.courses.get_course_assignment_briefs.
    learner_assignments: List[CourseAssignmentBrief] = []
    model_config = {"from_attributes": True}


class AssignCoursesBody(BaseModel):
    user_ids: List[int] = []


class LaunchResponse(BaseModel):
    launch_url: str


class ScormUploadResponse(BaseModel):
    message: str
    scorm_zip_name: Optional[str]
    scorm_launch_relative: Optional[str]
    launch_url: Optional[str]
    scorm_manifest_title: Optional[str] = None
    scorm_package_sha256: Optional[str] = None
    scorm_package_bytes: Optional[int] = None


# ── Groups ────────────────────────────────────────────────────────────────────

class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)


class GroupResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    created_by_id: Optional[int] = None
    model_config = {"from_attributes": True}


# Group members — the Learners who belong to a group.
class GroupMemberBody(BaseModel):
    user_id: int


class GroupMemberResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    added_at: datetime
    model_config = {"from_attributes": True}


class GroupMemberDetailResponse(BaseModel):
    """A group member plus the learner fields the group page needs to render."""

    id: int
    group_id: int
    user_id: int
    full_name: Optional[str] = None
    email: str
    added_at: datetime


# Group managers — the Instructors who manage a group. Kept as a distinct
# schema from GroupMemberBody/GroupMemberResponse even though the shape is
# similar, since a "manager" and a "member" are different concepts (see
# GroupManager vs GroupMember in models.py) and should read unambiguously
# in the API/OpenAPI docs.
class GroupManagerBody(BaseModel):
    user_id: int


class GroupManagerResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    assigned_at: datetime
    model_config = {"from_attributes": True}


class GroupManagerDetailResponse(BaseModel):
    """A group manager plus the instructor fields the group page needs to render."""

    id: int
    group_id: int
    user_id: int
    full_name: Optional[str] = None
    email: str
    assigned_at: datetime


# Group course assignments — a Course a Group has been collectively
# assigned. No due_date field here: a due date is a per-learner concept
# (see CourseAssignmentBrief.due_date below), not a per-group one — see
# models.py: GroupCourseAssignment.
class GroupCourseAssignmentBody(BaseModel):
    course_id: int


class GroupCourseAssignmentResponse(BaseModel):
    id: int
    group_id: int
    course_id: int
    assigned_at: datetime
    assigned_by_id: Optional[int] = None
    model_config = {"from_attributes": True}


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    type: str
    title: str
    message: str
    read: bool
    course_id: Optional[int] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class NotificationsListResponse(BaseModel):
    items: List[NotificationResponse]
    unread_count: int


class NotificationPatchBody(BaseModel):
    id: Optional[int] = None
    read_all: bool = False
