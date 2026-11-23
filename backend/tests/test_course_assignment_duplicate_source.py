"""G012 -- duplicate prevention ("one learner + one course = one active
CourseAssignment") and derived assignment `source` ("individual" | "group").

Same lightweight approach as the existing Groups test suites: route
handlers are called directly against the isolated in-memory SQLite session
from tests/conftest.py. Reuses the existing CourseAssignment model -- no
second assignment system, and `source` is derived (not persisted) by
group_service.resolve_assignment_source.
"""

from datetime import datetime

from fastapi import HTTPException
import pytest

from app.models import Course, CourseAssignment, Group, GroupMember
from app.routes import courses as courses_routes
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


def _rows_for(db_session, *, course_id, user_id=None):
    q = db_session.query(CourseAssignment).filter(CourseAssignment.course_id == course_id)
    if user_id is not None:
        q = q.filter(CourseAssignment.user_id == user_id)
    return q.all()


def _brief_for(db_session, *, course, user_id, current_user=None):
    briefs = courses_routes.get_course_assignment_briefs(db_session, course.id, current_user=current_user)
    return next((b for b in briefs if b.user_id == user_id), None)


# ═════════════════════════════════════════════════════════════════════════
# 1 — Individual first, group later
# ═════════════════════════════════════════════════════════════════════════

def test_individual_first_then_group_later_one_assignment_source_individual(db_session, roles):
    admin = make_user(db_session, roles, email="admin1@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l1@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Sales", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Angular")

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)
    # Force a distinct, unambiguous assigned_at so this test does not
    # depend on OS clock resolution between two back-to-back
    # datetime.utcnow() calls happening to land in the same tick (which
    # would make the individual and group timestamps coincidentally
    # equal, defeating resolve_assignment_source's timestamp match).
    row = _rows_for(db_session, course_id=course.id, user_id=learner.id)[0]
    row.assigned_at = datetime(2020, 1, 1, 0, 0, 0)
    db_session.commit()

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = _rows_for(db_session, course_id=course.id, user_id=learner.id)
    assert len(rows) == 1

    brief = _brief_for(db_session, course=course, user_id=learner.id)
    assert brief.source == "individual"
    assert brief.source_group_name is None


# ═════════════════════════════════════════════════════════════════════════
# 2 — Group first, individual later
# ═════════════════════════════════════════════════════════════════════════

def test_group_first_then_individual_later_one_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin2@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l2@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Sales", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Angular")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    original_row = _rows_for(db_session, course_id=course.id, user_id=learner.id)[0]

    brief_before = _brief_for(db_session, course=course, user_id=learner.id)
    assert brief_before.source == "group"
    assert brief_before.source_group_name == "Sales"

    # Admin includes the (already assigned) learner in a subsequent
    # individual /assign call -- the desired-set semantics of that
    # endpoint mean this is a no-op for them (their row is untouched).
    individual_assign_course(
        course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin
    )

    rows = _rows_for(db_session, course_id=course.id, user_id=learner.id)
    assert len(rows) == 1
    assert rows[0].id == original_row.id
    assert rows[0].assigned_at == original_row.assigned_at


# ═════════════════════════════════════════════════════════════════════════
# 3 — Learner in multiple groups, both assigned the same course
# ═════════════════════════════════════════════════════════════════════════

