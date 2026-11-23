"""Focused tests for the G003 group-membership endpoints (app.routes.groups)
and the group_service helpers they use.

The route handlers are plain Python functions underneath FastAPI's
decorators, so they're called directly here — same lightweight approach as
G002's service tests — against the isolated in-memory SQLite session from
tests/conftest.py. No real MySQL server, CourseAssignment rows, or
notifications are involved. Authorization is tested against the actual
`require_roles` dependency the routes use, not a re-implementation of it.
"""

import json

import pytest
from fastapi import HTTPException

from app.models import Group, GroupMember, User
from app.routes import groups as groups_routes
from app.schemas import GroupMemberBody
from app.security import require_roles
from tests.conftest import make_user


def _add_group(db_session, *, name, created_by=None):
    group = Group(name=name, created_by_id=created_by.id if created_by else None)
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


def _is_member(db_session, group_id, user_id):
    return (
        db_session.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
        is not None
    )


def _member_count(db_session):
    return db_session.query(GroupMember).count()


# ── Case 1: Admin adds learner ──────────────────────────────────────────────

def test_admin_adds_learner(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l1@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)

    result = groups_routes.add_group_member(
        group.id, GroupMemberBody(user_id=learner.id), db=db_session, _=admin
    )

    assert result.status_code == 201
    body = json.loads(result.body)
    assert body["success"] is True
    assert body["data"]["group_id"] == group.id
    assert body["data"]["user_id"] == learner.id
    assert _is_member(db_session, group.id, learner.id)


# ── Case 2: Admin removes learner ───────────────────────────────────────────

def test_admin_removes_learner(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l2@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 2", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()

    result = groups_routes.remove_group_member(group.id, learner.id, db=db_session, _=admin)

    assert result.status_code == 200
    body = json.loads(result.body)
    assert body["success"] is True
    assert not _is_member(db_session, group.id, learner.id)
    # Removing membership must not touch the User or Group rows.
    assert db_session.query(Group).filter(Group.id == group.id).first() is not None
    assert db_session.query(User).filter(User.id == learner.id).first() is not None


# ── Case 3: Duplicate membership ────────────────────────────────────────────

def test_duplicate_membership_is_rejected(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l3@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 3", created_by=admin)

    groups_routes.add_group_member(group.id, GroupMemberBody(user_id=learner.id), db=db_session, _=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.add_group_member(group.id, GroupMemberBody(user_id=learner.id), db=db_session, _=admin)

    assert exc_info.value.status_code == 400
    assert _member_count(db_session) == 1


# ── Case 4: Instructor cannot be added ──────────────────────────────────────

def test_instructor_cannot_be_added_as_member(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i4@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 4", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.add_group_member(group.id, GroupMemberBody(user_id=instructor.id), db=db_session, _=admin)

    assert exc_info.value.status_code == 400
    assert _member_count(db_session) == 0


# ── Case 5: Administrator cannot be added as learner ────────────────────────

def test_administrator_cannot_be_added_as_member(db_session, roles):
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    other_admin = make_user(db_session, roles, email="admin5b@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 5", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.add_group_member(group.id, GroupMemberBody(user_id=other_admin.id), db=db_session, _=admin)

    assert exc_info.value.status_code == 400
    assert _member_count(db_session) == 0


def test_admin_plus_instructor_rejected_but_instructor_plus_learner_allowed(db_session, roles):
    """Multi-role edge cases: presence of the Learner role is what matters,
    not the absence of other roles."""
    admin = make_user(db_session, roles, email="admin5c@test.com", role_names=["Administrator"])
    admin_instructor = make_user(
        db_session, roles, email="ai5@test.com", role_names=["Administrator", "Instructor"]
    )
    instructor_learner = make_user(
        db_session, roles, email="il5@test.com", role_names=["Instructor", "Learner"]
    )
    group = _add_group(db_session, name="Group 5b", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.add_group_member(
            group.id, GroupMemberBody(user_id=admin_instructor.id), db=db_session, _=admin
        )
    assert exc_info.value.status_code == 400

    result = groups_routes.add_group_member(
        group.id, GroupMemberBody(user_id=instructor_learner.id), db=db_session, _=admin
    )
    assert result.status_code == 201
    assert _is_member(db_session, group.id, instructor_learner.id)


# ── Case 6 & 7: Non-admin cannot add/remove (authorization) ─────────────────

def test_non_admin_is_forbidden_by_the_actual_require_roles_dependency(db_session, roles):
    """Both routes use Depends(require_roles("Administrator")) — exercise
    that exact dependency rather than re-implementing the check."""
    instructor = make_user(db_session, roles, email="i6@test.com", role_names=["Instructor"])
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor)
    assert exc_info.value.status_code == 403


# ── Case 8: Missing group ────────────────────────────────────────────────────

def test_add_and_remove_against_missing_group_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin8@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l8@test.com", role_names=["Learner"])

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.add_group_member(999, GroupMemberBody(user_id=learner.id), db=db_session, _=admin)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.remove_group_member(999, learner.id, db=db_session, _=admin)
    assert exc_info.value.status_code == 404


# ── Case 9: Missing user ─────────────────────────────────────────────────────

def test_add_missing_user_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin9@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 9", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.add_group_member(group.id, GroupMemberBody(user_id=999999), db=db_session, _=admin)
    assert exc_info.value.status_code == 404


# ── Case 10: Remove non-member ───────────────────────────────────────────────

def test_remove_non_member_returns_clean_error(db_session, roles):
    admin = make_user(db_session, roles, email="admin10@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l10@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 10", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.remove_group_member(group.id, learner.id, db=db_session, _=admin)
    assert exc_info.value.status_code == 404
