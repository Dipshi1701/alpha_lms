from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey,
    Integer, String, Table, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

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
    """Stores SCORM 1.2 runtime progress per user per course. One row per user+course pair."""

    __tablename__ = "scorm_progress"
    __table_args__ = (UniqueConstraint("course_id", "user_id"),)

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Core SCORM 1.2 fields
    lesson_location = Column(String(1024))       # Where the learner left off
    suspend_data = Column(Text)                  # Arbitrary SCO-saved state (can be long)
    lesson_status = Column(String(32), default="not attempted")  # not attempted / incomplete / completed / passed / failed
    score_raw = Column(String(16))               # Score as returned by SCO
    session_time = Column(String(16))            # Time spent in last session
    total_time = Column(String(16))              # Accumulated total time

    # Progress summary (0-100) computed from lesson_status
    progress_percent = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_commit_at = Column(DateTime)            # When LMSCommit was last called
    completed_at = Column(DateTime)              # When status reached completed/passed/failed
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
