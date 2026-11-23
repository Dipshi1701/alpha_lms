"""Focused tests for the G005 Group CRUD endpoints (app.routes.groups) and
the group_service helpers they use.

Same lightweight approach as G003/G004: route handlers are called directly
against the isolated in-memory SQLite session from tests/conftest.py, and
authorization is tested against the actual `require_roles` dependency.
"""

import json

import pytest
from fastapi import HTTPException

from app.models import Group, GroupManager, GroupMember, User
from app.routes import groups as groups_routes
from app.schemas import GroupCreate, GroupUpdate
from app.security import require_roles
from tests.conftest import make_user


def _add_group(db_session, *, name, created_by=None):
    group = Group(name=name, created_by_id=created_by.id if created_by else None)
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


# ── Create ───────────────────────────────────────────────────────────────────

def test_admin_creates_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])

    result = groups_routes.create_group(GroupCreate(name="Frontend Team"), db=db_session, current_user=admin)

    assert result.status_code == 201
    body = json.loads(result.body)
    assert body["success"] is True
    assert body["data"]["name"] == "Frontend Team"
    assert body["data"]["created_by_id"] == admin.id

    assert db_session.query(Group).filter(Group.name == "Frontend Team").first() is not None
    # Creating a group must not create any membership/manager rows.
    assert db_session.query(GroupMember).count() == 0
    assert db_session.query(GroupManager).count() == 0


