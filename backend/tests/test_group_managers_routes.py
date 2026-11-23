"""Focused tests for the G004 group-manager endpoints (app.routes.groups)
and the group_service helpers they use.

Same lightweight approach as G003's test_groups_routes.py: route handlers
are called directly (bypassing the HTTP/dependency-injection layer) against
the isolated in-memory SQLite session from tests/conftest.py, and
authorization is tested against the actual `require_roles` dependency.
"""

import json

import pytest
from fastapi import HTTPException

from app.models import Group, GroupManager, GroupMember, User
from app.routes import groups as groups_routes
from app.schemas import GroupManagerBody
from app.security import require_roles
from app.services import group_service as gs
from tests.conftest import make_user


def _add_group(db_session, *, name, created_by=None):
    group = Group(name=name, created_by_id=created_by.id if created_by else None)
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


def _is_manager(db_session, group_id, user_id):
    return (
        db_session.query(GroupManager)
        .filter(GroupManager.group_id == group_id, GroupManager.user_id == user_id)
        .first()
        is not None
    )


def _manager_count(db_session):
    return db_session.query(GroupManager).count()


# ── Case 1: Admin assigns Instructor ────────────────────────────────────────

def test_admin_assigns_instructor_as_manager(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i1@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)

    result = groups_routes.assign_group_manager(
        group.id, GroupManagerBody(user_id=instructor.id), db=db_session, _=admin
    )

    assert result.status_code == 201
    body = json.loads(result.body)
    assert body["success"] is True
    assert body["data"]["group_id"] == group.id
    assert body["data"]["user_id"] == instructor.id
    assert _is_manager(db_session, group.id, instructor.id)


# ── Case 2: Admin removes Instructor manager ────────────────────────────────

