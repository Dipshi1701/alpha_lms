from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Table, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base
import json  # noqa: F401  (available for callers that import from models)

# Join table for the many-to-many relationship between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)

    users = relationship("User", secondary=user_roles, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100), default="General", nullable=False)
    code = Column(String(64))
    price = Column(String(32))
    status = Column(String(20), default="Draft", nullable=False)  # Draft or Published
    content_type = Column(String(32), default="scorm12", nullable=False)

    # SCORM package metadata (filled after upload)
    scorm_zip_name = Column(String(255))
    scorm_launch_relative = Column(String(500))
    scorm_imsmanifest_relative = Column(String(500))
    scorm_manifest_title = Column(Text)
    scorm_manifest_identifier = Column(String(255))
    scorm_schema_version = Column(String(64))
    scorm_package_bytes = Column(Integer)
    scorm_package_sha256 = Column(String(64))
    scorm_validated_at = Column(DateTime)

    # SCORM runtime metadata extracted from imsmanifest.xml
    # These are returned to the JS runtime in tl_sco_data
    scorm_datafromlms     = Column(Text)           # adlcp:datafromlms
    scorm_masteryscore    = Column(String(16))      # mastery score threshold for pass/fail
    scorm_maxtimeallowed  = Column(String(32))      # maximum time allowed (HH:MM:SS)
    scorm_timelimitaction = Column(String(64))      # exit,message / continue,no message / etc.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assignments = relationship("CourseAssignment", back_populates="course", cascade="all, delete-orphan")


class CourseAssignment(Base):
    """Links a learner to a course they are allowed to access."""

    __tablename__ = "course_assignments"
    __table_args__ = (UniqueConstraint("course_id", "user_id"),)

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))

    course = relationship("Course", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id])


class ScormProgress(Base):
    """
    One row per user+course pair.
    Stores raw SCORM 1.2 runtime fields exactly as received from the JS runtime,
    plus derived reporting fields for dashboard/LMS use.
    """

    __tablename__ = "scorm_progress"
    __table_args__ = (UniqueConstraint("course_id", "user_id"),)

    id        = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    user_id   = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)

    # ── Raw SCORM 1.2 runtime fields (stored as received from JS commitData) ──
    lesson_location   = Column(Text)                              # SCO bookmark — stored verbatim
    suspend_data      = Column(Text)                              # opaque SCO save string — never parsed
    lesson_status     = Column(String(32),  default="not attempted")
    score_raw         = Column(String(16))                        # JS field name: score
    score_min         = Column(String(16))                        # JS field name: minscore
    score_max         = Column(String(16))                        # JS field name: maxscore
    total_time        = Column(String(32),  default="0000:00:00.00")
    session_time      = Column(String(32))                        # last session only
    entry             = Column(String(16),  default="ab-initio")
    lesson_mode       = Column(String(16),  default="normal")
    scorm_exit        = Column(String(16))                        # time-out / suspend / logout / ""
    credit            = Column(String(16),  default="credit")
    comments          = Column(Text)                              # learner → LMS comments
    comments_from_lms = Column(Text)                              # LMS → learner comments

    # ── LMS reporting / business fields ──────────────────────────────────────
    progress_percent   = Column(Integer,  default=0)              # 0-100 derived from lesson_status
    first_access_time  = Column(DateTime)                         # first time learner opened the course
    last_accessed_time = Column(DateTime)                         # last commit or finish time
    last_commit_at     = Column(DateTime)
    completed_at       = Column(DateTime)                         # set when status is completed/passed/failed

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    interactions = relationship("ScormInteraction", back_populates="progress", cascade="all, delete-orphan")


class ScormInteraction(Base):
    """
    One row per quiz interaction per progress record.
    Populated from the interactions[] array sent by JS commitData() on commit/finish.
    """

    __tablename__ = "scorm_interactions"

    id                     = Column(Integer, primary_key=True)
    progress_id            = Column(Integer, ForeignKey("scorm_progress.id", ondelete="CASCADE"), nullable=False)
    interaction_index      = Column(Integer, nullable=False)       # position in array (0-based)
    interaction_id         = Column(String(255))                   # cmi.interactions.n.id
    interaction_time       = Column(String(32))                    # HH:MM:SS
    interaction_type       = Column(String(32))                    # true-false / choice / fill-in / etc.
    weighting              = Column(String(16))
    student_response       = Column(Text)
    result                 = Column(String(32))                    # correct / wrong / neutral / etc.
    latency                = Column(String(32))
    correct_responses_json = Column(Text)                          # JSON: [{pattern: "..."}]

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    progress = relationship("ScormProgress", back_populates="interactions")
