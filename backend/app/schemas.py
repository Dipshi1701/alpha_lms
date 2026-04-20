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


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=100)
    code: Optional[str] = None
    price: Optional[str] = None
    status: Optional[str] = None


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    category: str
    code: Optional[str]
    price: Optional[str]
    status: str
    content_type: str
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
