"""G009 — Scoped Group Access & Authorization regression/IDOR tests.

G009's inspection found NO backend authorization gap requiring a code
change. Every endpoint that grants Instructor access to group data already
enforces scoping via the existing helpers from G002/G005:

* group_service.is_scoped_manager(user)     -- Instructor AND NOT Administrator
* group_service.get_managed_group_ids(db, u) -- literal group_managers lookup
* group_service.can_view_group(db, u, gid)   -- the two combined

Concretely:

* GET  /api/groups                  (list_groups)       -- scoped
* GET  /api/groups/{group_id}       (get_group)          -- scoped (403 if
  the group exists but isn't managed by this Instructor -- the existing
  project convention already used by get_group/list_group_courses)
* GET  /api/groups/{group_id}/courses (list_group_courses) -- scoped

Every OTHER group-related endpoint (create/update/delete group, add/remove
member, assign/remove manager, assign/remove group course) is
Administrator-only (Depends(require_roles("Administrator"))), so an
Instructor -- scoped or not, and regardless of which group_id is supplied
-- cannot reach them at all. There is no "member list" or "manager list"
GET endpoint in the API at all, so there is nothing to leak there beyond
what require_roles already blocks.

This file is a dedicated regression suite that locks in and proves all of
the above, including IDOR-style direct-group-ID access attempts. It does
not add a Manager role, does not touch ROLE_NAMES/security.py, and does
not change any G001-G008 production behavior.

Two things were deliberately NOT changed and are called out explicitly in
the final report rather than silently left alone:

1. `GET /api/courses` (courses.list_courses) gives Administrator+Instructor
   unrestricted visibility into every course and its global
   `assigned_user_ids`. This is a pre-existing, Groups-independent design
   of the base Course-management feature (predates any Group/GroupManager
   concept) -- not a gap introduced by or specific to Groups, so "fixing"
   it would be an out-of-scope refactor of unrelated Course permissions.
2. `list_group_courses`'s response reuses `courses.course_to_response`,
   which embeds each course's global `assigned_user_ids` (not filtered to
   the group's own members). Since that exact same global list is already
   visible to any Instructor via `GET /api/courses` today, scoping it only
   within the Group view would not add real protection and would require
   touching shared G006 response-building code -- left unchanged per "do
   not change G006 business logic unnecessarily".
"""

import json

import pytest
from fastapi import HTTPException

from app.models import Course, Group, GroupCourseAssignment, GroupManager, GroupMember
from app.routes import groups as groups_routes
from app.routes.courses import assign_course as individual_assign_course
from app.schemas import AssignCoursesBody, GroupCourseAssignmentBody
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


def _manage(db_session, *, group_id, user_id):
    db_session.add(GroupManager(group_id=group_id, user_id=user_id))
    db_session.commit()


def _member(db_session, *, group_id, user_id):
    db_session.add(GroupMember(group_id=group_id, user_id=user_id))
    db_session.commit()


# ═══════════════════════════════════════════════════════════════════════════
# 1-3. Administrator: unrestricted list/get access
# ═══════════════════════════════════════════════════════════════════════════

def test_admin_can_list_all_groups(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)

    result = groups_routes.list_groups(db=db_session, current_user=admin)
    names = {row["name"] for row in json.loads(result.body)["data"]}
    assert {group_a.name, group_b.name} <= names


def test_admin_can_access_group_a(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)

    result = groups_routes.get_group(group_a.id, db=db_session, current_user=admin)
    assert json.loads(result.body)["data"]["id"] == group_a.id


def test_admin_can_access_group_b(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])
    group_b = _add_group(db_session, name="Group B", created_by=admin)

    result = groups_routes.get_group(group_b.id, db=db_session, current_user=admin)
    assert json.loads(result.body)["data"]["id"] == group_b.id


# ═══════════════════════════════════════════════════════════════════════════
# 4-6. Instructor A manages Group A: can access A, cannot access B
# ═══════════════════════════════════════════════════════════════════════════

