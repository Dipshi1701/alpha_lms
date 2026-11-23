"""G008 — regression tests locking in existing assignment-date behavior.

This module is TEST-ONLY. G008's inspection confirmed that no production
code changes were required:

* `CourseAssignment.assigned_at` and `GroupCourseAssignment.assigned_at`
  already exist (added in earlier milestones).
* G007's group_service.sync_group_course_assignment_to_learners() already
  propagates the *same* `assigned_at` from a GroupCourseAssignment event to
  every learner-level CourseAssignment row it creates.
* Existing individual CourseAssignment rows are never overwritten by a
  later group assignment.
* Re-assigning the same (group_id, course_id) pair is already rejected by
  routes.groups.assign_group_course (via group_service.is_group_course_
  assigned), so it cannot reset any dates.
* Removing a learner from a group (group_service.remove_group_member) only
  ever touches the group_members row — it never touches CourseAssignment.

UPDATE (G012): a `due_date` field has now been deliberately added to
`CourseAssignment` (never to `GroupCourseAssignment`, which stays a
group-level relationship only) — see models.py, the G012 migration, and
group_service.compute_due_date. TEST 8 below used to lock in the absence
of any due_date column as a tripwire against an *accidental* addition; it
now locks in the new, deliberate reality instead (due_date exists on
CourseAssignment only) now that G012 has explicitly, intentionally added
it via a real migration and full spec.

This suite calls route handlers directly against the isolated in-memory
SQLite session from tests/conftest.py, the same lightweight approach used
by every other Groups test file (G002-G007) — no production files are
modified by this file.
"""

import json

import pytest
from fastapi import HTTPException

from app.models import Course, CourseAssignment, Group, GroupCourseAssignment, GroupMember
from app.routes import groups as groups_routes
from app.routes.courses import assign_course as individual_assign_course
from app.schemas import AssignCoursesBody, GroupCourseAssignmentBody
from tests.conftest import make_user


def _add_group(db_session, *, name, created_by=None):
    group = Group(name=name, created_by_id=created_by.id if created_by else None)
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


def _add_course(db_session, *, title):
    course = Course(title=title)
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course


def _assignment_for(db_session, *, course_id, user_id):
    return (
        db_session.query(CourseAssignment)
        .filter(CourseAssignment.course_id == course_id, CourseAssignment.user_id == user_id)
        .first()
    )


def _group_course_row(db_session, *, group_id, course_id):
    return (
        db_session.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group_id, GroupCourseAssignment.course_id == course_id)
        .first()
    )


# ═════════════════════════════════════════════════════════════════════════
# TEST 1 — Same assigned_at for a group assignment with multiple learners
# ═════════════════════════════════════════════════════════════════════════

def test_group_assignment_gives_every_learner_the_same_assigned_at(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])
    l1 = make_user(db_session, roles, email="l1a@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l1b@test.com", role_names=["Learner"])
    l3 = make_user(db_session, roles, email="l1c@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    for learner in (l1, l2, l3):
        db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course A")

    result = groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert result.status_code == 201

    group_row = _group_course_row(db_session, group_id=group.id, course_id=course.id)
    assert group_row is not None

    rows = db_session.query(CourseAssignment).filter(CourseAssignment.course_id == course.id).all()
    assert len(rows) == 3
    assert {r.user_id for r in rows} == {l1.id, l2.id, l3.id}
    for row in rows:
        assert row.assigned_at == group_row.assigned_at


# ═════════════════════════════════════════════════════════════════════════
# TEST 2 — Individual assignment date must not be overwritten
# ═════════════════════════════════════════════════════════════════════════

def test_individual_assignment_date_not_overwritten_by_group_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    l1 = make_user(db_session, roles, email="l2@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A")

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[l1.id]), db=db_session, current_user=admin)
    original_row = _assignment_for(db_session, course_id=course.id, user_id=l1.id)
    original_assigned_at = original_row.assigned_at

    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=l1.id))
    db_session.commit()

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = db_session.query(CourseAssignment).filter(
        CourseAssignment.course_id == course.id, CourseAssignment.user_id == l1.id
    ).all()
    assert len(rows) == 1
    assert rows[0].id == original_row.id
    assert rows[0].assigned_at == original_assigned_at


# ═════════════════════════════════════════════════════════════════════════
# TEST 3 — Group assignment creates only missing learner assignments
# ═════════════════════════════════════════════════════════════════════════

def test_group_assignment_creates_only_missing_learner_assignments(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])
    l1 = make_user(db_session, roles, email="l3a@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l3b@test.com", role_names=["Learner"])
    l3 = make_user(db_session, roles, email="l3c@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A")

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[l1.id]), db=db_session, current_user=admin)
    l1_original_row = _assignment_for(db_session, course_id=course.id, user_id=l1.id)
    l1_original_assigned_at = l1_original_row.assigned_at

    group = _add_group(db_session, name="Group 1", created_by=admin)
    for learner in (l1, l2, l3):
        db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = db_session.query(CourseAssignment).filter(CourseAssignment.course_id == course.id).all()
    assert len(rows) == 3

    by_user = {r.user_id: r for r in rows}
    assert set(by_user.keys()) == {l1.id, l2.id, l3.id}

    # L1 keeps the pre-existing row untouched.
    assert by_user[l1.id].id == l1_original_row.id
    assert by_user[l1.id].assigned_at == l1_original_assigned_at
    # L2 and L3 received newly created rows.
    assert by_user[l2.id].id != l1_original_row.id
    assert by_user[l3.id].id != l1_original_row.id

    # No duplicate (course_id, user_id) pairs.
    pairs = [(r.course_id, r.user_id) for r in rows]
    assert len(pairs) == len(set(pairs))