def test_learner_in_multiple_groups_same_course_one_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin3@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l3@test.com", role_names=["Learner"])
    group_a = _add_group(db_session, name="Sales", created_by=admin)
    group_b = _add_group(db_session, name="Support", created_by=admin)
    db_session.add(GroupMember(group_id=group_a.id, user_id=learner.id))
    db_session.add(GroupMember(group_id=group_b.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Angular")

    groups_routes.assign_group_course(
        group_a.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    groups_routes.assign_group_course(
        group_b.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )

    rows = _rows_for(db_session, course_id=course.id, user_id=learner.id)
    assert len(rows) == 1

    brief = _brief_for(db_session, course=course, user_id=learner.id)
    assert brief.source == "group"
    assert brief.source_group_name == "Sales"  # first group to actually create the row


# ═════════════════════════════════════════════════════════════════════════
# 4 — Same group/course repeated
# ═════════════════════════════════════════════════════════════════════════

def test_repeated_same_group_course_assignment_no_duplicate(db_session, roles):
    admin = make_user(db_session, roles, email="admin4@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l4@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Sales", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Angular")

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    with pytest.raises(HTTPException) as exc_info:
        groups_routes.assign_group_course(
            group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
        )
    assert exc_info.value.status_code == 400

    rows = _rows_for(db_session, course_id=course.id, user_id=learner.id)
    assert len(rows) == 1


# ═════════════════════════════════════════════════════════════════════════
# 5 — Same individual assignment repeated
# ═════════════════════════════════════════════════════════════════════════

def test_repeated_individual_assignment_no_duplicate_and_unchanged_row(db_session, roles):
    admin = make_user(db_session, roles, email="admin5@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l5@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Angular")

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)
    original_row = _rows_for(db_session, course_id=course.id, user_id=learner.id)[0]
    original_assigned_at = original_row.assigned_at
    original_due_date = original_row.due_date

    # PART 18.7/18.8 — repeating the exact same desired set is a no-op for
    # this already-assigned learner.
    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)

    rows = _rows_for(db_session, course_id=course.id, user_id=learner.id)
    assert len(rows) == 1
    assert rows[0].id == original_row.id
    assert rows[0].assigned_at == original_assigned_at
    assert rows[0].due_date == original_due_date


# ═════════════════════════════════════════════════════════════════════════
# 6 — Learner has Course X but remains selectable for Course Y
# ═════════════════════════════════════════════════════════════════════════

def test_learner_with_course_x_still_selectable_for_course_y(db_session, roles):
    admin = make_user(db_session, roles, email="admin6@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l6@test.com", role_names=["Learner"])
    course_x = _add_course(db_session, title="Angular")
    course_y = _add_course(db_session, title="React")

    individual_assign_course(course_x.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)

    # Course X's own assignment briefs mark this learner as already assigned...
    brief_x = _brief_for(db_session, course=course_x, user_id=learner.id)
    assert brief_x is not None

    # ...but Course Y's briefs have no entry for them at all -- nothing
    # disables/blocks assigning Course Y to this same learner.
    brief_y = _brief_for(db_session, course=course_y, user_id=learner.id)
    assert brief_y is None

    result = individual_assign_course(
        course_y.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin
    )
    assert result.status_code == 200
    assert len(_rows_for(db_session, course_id=course_y.id, user_id=learner.id)) == 1
    # Course X's assignment is completely unaffected.
    assert len(_rows_for(db_session, course_id=course_x.id, user_id=learner.id)) == 1


# ═════════════════════════════════════════════════════════════════════════
# 9 — No duplicate CourseAssignment rows across a mixed sequence of events
# ═════════════════════════════════════════════════════════════════════════

def test_no_duplicate_rows_across_mixed_individual_and_group_events(db_session, roles):
    admin = make_user(db_session, roles, email="admin9@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l9@test.com", role_names=["Learner"])
    group_a = _add_group(db_session, name="Sales", created_by=admin)
    group_b = _add_group(db_session, name="Support", created_by=admin)
    db_session.add(GroupMember(group_id=group_a.id, user_id=learner.id))
    db_session.add(GroupMember(group_id=group_b.id, user_id=learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Angular")

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)
    groups_routes.assign_group_course(
        group_a.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    groups_routes.assign_group_course(
        group_b.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)

    rows = _rows_for(db_session, course_id=course.id, user_id=learner.id)
    assert len(rows) == 1
    # And it must be the ORIGINAL individually-created row throughout.
    pairs = [(r.course_id, r.user_id) for r in _rows_for(db_session, course_id=course.id)]
    assert len(pairs) == len(set(pairs))


# ── Source scoping: a Learner never sees another learner's brief ────────

def test_learner_scoped_briefs_never_leak_another_learners_assignment(db_session, roles):
    admin = make_user(db_session, roles, email="admin10@test.com", role_names=["Administrator"])
    l1 = make_user(db_session, roles, email="l10a@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l10b@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Angular")

    individual_assign_course(
        course.id, AssignCoursesBody(user_ids=[l1.id, l2.id]), db=db_session, current_user=admin
    )

    # Admin/Instructor-facing view sees both.
    admin_briefs = courses_routes.get_course_assignment_briefs(db_session, course.id, current_user=admin)
    assert {b.user_id for b in admin_briefs} == {l1.id, l2.id}

    # l1's own (Learner-scoped) view only ever contains their own row.
    l1_briefs = courses_routes.get_course_assignment_briefs(db_session, course.id, current_user=l1)
    assert {b.user_id for b in l1_briefs} == {l1.id}
