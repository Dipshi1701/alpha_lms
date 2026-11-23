"""Focused tests for G007: expanding a Group -> Course assignment (G006)
into individual, learner-level CourseAssignment rows.

Same lightweight approach as G003/G004/G005/G006: route handlers are
called directly against the isolated in-memory SQLite session from
tests/conftest.py, and authorization is tested against the actual
`require_roles` dependency. Reuses the existing CourseAssignment model —
no second assignment system.
"""

import json
from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.models import (
    Course, CourseAssignment, Group, GroupCourseAssignment, GroupManager, GroupMember,
)
from app.routes import groups as groups_routes
from app.schemas import GroupCourseAssignmentBody
from app.security import require_roles
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


def _assignments_for(db_session, course_id):
    return db_session.query(CourseAssignment).filter(CourseAssignment.course_id == course_id).all()


# ── Basic group assignment ──────────────────────────────────────────────────

def test_group_with_three_learners_creates_three_assignments(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])
    l1 = make_user(db_session, roles, email="l1a@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l2a@test.com", role_names=["Learner"])
    l3 = make_user(db_session, roles, email="l3a@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Frontend Batch", created_by=admin)
    for learner in (l1, l2, l3):
        db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Angular Basics")

    result = groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert result.status_code == 201

    rows = _assignments_for(db_session, course.id)
    assert {r.user_id for r in rows} == {l1.id, l2.id, l3.id}


def test_group_with_one_learner_creates_one_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l2@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course 1")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = _assignments_for(db_session, course.id)
    assert len(rows) == 1
    assert rows[0].user_id == learner.id


