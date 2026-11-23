"""Shared pytest fixtures for backend tests.

The repository has no established DB test fixtures yet (test_auth.py /
test_users.py are placeholder files). This conftest adds the minimum needed
to unit-test services against an isolated database: a fresh in-memory
SQLite session per test (built from the app's real SQLAlchemy models), plus
a small helper for creating role-bearing users. It never touches the real
DATABASE_URL / MySQL configured in .env.
"""

import os

# Populate config.py's required env vars before app.config is imported by
# anything under app/, in case no .env is present when tests run.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("APP_NAME", "LMS API Test")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.com")
os.environ.setdefault("ADMIN_PASSWORD", "admin123")
os.environ.setdefault("SCORM_STORAGE_PATH", "storage/scorm")
os.environ.setdefault("SCORM_MAX_ZIP_BYTES", "157286400")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Role, User


@pytest.fixture()
def db_session():
    """A fresh in-memory SQLite session with all tables created, per test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def roles(db_session):
    """Create the three standard roles and return them keyed by name."""
    role_map = {}
    for name in ("Administrator", "Instructor", "Learner"):
        role = Role(name=name)
        db_session.add(role)
        role_map[name] = role
    db_session.commit()
    return role_map


def make_user(db_session, roles, *, email, role_names, full_name=None):
    """Test helper: create a User with the given role name(s) attached."""
    user = User(
        email=email,
        hashed_password="x",
        full_name=full_name or email,
        is_active=True,
    )
    for name in role_names:
        user.roles.append(roles[name])
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user
