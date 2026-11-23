"""Unit tests for app.services.group_service (G002).

Uses the isolated in-memory SQLite session from tests/conftest.py — no real
MySQL server, CourseAssignment rows, or notifications are involved.
"""

from app.models import Group, GroupManager, GroupMember
from app.services import group_service as gs
from tests.conftest import make_user


def _add_group(db_session, *, name, created_by=None):
    group = Group(name=name, created_by_id=created_by.id if created_by else None)
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


def _add_member(db_session, group, user):
    db_session.add(GroupMember(group_id=group.id, user_id=user.id))
    db_session.commit()


def _add_manager(db_session, group, user):
    db_session.add(GroupManager(group_id=group.id, user_id=user.id))
    db_session.commit()


# ── Case 1: Instructor manages no groups ────────────────────────────────────

def test_instructor_manages_no_groups(db_session, roles):
    instructor = make_user(db_session, roles, email="i1@test.com", role_names=["Instructor"])

    assert gs.get_managed_group_ids(db_session, instructor) == []
    assert gs.get_managed_learner_ids(db_session, instructor) == set()


# ── Case 2: Instructor manages one group with 3 learners ───────────────────

def test_instructor_manages_one_group_with_three_learners(db_session, roles):
    instructor = make_user(db_session, roles, email="i2@test.com", role_names=["Instructor"])
    learners = [
        make_user(db_session, roles, email=f"l2-{i}@test.com", role_names=["Learner"])
        for i in range(3)
    ]
    group = _add_group(db_session, name="Group A", created_by=instructor)
    _add_manager(db_session, group, instructor)
    for learner in learners:
        _add_member(db_session, group, learner)

    assert gs.get_managed_group_ids(db_session, instructor) == [group.id]
    assert gs.get_managed_learner_ids(db_session, instructor) == {l.id for l in learners}


# ── Case 3: Instructor manages two groups with overlapping learners ────────

def test_instructor_manages_two_groups_with_overlap(db_session, roles):
    instructor = make_user(db_session, roles, email="i3@test.com", role_names=["Instructor"])
    l1 = make_user(db_session, roles, email="l3-1@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l3-2@test.com", role_names=["Learner"])
    l3 = make_user(db_session, roles, email="l3-3@test.com", role_names=["Learner"])

    group1 = _add_group(db_session, name="Group 1", created_by=instructor)
    group2 = _add_group(db_session, name="Group 2", created_by=instructor)
    _add_manager(db_session, group1, instructor)
    _add_manager(db_session, group2, instructor)
    _add_member(db_session, group1, l1)
    _add_member(db_session, group1, l2)
    _add_member(db_session, group2, l2)
    _add_member(db_session, group2, l3)

    assert set(gs.get_managed_group_ids(db_session, instructor)) == {group1.id, group2.id}
    assert gs.get_managed_learner_ids(db_session, instructor) == {l1.id, l2.id, l3.id}
    # expand_group_ids should give the same result directly from the group ids
    assert gs.expand_group_ids(db_session, [group1.id, group2.id]) == {l1.id, l2.id, l3.id}


# ── Case 4: Learner manages nothing ─────────────────────────────────────────

def test_learner_manages_nothing(db_session, roles):
    learner = make_user(db_session, roles, email="l4@test.com", role_names=["Learner"])

    assert gs.get_managed_group_ids(db_session, learner) == []
    assert gs.get_managed_learner_ids(db_session, learner) == set()
    assert gs.is_scoped_manager(learner) is False


# ── Case 5: Administrator ───────────────────────────────────────────────────

def test_administrator_lookup_is_literal_not_synthesized(db_session, roles):
    """
    Administrators are not implicitly added to group_managers. Consistent
    with the rest of the codebase (e.g. list_courses ignores CourseAssignment
    for Administrators and just returns every course), unrestricted
    visibility for Administrators is a caller-side concern, not something
    this lookup fabricates. So with no explicit group_managers row, an
    Administrator's own managed-group lookup is legitimately empty — same as
    any other user with no rows.
    """
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])

    assert gs.get_managed_group_ids(db_session, admin) == []
    assert gs.get_managed_learner_ids(db_session, admin) == set()
    assert gs.is_scoped_manager(admin) is False

    # If an Administrator is explicitly added as a group manager (nothing
    # stops it at the DB level), the lookup honestly reflects that too.
    learner = make_user(db_session, roles, email="l5@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Admin Group", created_by=admin)
    _add_manager(db_session, group, admin)
    _add_member(db_session, group, learner)

    assert gs.get_managed_group_ids(db_session, admin) == [group.id]
    assert gs.get_managed_learner_ids(db_session, admin) == {learner.id}
    # is_scoped_manager is still False — the Administrator role always wins.
    assert gs.is_scoped_manager(admin) is False


# ── Case 6: is_scoped_manager role combinations ─────────────────────────────

def test_is_scoped_manager_role_combinations(db_session, roles):
    instructor_only = make_user(db_session, roles, email="i6a@test.com", role_names=["Instructor"])
    admin_only = make_user(db_session, roles, email="i6b@test.com", role_names=["Administrator"])
    admin_and_instructor = make_user(
        db_session, roles, email="i6c@test.com", role_names=["Administrator", "Instructor"]
    )
    learner_only = make_user(db_session, roles, email="i6d@test.com", role_names=["Learner"])

    assert gs.is_scoped_manager(instructor_only) is True
    assert gs.is_scoped_manager(admin_only) is False
    assert gs.is_scoped_manager(admin_and_instructor) is False
    assert gs.is_scoped_manager(learner_only) is False


# ── Extra: expand_group_ids only returns Learners, and is empty-safe ───────

def test_expand_group_ids_excludes_non_learners_and_is_empty_safe(db_session, roles):
    instructor = make_user(db_session, roles, email="i7@test.com", role_names=["Instructor"])
    learner = make_user(db_session, roles, email="l7@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group X", created_by=instructor)
    _add_member(db_session, group, learner)
    _add_member(db_session, group, instructor)  # not a Learner — must be excluded

    assert gs.expand_group_ids(db_session, [group.id]) == {learner.id}
    assert gs.expand_group_ids(db_session, []) == set()