def test_admin_removes_instructor_manager(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i2@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 2", created_by=admin)
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.commit()

    result = groups_routes.remove_group_manager(group.id, instructor.id, db=db_session, _=admin)

    assert result.status_code == 200
    body = json.loads(result.body)
    assert body["success"] is True
    assert not _is_manager(db_session, group.id, instructor.id)
    # Instructor and Group must remain intact.
    assert db_session.query(User).filter(User.id == instructor.id).first() is not None
    assert db_session.query(Group).filter(Group.id == group.id).first() is not None


# ── Case 3: Learner cannot become manager ───────────────────────────────────

def test_learner_cannot_become_manager(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l3@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 3", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_manager(group.id, GroupManagerBody(user_id=learner.id), db=db_session, _=admin)

    assert exc_info.value.status_code == 400
    assert _manager_count(db_session) == 0


# ── Case 4: Administrator cannot become manager ─────────────────────────────

def test_administrator_cannot_become_manager(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    other_admin = make_user(db_session, roles, email="admin4b@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 4", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_manager(
            group.id, GroupManagerBody(user_id=other_admin.id), db=db_session, _=admin
        )

    assert exc_info.value.status_code == 400
    assert _manager_count(db_session) == 0


def test_admin_plus_instructor_allowed_but_admin_only_rejected(db_session, roles):
    """Multi-role edge case: presence of the Instructor role is what
    matters, regardless of whether Administrator is also present."""
    admin = make_user(db_session, roles, email="admin4c@test.com", role_names=["Administrator"])
    admin_instructor = make_user(
        db_session, roles, email="ai4@test.com", role_names=["Administrator", "Instructor"]
    )
    group = _add_group(db_session, name="Group 4b", created_by=admin)

    result = groups_routes.assign_group_manager(
        group.id, GroupManagerBody(user_id=admin_instructor.id), db=db_session, _=admin
    )
    assert result.status_code == 201
    assert _is_manager(db_session, group.id, admin_instructor.id)


# ── Case 5: Duplicate manager assignment ────────────────────────────────────

def test_duplicate_manager_assignment_is_rejected(db_session, roles):
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i5@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 5", created_by=admin)

    groups_routes.assign_group_manager(group.id, GroupManagerBody(user_id=instructor.id), db=db_session, _=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_manager(
            group.id, GroupManagerBody(user_id=instructor.id), db=db_session, _=admin
        )

    assert exc_info.value.status_code == 400
    assert _manager_count(db_session) == 1


# ── Case 6: Multiple groups for one Instructor ──────────────────────────────

def test_instructor_can_manage_multiple_groups(db_session, roles):
    admin = make_user(db_session, roles, email="admin6@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i6@test.com", role_names=["Instructor"])
    group1 = _add_group(db_session, name="Group 6-1", created_by=admin)
    group2 = _add_group(db_session, name="Group 6-2", created_by=admin)
    group3 = _add_group(db_session, name="Group 6-3", created_by=admin)

    for group in (group1, group2, group3):
        result = groups_routes.assign_group_manager(
            group.id, GroupManagerBody(user_id=instructor.id), db=db_session, _=admin
        )
        assert result.status_code == 201

    assert set(gs.get_managed_group_ids(db_session, instructor)) == {group1.id, group2.id, group3.id}


# ── Case 7: Multiple managers for one group ─────────────────────────────────

def test_group_can_have_multiple_managers(db_session, roles):
    admin = make_user(db_session, roles, email="admin7@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia7@test.com", role_names=["Instructor"])
    instructor_b = make_user(db_session, roles, email="ib7@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 7", created_by=admin)

    groups_routes.assign_group_manager(group.id, GroupManagerBody(user_id=instructor_a.id), db=db_session, _=admin)
    groups_routes.assign_group_manager(group.id, GroupManagerBody(user_id=instructor_b.id), db=db_session, _=admin)

    assert _is_manager(db_session, group.id, instructor_a.id)
    assert _is_manager(db_session, group.id, instructor_b.id)
    assert _manager_count(db_session) == 2


# ── Case 8 & 9: Non-admin cannot assign/remove (authorization) ─────────────

def test_non_admin_is_forbidden_by_the_actual_require_roles_dependency(db_session, roles):
    """Both routes use Depends(require_roles("Administrator")) — exercise
    that exact dependency rather than re-implementing the check."""
    instructor = make_user(db_session, roles, email="i8@test.com", role_names=["Instructor"])
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor)
    assert exc_info.value.status_code == 403


# ── Case 10: Missing group ───────────────────────────────────────────────────

def test_assign_and_remove_against_missing_group_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin10@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i10@test.com", role_names=["Instructor"])

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_manager(999, GroupManagerBody(user_id=instructor.id), db=db_session, _=admin)
    assert exc_info.value.status_code == 404

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.remove_group_manager(999, instructor.id, db=db_session, _=admin)
    assert exc_info.value.status_code == 404


# ── Case 11: Missing user ────────────────────────────────────────────────────

def test_assign_missing_user_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin11@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 11", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_manager(group.id, GroupManagerBody(user_id=999999), db=db_session, _=admin)
    assert exc_info.value.status_code == 404


# ── Case 12: Removing manager does not remove membership ────────────────────

def test_removing_manager_does_not_remove_group_membership(db_session, roles):
    """An Instructor+Learner user can legitimately be both a manager and a
    member of the same group (G003 only requires the Learner role to be a
    member; G004 only requires the Instructor role to be a manager — the
    schema does not prevent holding both at once). Removing the manager
    assignment must leave the independent membership row untouched.
    """
    admin = make_user(db_session, roles, email="admin12@test.com", role_names=["Administrator"])
    instructor_learner = make_user(
        db_session, roles, email="il12@test.com", role_names=["Instructor", "Learner"]
    )
    group = _add_group(db_session, name="Group 12", created_by=admin)

    groups_routes.assign_group_manager(
        group.id, GroupManagerBody(user_id=instructor_learner.id), db=db_session, _=admin
    )
    db_session.add(GroupMember(group_id=group.id, user_id=instructor_learner.id))
    db_session.commit()

    result = groups_routes.remove_group_manager(group.id, instructor_learner.id, db=db_session, _=admin)

    assert result.status_code == 200
    assert not _is_manager(db_session, group.id, instructor_learner.id)
    # The independent GroupMember row must survive.
    assert (
        db_session.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == instructor_learner.id)
        .first()
        is not None
    )


# ── Case 10 (removal side): missing manager assignment ──────────────────────

def test_remove_non_manager_returns_clean_error(db_session, roles):
    admin = make_user(db_session, roles, email="admin13@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i13@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 13", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.remove_group_manager(group.id, instructor.id, db=db_session, _=admin)
    assert exc_info.value.status_code == 404