def test_create_group_rejects_duplicate_name(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    _add_group(db_session, name="Frontend Team", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.create_group(GroupCreate(name="Frontend Team"), db=db_session, current_user=admin)

    assert exc_info.value.status_code == 400
    assert db_session.query(Group).filter(Group.name == "Frontend Team").count() == 1


def test_create_group_rejects_whitespace_only_name(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.create_group(GroupCreate(name="   "), db=db_session, current_user=admin)

    assert exc_info.value.status_code == 400
    assert db_session.query(Group).count() == 0


# ── List ─────────────────────────────────────────────────────────────────────

def test_admin_lists_all_groups(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i4@test.com", role_names=["Instructor"])
    group1 = _add_group(db_session, name="Group 1", created_by=admin)
    _add_group(db_session, name="Group 2", created_by=admin)
    db_session.add(GroupManager(group_id=group1.id, user_id=instructor.id))
    db_session.commit()

    result = groups_routes.list_groups(db=db_session, current_user=admin)
    body = json.loads(result.body)
    names = {row["name"] for row in body["data"]}
    assert names == {"Group 1", "Group 2"}


def test_scoped_instructor_only_sees_managed_groups(db_session, roles):
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i5@test.com", role_names=["Instructor"])
    group1 = _add_group(db_session, name="Group 1", created_by=admin)
    group3 = _add_group(db_session, name="Group 3", created_by=admin)
    _add_group(db_session, name="Group 2", created_by=admin)  # not managed
    _add_group(db_session, name="Group 4", created_by=admin)  # not managed
    db_session.add(GroupManager(group_id=group1.id, user_id=instructor.id))
    db_session.add(GroupManager(group_id=group3.id, user_id=instructor.id))
    db_session.commit()

    result = groups_routes.list_groups(db=db_session, current_user=instructor)
    body = json.loads(result.body)
    names = {row["name"] for row in body["data"]}
    assert names == {"Group 1", "Group 3"}


def test_instructor_with_no_managed_groups_sees_empty_list(db_session, roles):
    admin = make_user(db_session, roles, email="admin6@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i6@test.com", role_names=["Instructor"])
    _add_group(db_session, name="Group 1", created_by=admin)

    result = groups_routes.list_groups(db=db_session, current_user=instructor)
    body = json.loads(result.body)
    assert body["data"] == []


def test_admin_plus_instructor_sees_all_groups_not_just_managed(db_session, roles):
    """The Administrator role always wins — mirrors is_scoped_manager()."""
    admin_instructor = make_user(
        db_session, roles, email="ai7@test.com", role_names=["Administrator", "Instructor"]
    )
    _add_group(db_session, name="Group 1", created_by=admin_instructor)
    _add_group(db_session, name="Group 2", created_by=admin_instructor)

    result = groups_routes.list_groups(db=db_session, current_user=admin_instructor)
    body = json.loads(result.body)
    assert len(body["data"]) == 2


# ── Get ──────────────────────────────────────────────────────────────────────

def test_admin_can_get_any_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin8@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)

    result = groups_routes.get_group(group.id, db=db_session, current_user=admin)
    body = json.loads(result.body)
    assert body["data"]["id"] == group.id


def test_scoped_instructor_can_get_managed_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin9@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i9@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.commit()

    result = groups_routes.get_group(group.id, db=db_session, current_user=instructor)
    body = json.loads(result.body)
    assert body["data"]["id"] == group.id


def test_scoped_instructor_cannot_get_unmanaged_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin10@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i10@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.get_group(group.id, db=db_session, current_user=instructor)
    assert exc_info.value.status_code == 403


def test_get_missing_group_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin11@test.com", role_names=["Administrator"])

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.get_group(999, db=db_session, current_user=admin)
    assert exc_info.value.status_code == 404


# ── Update ───────────────────────────────────────────────────────────────────

def test_admin_updates_group_name(db_session, roles):
    admin = make_user(db_session, roles, email="admin12@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Old Name", created_by=admin)

    result = groups_routes.update_group(group.id, GroupUpdate(name="New Name"), db=db_session, _=admin)
    body = json.loads(result.body)
    assert body["data"]["name"] == "New Name"
    db_session.refresh(group)
    assert group.name == "New Name"


def test_update_group_rejects_duplicate_name(db_session, roles):
    admin = make_user(db_session, roles, email="admin13@test.com", role_names=["Administrator"])
    _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.update_group(group_b.id, GroupUpdate(name="Group A"), db=db_session, _=admin)
    assert exc_info.value.status_code == 400


def test_update_missing_group_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin14@test.com", role_names=["Administrator"])

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.update_group(999, GroupUpdate(name="X"), db=db_session, _=admin)
    assert exc_info.value.status_code == 404


# ── Delete ───────────────────────────────────────────────────────────────────

def test_admin_deletes_group_and_cascades_membership_and_manager_rows(db_session, roles):
    admin = make_user(db_session, roles, email="admin15@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i15@test.com", role_names=["Instructor"])
    learner = make_user(db_session, roles, email="l15@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()

    result = groups_routes.delete_group(group.id, db=db_session, _=admin)
    body = json.loads(result.body)
    assert body["success"] is True

    assert db_session.query(Group).filter(Group.id == group.id).first() is None
    assert db_session.query(GroupManager).filter(GroupManager.group_id == group.id).count() == 0
    assert db_session.query(GroupMember).filter(GroupMember.group_id == group.id).count() == 0
    # Users themselves must remain completely untouched.
    assert db_session.query(User).filter(User.id == instructor.id).first() is not None
    assert db_session.query(User).filter(User.id == learner.id).first() is not None


def test_delete_missing_group_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin16@test.com", role_names=["Administrator"])

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.delete_group(999, db=db_session, _=admin)
    assert exc_info.value.status_code == 404


# ── Authorization ────────────────────────────────────────────────────────────

def test_non_admin_is_forbidden_for_mutations(db_session, roles):
    """Create/Update/Delete use Depends(require_roles("Administrator"))."""
    instructor = make_user(db_session, roles, email="i17@test.com", role_names=["Instructor"])
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor)
    assert exc_info.value.status_code == 403


def test_learner_is_forbidden_for_list_and_get(db_session, roles):
    """List/Get use Depends(require_roles("Administrator", "Instructor"))."""
    learner = make_user(db_session, roles, email="l17@test.com", role_names=["Learner"])
    checker = require_roles("Administrator", "Instructor")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=learner)
    assert exc_info.value.status_code == 403
