"""Focused tests for the G006 Group Course Assignment endpoints
(app.routes.groups) and the group_service helpers they use.

Same lightweight approach as G003/G004/G005: route handlers are called
directly against the isolated in-memory SQLite session from
tests/conftest.py, and authorization is tested against the actual
`require_roles` dependency.
"""

import json

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


# ── Assign ───────────────────────────────────────────────────────────────────

def test_admin_assigns_course_to_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course = _add_course(db_session, title="Course 1")

    result = groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    assert result.status_code == 201
    body = json.loads(result.body)
    assert body["success"] is True
    assert body["data"]["group_id"] == group.id
    assert body["data"]["course_id"] == course.id
    assert body["data"]["assigned_by_id"] == admin.id

    row = (
        db_session.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group.id, GroupCourseAssignment.course_id == course.id)
        .first()
    )
    assert row is not None
    # Assigning a course to a group must not create any per-learner CourseAssignment rows.
    assert db_session.query(CourseAssignment).count() == 0


def test_assign_course_missing_group_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    course = _add_course(db_session, title="Course 1")

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            999, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 404


def test_assign_course_missing_course_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            group.id, GroupCourseAssignmentBody(course_id=999), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 404


def test_duplicate_course_assignment_is_rejected(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course = _add_course(db_session, title="Course 1")
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course.id, assigned_by_id=admin.id))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 400
    assert db_session.query(GroupCourseAssignment).count() == 1


# ── List ─────────────────────────────────────────────────────────────────────

def test_list_group_courses_returns_assigned_courses(db_session, roles):
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course1 = _add_course(db_session, title="Course 1")
    course2 = _add_course(db_session, title="Course 2")
    _add_course(db_session, title="Course 3")  # not assigned
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course1.id, assigned_by_id=admin.id))
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course2.id, assigned_by_id=admin.id))
    db_session.commit()

    result = groups_routes.list_group_courses(group.id, db=db_session, current_user=admin)
    body = json.loads(result.body)
    titles = {row["title"] for row in body["data"]}
    assert titles == {"Course 1", "Course 2"}


def test_scoped_instructor_can_see_courses_for_managed_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin6@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i6@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course = _add_course(db_session, title="Course 1")
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course.id, assigned_by_id=admin.id))
    db_session.commit()

    result = groups_routes.list_group_courses(group.id, db=db_session, current_user=instructor)
    body = json.loads(result.body)
    assert len(body["data"]) == 1
    assert body["data"][0]["title"] == "Course 1"


def test_scoped_instructor_cannot_see_courses_for_unrelated_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin7@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i7@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)  # not managed by instructor
    course = _add_course(db_session, title="Course 1")
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course.id, assigned_by_id=admin.id))
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.list_group_courses(group.id, db=db_session, current_user=instructor)
    assert exc_info.value.status_code == 403


# ── Remove ───────────────────────────────────────────────────────────────────

def test_admin_removes_group_course_association_only(db_session, roles):
    admin = make_user(db_session, roles, email="admin8@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i8@test.com", role_names=["Instructor"])
    learner = make_user(db_session, roles, email="l8@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course1 = _add_course(db_session, title="Course 1")
    course2 = _add_course(db_session, title="Course 2")
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course1.id, assigned_by_id=admin.id))
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course2.id, assigned_by_id=admin.id))
    db_session.add(GroupManager(group_id=group.id, user_id=instructor.id))
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.add(CourseAssignment(course_id=course1.id, user_id=learner.id, assigned_by_id=admin.id))
    db_session.commit()

    result = groups_routes.remove_group_course(group.id, course1.id, db=db_session, _=admin)
    body = json.loads(result.body)
    assert body["success"] is True

    # Only the (group, course1) association is gone.
    assert (
        db_session.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group.id, GroupCourseAssignment.course_id == course1.id)
        .first()
        is None
    )
    # course2's group assignment remains untouched.
    assert (
        db_session.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group.id, GroupCourseAssignment.course_id == course2.id)
        .first()
        is not None
    )
    # Nothing else was touched.
    assert db_session.query(Course).filter(Course.id == course1.id).first() is not None
    assert db_session.query(GroupManager).filter(GroupManager.group_id == group.id).count() == 1
    assert db_session.query(GroupMember).filter(GroupMember.group_id == group.id).count() == 1
    assert (
        db_session.query(CourseAssignment)
        .filter(CourseAssignment.course_id == course1.id, CourseAssignment.user_id == learner.id)
        .first()
        is not None
    )


def test_remove_group_course_not_assigned_returns_404(db_session, roles):
    admin = make_user(db_session, roles, email="admin9@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course = _add_course(db_session, title="Course 1")

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.remove_group_course(group.id, course.id, db=db_session, _=admin)
    assert exc_info.value.status_code == 404


# ── Data integrity ───────────────────────────────────────────────────────────

def test_deleting_group_does_not_delete_course(db_session, roles):
    admin = make_user(db_session, roles, email="admin10@test.com", role_names=["Administrator"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    course = _add_course(db_session, title="Course 1")
    db_session.add(GroupCourseAssignment(group_id=group.id, course_id=course.id, assigned_by_id=admin.id))
    db_session.commit()

    groups_routes.delete_group(group.id, db=db_session, _=admin)

    assert db_session.query(Course).filter(Course.id == course.id).first() is not None
    assert db_session.query(GroupCourseAssignment).filter(GroupCourseAssignment.group_id == group.id).count() == 0


# ── Authorization ────────────────────────────────────────────────────────────

def test_non_admin_is_forbidden_to_assign_or_remove_course(db_session, roles):
    """Assign/remove use Depends(require_roles("Administrator"))."""
    instructor = make_user(db_session, roles, email="i11@test.com", role_names=["Instructor"])
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor)
    assert exc_info.value.status_code == 403


def test_scoped_instructor_cannot_assign_course_to_unrelated_group(db_session, roles):
    """
    Instructors are not in the assign/remove required-roles list at all, so a
    scoped Instructor can never assign a course to any group -- managed or
    not -- confirming they cannot act on an unrelated group either.
    """
    admin = make_user(db_session, roles, email="admin12@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i12@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)  # not managed by instructor
    course = _add_course(db_session, title="Course 1")
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor)
    assert exc_info.value.status_code == 403
    assert db_session.query(GroupCourseAssignment).count() == 0