def test_empty_group_creates_zero_learner_assignments(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course = _add_course(db_session, title="Course 1")

    result = groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    # The Group -> Course link still succeeds even with zero learners.
    assert result.status_code == 201
    assert db_session.query(GroupCourseAssignment).filter(GroupCourseAssignment.group_id == group.id).count() == 1
    assert _assignments_for(db_session, course.id) == []


def test_missing_group_returns_normal_error(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    course = _add_course(db_session, title="Course 1")

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            999, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 404
    assert _assignments_for(db_session, course.id) == []


def test_missing_course_returns_normal_error(db_session, roles):
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l5@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            group.id, GroupCourseAssignmentBody(course_id=999), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 404
    assert db_session.query(CourseAssignment).count() == 0


# ── Duplicate protection ─────────────────────────────────────────────────────

def test_existing_individual_assignment_then_group_assignment_no_duplicate(db_session, roles):
    admin = make_user(db_session, roles, email="admin6@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l6@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")
    db_session.add(CourseAssignment(course_id=course.id, user_id=learner.id, assigned_by_id=admin.id))
    db_session.commit()

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = _assignments_for(db_session, course.id)
    assert len(rows) == 1
    assert rows[0].user_id == learner.id


def test_group_assignment_then_individual_assignment_no_duplicate(db_session, roles):
    """Reverse order: group assignment creates the row first; a later
    individual-assignment attempt for the same (course, user) must still
    respect the existing CourseAssignment uniqueness rule."""
    admin = make_user(db_session, roles, email="admin7@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l7@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert len(_assignments_for(db_session, course.id)) == 1

    # Simulate an individual-assignment attempt the same way courses.py's
    # assign_course would (pre-check before insert) -- it must see the
    # learner as already assigned and not create a second row.
    already = (
        db_session.query(CourseAssignment)
        .filter(CourseAssignment.course_id == course.id, CourseAssignment.user_id == learner.id)
        .first()
    )
    assert already is not None
    rows = _assignments_for(db_session, course.id)
    assert len(rows) == 1


def test_learner_in_two_groups_assigned_same_course_no_duplicate(db_session, roles):
    admin = make_user(db_session, roles, email="admin8@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l8@test.com", role_names=["Learner"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    db_session.add(GroupMember(group_id=group_a.id, user_id=learner.id))
    db_session.add(GroupMember(group_id=group_b.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group_a.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    groups_routes.assign_group_course(
        group_b.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = _assignments_for(db_session, course.id)
    assert len(rows) == 1
    assert rows[0].user_id == learner.id


def test_repeating_same_group_course_assignment_rejected_no_duplicate(db_session, roles):
    """The group_course_assignments row itself is unique per (group, course)
    -- re-assigning is a clean 400, and no second batch of learner
    CourseAssignment rows is created."""
    admin = make_user(db_session, roles, email="admin9@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l9@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 400
    assert len(_assignments_for(db_session, course.id)) == 1


# ── Roles ────────────────────────────────────────────────────────────────────

def test_instructor_and_administrator_members_do_not_get_assignments(db_session, roles):
    """
    Only users with the Learner role are ever expanded to CourseAssignment.
    An Instructor/Administrator cannot even become a GroupMember via the
    G003 API (it requires the Learner role), but this test directly seeds a
    group_members row for them anyway to prove sync_group_course_assignment_
    to_learners() itself filters by role rather than relying solely on the
    G003 API-level guard.
    """
    admin = make_user(db_session, roles, email="admin10@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i10@test.com", role_names=["Instructor"])
    learner = make_user(db_session, roles, email="l10@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=instructor.id))
    db_session.add(GroupMember(group_id=group.id, user_id=admin.id))
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = _assignments_for(db_session, course.id)
    assert {r.user_id for r in rows} == {learner.id}


def test_only_learner_members_receive_assignments(db_session, roles):
    admin = make_user(db_session, roles, email="admin11@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l11@test.com", role_names=["Learner"])
    instr_learner = make_user(
        db_session, roles, email="il11@test.com", role_names=["Instructor", "Learner"]
    )
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.add(GroupMember(group_id=group.id, user_id=instr_learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = _assignments_for(db_session, course.id)
    # Someone who also holds the Learner role is assigned too -- matches the
    # existing role semantics (Instructor + Learner is still a Learner).
    assert {r.user_id for r in rows} == {learner.id, instr_learner.id}


# ── Membership add/remove ────────────────────────────────────────────────────

def test_removing_learner_from_group_does_not_delete_their_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin12@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l12@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert len(_assignments_for(db_session, course.id)) == 1

    groups_routes.remove_group_member(group.id, learner.id, db=db_session, _=admin)

    assert db_session.query(GroupMember).filter(GroupMember.group_id == group.id).count() == 0
    # The existing CourseAssignment is untouched -- membership and
    # assignment are separate concepts (unchanged G003 behavior).
    assert len(_assignments_for(db_session, course.id)) == 1


def test_learner_added_after_group_course_assignment_receives_it_with_own_assigned_at(db_session, roles):
    """
    SUPERSEDES the previously-deferred behavior from G007/G008: that
    earlier test explicitly documented adding a learner to an
    already-course-assigned group as "DEFERRED BEHAVIOR ... intentionally
    left to a later milestone". G012 PART 7/13 is that later milestone --
    it explicitly requires the learner to now receive the already-assigned
    course, using THEIR OWN join-time as assigned_at (never the original
    GroupCourseAssignment.assigned_at), so their due_date is computed from
    when they actually joined -- e.g. spec's own "Neha" example.
    """
    admin = make_user(db_session, roles, email="admin13@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course = _add_course(db_session, title="Course X")
    assert course.assignment_duration_days == 7  # model default, unchanged here

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert _assignments_for(db_session, course.id) == []

    learner_c = make_user(db_session, roles, email="lc13@test.com", role_names=["Learner"])
    from app.schemas import GroupMemberBody
    groups_routes.add_group_member(group.id, GroupMemberBody(user_id=learner_c.id), db=db_session, _=admin)

    assert db_session.query(GroupMember).filter(GroupMember.group_id == group.id).count() == 1
    rows = _assignments_for(db_session, course.id)
    assert len(rows) == 1
    row = rows[0]
    assert row.user_id == learner_c.id
    assert row.assigned_at is not None
    assert row.due_date == row.assigned_at + timedelta(days=course.assignment_duration_days)

    group_row = (
        db_session.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group.id, GroupCourseAssignment.course_id == course.id)
        .first()
    )
    # The learner's own assigned_at must NOT be the original group
    # assignment's timestamp -- they joined later.
    assert row.assigned_at != group_row.assigned_at


# ── Assignment date ──────────────────────────────────────────────────────────

def test_learner_assignments_use_group_course_assignment_timestamp(db_session, roles):
    admin = make_user(db_session, roles, email="admin14@test.com", role_names=["Administrator"])
    l1 = make_user(db_session, roles, email="l14a@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l14b@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=l1.id))
    db_session.add(GroupMember(group_id=group.id, user_id=l2.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    result = groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    body = json.loads(result.body)
    group_assigned_at = body["data"]["assigned_at"]

    rows = _assignments_for(db_session, course.id)
    assert len(rows) == 2
    for row in rows:
        assert row.assigned_at.isoformat() == group_assigned_at


# ── Authorization ────────────────────────────────────────────────────────────

def test_non_admin_cannot_assign_group_course(db_session, roles):
    instructor = make_user(db_session, roles, email="i15@test.com", role_names=["Instructor"])
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor)
    assert exc_info.value.status_code == 403


def test_scoped_instructor_cannot_assign_group_course_even_if_managed(db_session, roles):
    """Assign/remove Group Course stay Administrator-only per G006 -- a
    scoped Instructor cannot perform this even for a group they manage."""
    admin = make_user(db_session, roles, email="admin16@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i16@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.commit()
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor)
    assert exc_info.value.status_code == 403


def test_g006_list_visibility_still_works(db_session, roles):
    admin = make_user(db_session, roles, email="admin17@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i17@test.com", role_names=["Instructor"])
    managed_group = _add_group(db_session, name="Managed", created_by=admin)
    other_group = _add_group(db_session, name="Other", created_by=admin)
    db_session.add(GroupManager(group_id=managed_group.id, user_id=instructor.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")
    groups_routes.assign_group_course(
        managed_group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    result = groups_routes.list_group_courses(managed_group.id, db=db_session, current_user=instructor)
    body = json.loads(result.body)
    assert len(body["data"]) == 1

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.list_group_courses(other_group.id, db=db_session, current_user=instructor)
    assert exc_info.value.status_code == 403


# ── Data integrity ───────────────────────────────────────────────────────────

def test_group_membership_and_manager_relationships_unchanged(db_session, roles):
    admin = make_user(db_session, roles, email="admin18@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i18@test.com", role_names=["Instructor"])
    learner = make_user(db_session, roles, email="l18@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    assert db_session.query(GroupManager).filter(GroupManager.group_id == group.id).count() == 1
    assert db_session.query(GroupMember).filter(GroupMember.group_id == group.id).count() == 1


def test_course_unchanged_after_group_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin19@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l19@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    refreshed = db_session.query(Course).filter(Course.id == course.id).first()
    assert refreshed.title == "Course X"
    assert refreshed.status == "Draft"


def test_existing_individual_course_assignments_unchanged(db_session, roles):
    """Assigning course_a to a group must not touch an unrelated existing
    individual CourseAssignment for course_b."""
    admin = make_user(db_session, roles, email="admin20@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l20@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course_a = _add_course(db_session, title="Course A")
    course_b = _add_course(db_session, title="Course B")
    db_session.add(CourseAssignment(course_id=course_b.id, user_id=learner.id, assigned_by_id=admin.id))
    db_session.commit()

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course_a.id), db=db_session, current_user=admin
    )

    assert len(_assignments_for(db_session, course_b.id)) == 1
    assert len(_assignments_for(db_session, course_a.id)) == 1


def test_removing_group_course_link_does_not_delete_learner_assignments(db_session, roles):
    admin = make_user(db_session, roles, email="admin21@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l21@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Course X")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    assert len(_assignments_for(db_session, course.id)) == 1

    groups_routes.remove_group_course(group.id, course.id, db=db_session, _=admin)

    assert (
        db_session.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group.id, GroupCourseAssignment.course_id == course.id)
        .first()
        is None
    )
    # The learner-level CourseAssignment created earlier remains intact.
    assert len(_assignments_for(db_session, course.id)) == 1