def test_instructor_a_can_access_managed_group_a(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia4@test.com", role_names=["Instructor"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)

    result = groups_routes.get_group(group_a.id, db=db_session, current_user=instructor_a)
    assert json.loads(result.body)["data"]["id"] == group_a.id


def test_instructor_a_cannot_access_unmanaged_group_b(db_session, roles):
    """Direct group-ID (IDOR-style) access attempt: Group B exists, but
    Instructor A does not manage it."""
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia5@test.com", role_names=["Instructor"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.get_group(group_b.id, db=db_session, current_user=instructor_a)
    assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 7-8. Instructor B manages Group B: can access B, cannot access A
# ═══════════════════════════════════════════════════════════════════════════

def test_instructor_b_manages_group_b(db_session, roles):
    admin = make_user(db_session, roles, email="admin6@test.com", role_names=["Administrator"])
    instructor_b = make_user(db_session, roles, email="ib6@test.com", role_names=["Instructor"])
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    _manage(db_session, group_id=group_b.id, user_id=instructor_b.id)

    result = groups_routes.get_group(group_b.id, db=db_session, current_user=instructor_b)
    assert json.loads(result.body)["data"]["id"] == group_b.id


def test_instructor_b_cannot_access_group_a(db_session, roles):
    admin = make_user(db_session, roles, email="admin7@test.com", role_names=["Administrator"])
    instructor_b = make_user(db_session, roles, email="ib7@test.com", role_names=["Instructor"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    _manage(db_session, group_id=group_b.id, user_id=instructor_b.id)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.get_group(group_a.id, db=db_session, current_user=instructor_b)
    assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 9. Instructor with no managed groups cannot access any group data
# ═══════════════════════════════════════════════════════════════════════════

def test_instructor_with_no_managed_groups_cannot_access_any_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin8@test.com", role_names=["Administrator"])
    instructor = make_user(db_session, roles, email="i8@test.com", role_names=["Instructor"])
    group = _add_group(db_session, name="Group 1", created_by=admin)

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.get_group(group.id, db=db_session, current_user=instructor)
    assert exc_info.value.status_code == 403

    result = groups_routes.list_groups(db=db_session, current_user=instructor)
    assert json.loads(result.body)["data"] == []


# ═══════════════════════════════════════════════════════════════════════════
# 10. Instructor cannot retrieve/mutate unrelated group members
#     (there is no member-listing GET endpoint at all; membership mutation
#     is Administrator-only, so an Instructor cannot touch it for ANY
#     group_id -- including a group they themselves manage)
# ═══════════════════════════════════════════════════════════════════════════

def test_instructor_cannot_add_or_remove_members_even_for_managed_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin9@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia9@test.com", role_names=["Instructor"])
    learner = make_user(db_session, roles, email="l9@test.com", role_names=["Learner"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor_a)
    assert exc_info.value.status_code == 403
    assert db_session.query(GroupMember).filter(GroupMember.group_id == group_a.id).count() == 0


def test_instructor_cannot_retrieve_unrelated_group_members_via_unmanaged_group_id(db_session, roles):
    """No GET endpoint exposes group_members at all. The member-mutation
    endpoints use Depends(require_roles("Administrator")), which is a
    blanket role check that runs before any group_id is even looked at --
    so it blocks Instructor A identically whether group_b is managed by
    them or not. This is verified by exercising the actual dependency
    (calling the route handler directly bypasses Depends() entirely, which
    would produce a false pass/fail unrelated to authorization -- see the
    established convention in test_group_managers_routes.py Case 8/9)."""
    admin = make_user(db_session, roles, email="admin10@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia10@test.com", role_names=["Instructor"])
    learner_b = make_user(db_session, roles, email="lb10@test.com", role_names=["Learner"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)
    _member(db_session, group_id=group_b.id, user_id=learner_b.id)
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor_a)
    assert exc_info.value.status_code == 403
    # Group B's membership is untouched regardless of Instructor A's scope.
    assert (
        db_session.query(GroupMember)
        .filter(GroupMember.group_id == group_b.id, GroupMember.user_id == learner_b.id)
        .first()
        is not None
    )


# ═══════════════════════════════════════════════════════════════════════════
# 11. Instructor cannot retrieve unrelated group course assignments
# ═══════════════════════════════════════════════════════════════════════════

def test_instructor_cannot_list_courses_for_unrelated_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin11@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia11@test.com", role_names=["Instructor"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)
    course = _add_course(db_session, title="Course X")
    groups_routes.assign_group_course(
        group_b.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    with pytest.raises(HTTPException) as exc_info:
        groups_routes.list_group_courses(group_b.id, db=db_session, current_user=instructor_a)
    assert exc_info.value.status_code == 403


def test_instructor_can_list_courses_for_own_managed_group(db_session, roles):
    admin = make_user(db_session, roles, email="admin12@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia12@test.com", role_names=["Instructor"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)
    course = _add_course(db_session, title="Course X")
    groups_routes.assign_group_course(
        group_a.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    result = groups_routes.list_group_courses(group_a.id, db=db_session, current_user=instructor_a)
    assert len(json.loads(result.body)["data"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
# 12. Instructor cannot manipulate unrelated group manager data
# ═══════════════════════════════════════════════════════════════════════════

def test_instructor_cannot_assign_or_remove_managers_for_unrelated_group(db_session, roles):
    """Assign/remove-manager endpoints use Depends(require_roles("Administrator")),
    a blanket role check that runs before any group_id is examined -- being
    a manager of Group A grants no manager-mutation rights on Group B (or
    even on Group A itself -- see test 10's equivalent for members). Calling
    the route handler directly would bypass Depends() entirely and produce
    a false pass, so -- following the established convention in
    test_group_managers_routes.py Case 8/9 -- the actual dependency is
    exercised instead."""
    admin = make_user(db_session, roles, email="admin13@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia13@test.com", role_names=["Instructor"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)
    checker = require_roles("Administrator")

    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=instructor_a)
    assert exc_info.value.status_code == 403
    assert db_session.query(GroupManager).filter(GroupManager.group_id == group_b.id).count() == 0


# ═══════════════════════════════════════════════════════════════════════════
# 13. Shared learner membership does not expose another group
# ═══════════════════════════════════════════════════════════════════════════

def test_shared_learner_membership_does_not_expand_instructor_scope(db_session, roles):
    """
    Group A: Learner 1, Learner 2
    Group B: Learner 2, Learner 3
    Instructor A manages ONLY Group A.

    Instructor A's managed-learner scope legitimately includes Learner 2
    (shared with Group B), but that must NOT grant any access to Group B
    itself -- authorization is based on managed GROUPS (group_managers),
    never derived from shared learner membership.
    """
    admin = make_user(db_session, roles, email="admin14@test.com", role_names=["Administrator"])
    instructor_a = make_user(db_session, roles, email="ia14@test.com", role_names=["Instructor"])
    l1 = make_user(db_session, roles, email="l14a@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l14b@test.com", role_names=["Learner"])
    l3 = make_user(db_session, roles, email="l14c@test.com", role_names=["Learner"])
    group_a = _add_group(db_session, name="Group A", created_by=admin)
    group_b = _add_group(db_session, name="Group B", created_by=admin)
    _member(db_session, group_id=group_a.id, user_id=l1.id)
    _member(db_session, group_id=group_a.id, user_id=l2.id)
    _member(db_session, group_id=group_b.id, user_id=l2.id)
    _member(db_session, group_id=group_b.id, user_id=l3.id)
    _manage(db_session, group_id=group_a.id, user_id=instructor_a.id)

    from app.services import group_service as gs
    managed_learners = gs.get_managed_learner_ids(db_session, instructor_a)
    assert managed_learners == {l1.id, l2.id}  # shared Learner 2 legitimately included

    # But Group B itself remains completely inaccessible.
    with pytest.raises(HTTPException) as exc_info:
        groups_routes.get_group(group_b.id, db=db_session, current_user=instructor_a)
    assert exc_info.value.status_code == 403

    managed_group_ids = gs.get_managed_group_ids(db_session, instructor_a)
    assert group_b.id not in managed_group_ids


# ═══════════════════════════════════════════════════════════════════════════
# 14. Existing Admin permissions continue to work
# ═══════════════════════════════════════════════════════════════════════════

def test_admin_full_permissions_still_work(db_session, roles):
    admin = make_user(db_session, roles, email="admin15@test.com", role_names=["Administrator"])
    from app.schemas import GroupCreate, GroupUpdate

    create_result = groups_routes.create_group(GroupCreate(name="New Group"), db=db_session, current_user=admin)
    group_id = json.loads(create_result.body)["data"]["id"]

    groups_routes.get_group(group_id, db=db_session, current_user=admin)
    groups_routes.update_group(group_id, GroupUpdate(name="Renamed Group"), db=db_session, _=admin)
    groups_routes.list_groups(db=db_session, current_user=admin)

    course = _add_course(db_session, title="Admin Course")
    groups_routes.assign_group_course(
        group_id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    groups_routes.list_group_courses(group_id, db=db_session, current_user=admin)
    groups_routes.remove_group_course(group_id, course.id, db=db_session, _=admin)
    groups_routes.delete_group(group_id, db=db_session, _=admin)

    assert db_session.query(Group).filter(Group.id == group_id).first() is None


# ═══════════════════════════════════════════════════════════════════════════
# 15. Existing Learner behavior continues to work (i.e. remains excluded)
# ═══════════════════════════════════════════════════════════════════════════

def test_learner_still_has_no_group_endpoint_access(db_session, roles):
    admin = make_user(db_session, roles, email="admin16@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l16@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Group 1", created_by=admin)
    checker_list_get = require_roles("Administrator", "Instructor")

    with pytest.raises(HTTPException) as exc_info:
        checker_list_get(current_user=learner)
    assert exc_info.value.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 16. Existing individual CourseAssignment behavior continues to work
# ═══════════════════════════════════════════════════════════════════════════

def test_individual_course_assignment_behavior_unchanged(db_session, roles):
    admin = make_user(db_session, roles, email="admin17@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l17@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course X")

    result = individual_assign_course(
        course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin
    )
    body = json.loads(result.body)
    assert body["success"] is True
    assert learner.id in body["data"]["user_ids"]