# ═════════════════════════════════════════════════════════════════════════
# TEST 4 — Duplicate group assignment does not reset dates
# ═════════════════════════════════════════════════════════════════════════

def test_duplicate_group_assignment_rejected_and_dates_unchanged(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l4@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course A")

    first_result = groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert first_result.status_code == 201

    group_row = _group_course_row(db_session, group_id=group.id, course_id=course.id)
    original_group_assigned_at = group_row.assigned_at
    original_learner_assigned_at = _assignment_for(
        db_session, course_id=course.id, user_id=learner.id
    ).assigned_at

    # Second attempt at the same (group, course) is rejected per existing G006 behavior.
    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 400

    db_session.refresh(group_row)
    assert group_row.assigned_at == original_group_assigned_at
    assert (
        _assignment_for(db_session, course_id=course.id, user_id=learner.id).assigned_at
        == original_learner_assigned_at
    )
    assert db_session.query(CourseAssignment).filter(CourseAssignment.course_id == course.id).count() == 1
    assert db_session.query(GroupCourseAssignment).filter(GroupCourseAssignment.group_id == group.id).count() == 1


# ═════════════════════════════════════════════════════════════════════════
# TEST 5 — Learner in multiple groups: no duplicate assignment
# ═════════════════════════════════════════════════════════════════════════

def test_learner_in_multiple_groups_does_not_get_duplicate_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l5@test.com", role_names=["Learner"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    db_session.add(GroupMember(group_id=group_a.id, user_id=learner.id))
    db_session.add(GroupMember(group_id=group_b.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course A")

    groups_routes.assign_group_course(
        group_a.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    original_assigned_at = _assignment_for(db_session, course_id=course.id, user_id=learner.id).assigned_at

    # Group B + Course A is a different (group_id, course_id) pair, so the
    # GroupCourseAssignment for Group B is allowed to succeed -- the
    # duplicate protection that matters here is at the learner level.
    result = groups_routes.assign_group_course(
        group_b.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert result.status_code == 201

    rows = db_session.query(CourseAssignment).filter(
        CourseAssignment.course_id == course.id, CourseAssignment.user_id == learner.id
    ).all()
    assert len(rows) == 1
    assert rows[0].assigned_at == original_assigned_at


# ═════════════════════════════════════════════════════════════════════════
# TEST 6 — Learner removed from group: assignment remains
# ═════════════════════════════════════════════════════════════════════════

def test_learner_removed_from_group_keeps_existing_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin6@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l6@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group A", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course A")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    original_row = _assignment_for(db_session, course_id=course.id, user_id=learner.id)
    assert original_row is not None
    original_assigned_at = original_row.assigned_at

    groups_routes.remove_group_member(group.id, learner.id, db=db_session, _=admin)

    assert db_session.query(GroupMember).filter(GroupMember.group_id == group.id).count() == 0
    row_after_removal = _assignment_for(db_session, course_id=course.id, user_id=learner.id)
    assert row_after_removal is not None
    assert row_after_removal.id == original_row.id
    assert row_after_removal.assigned_at == original_assigned_at


# ═════════════════════════════════════════════════════════════════════════
# TEST 7 — Empty group
# ═════════════════════════════════════════════════════════════════════════

def test_empty_group_assignment_succeeds_with_zero_learner_assignments(db_session, roles):
    admin = make_user(db_session, roles, email="admin7@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Empty Group", created_by=admin)
    course = _add_course(db_session, title="Course A")

    result = groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    assert result.status_code == 201
    assert _group_course_row(db_session, group_id=group.id, course_id=course.id) is not None
    assert db_session.query(CourseAssignment).filter(CourseAssignment.course_id == course.id).count() == 0


# ═════════════════════════════════════════════════════════════════════════
# TEST 8 — due-date lives on CourseAssignment only (G012)
# ═════════════════════════════════════════════════════════════════════════
#
# UPDATED for G012: this test used to assert that NO due_date column
# existed anywhere, as a tripwire against an accidental/undocumented
# addition. G012 deliberately adds due_date to CourseAssignment via a real
# migration (see alembic/versions/20260914_0005_...) and a full spec — this
# is exactly the "explicit, deliberate migration/decision" the original
# comment said would justify updating this guard. GroupCourseAssignment
# still intentionally has no due_date column: a due date is a per-learner
# concept, computed from each learner's own CourseAssignment.assigned_at,
# not a per-group one (see group_service.compute_due_date).

def test_due_date_field_exists_on_course_assignment_only():
    assert "due_date" in CourseAssignment.__table__.columns.keys()
    assert "due_date" not in GroupCourseAssignment.__table__.columns.keys()


# ═════════════════════════════════════════════════════════════════════════
# TEST 9 — Individual assignment regression (sanity check; full regression
# is verified by running the complete `pytest tests/ -v` suite)
# ═════════════════════════════════════════════════════════════════════════

def test_individual_assignment_creation_and_authorization_unchanged(db_session, roles):
    admin = make_user(db_session, roles, email="admin9@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l9@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A")

    individual_assign_course(
        course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin
    )
    row = _assignment_for(db_session, course_id=course.id, user_id=learner.id)
    assert row is not None
    assert row.assigned_by_id == admin.id
    assert row.assigned_at is not None
