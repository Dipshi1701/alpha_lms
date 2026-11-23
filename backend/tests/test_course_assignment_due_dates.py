"""G012 -- due_date edge cases.

Same lightweight approach as the existing Groups test suites: route
handlers are called directly against the isolated in-memory SQLite session
from tests/conftest.py. Reuses the existing CourseAssignment/Course models
-- no second assignment system, no new schema beyond
Course.assignment_duration_days and CourseAssignment.due_date.
"""

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models import Course, CourseAssignment, Group, GroupCourseAssignment, GroupMember
from app.routes import groups as groups_routes
from app.routes.courses import assign_course as individual_assign_course
from app.routes.courses import update_course
from app.schemas import AssignCoursesBody, CourseCreate, CourseUpdate, GroupCourseAssignmentBody
from tests.conftest import make_user


def _add_group(db_session, *, name, created_by=None):
    group = Group(name=name, created_by_id=created_by.id if created_by else None)
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


def _add_course(db_session, *, title, duration_days=7):
    course = Course(title=title, assignment_duration_days=duration_days)
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


# ═════════════════════════════════════════════════════════════════════════
# 1-3 — Individual assignment: 1-day / 7-day / 30-day durations
# ═════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("duration_days", [1, 7, 30])
def test_individual_assignment_due_date_matches_course_duration(db_session, roles, duration_days):
    admin = make_user(db_session, roles, email=f"admin-d{duration_days}@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email=f"l-d{duration_days}@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A", duration_days=duration_days)

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)
    row = _assignment_for(db_session, course_id=course.id, user_id=learner.id)

    assert row.due_date is not None
    assert row.due_date == row.assigned_at + timedelta(days=duration_days)


# ═════════════════════════════════════════════════════════════════════════
# 4 — Assignment near month end
# ═════════════════════════════════════════════════════════════════════════

def test_due_date_rolls_over_month_end_correctly(db_session, roles):
    admin = make_user(db_session, roles, email="admin-me@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l-me@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A", duration_days=7)

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)
    row = _assignment_for(db_session, course_id=course.id, user_id=learner.id)
    # Force assigned_at to a known near-month-end date and recompute the
    # same way the app does, to make the rollover explicit and readable.
    row.assigned_at = datetime(2026, 9, 27, 10, 0, 0)
    from app.services.group_service import compute_due_date
    row.due_date = compute_due_date(course, row.assigned_at)
    db_session.commit()
    db_session.refresh(row)

    assert row.due_date == datetime(2026, 10, 4, 10, 0, 0)


# ═════════════════════════════════════════════════════════════════════════
# 5 — Assignment near year end
# ═════════════════════════════════════════════════════════════════════════

def test_due_date_rolls_over_year_end_correctly(db_session, roles):
    admin = make_user(db_session, roles, email="admin-ye@test.com", role_names=["Administrator"])
    course = _add_course(db_session, title="Course A", duration_days=10)
    from app.services.group_service import compute_due_date

    assigned_at = datetime(2026, 12, 28, 9, 30, 0)
    assert compute_due_date(course, assigned_at) == datetime(2027, 1, 7, 9, 30, 0)


# ═════════════════════════════════════════════════════════════════════════
# 6 — Leap-year date arithmetic
# ═════════════════════════════════════════════════════════════════════════

def test_due_date_handles_leap_year_correctly(db_session, roles):
    course = _add_course(db_session, title="Course A", duration_days=1)
    from app.services.group_service import compute_due_date

    # 2028 is a leap year -- Feb 28 + 1 day must land on Feb 29, not Mar 1
    # skipping a day or Mar 1 accidentally treated as +2.
    assigned_at = datetime(2028, 2, 28, 12, 0, 0)
    assert compute_due_date(course, assigned_at) == datetime(2028, 2, 29, 12, 0, 0)

    # And crossing out of the leap day correctly.
    assigned_at2 = datetime(2028, 2, 29, 12, 0, 0)
    assert compute_due_date(course, assigned_at2) == datetime(2028, 3, 1, 12, 0, 0)


# ═════════════════════════════════════════════════════════════════════════
# 7 — Invalid duration is rejected at the schema layer
# ═════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("bad_value", [0, -1, -7])
def test_invalid_duration_rejected_on_create(bad_value):
    with pytest.raises(ValidationError):
        CourseCreate(title="Course A", assignment_duration_days=bad_value)


@pytest.mark.parametrize("bad_value", [0, -5])
def test_invalid_duration_rejected_on_update(bad_value):
    with pytest.raises(ValidationError):
        CourseUpdate(assignment_duration_days=bad_value)


def test_decimal_duration_rejected():
    with pytest.raises(ValidationError):
        CourseCreate(title="Course A", assignment_duration_days=3.5)


def test_non_numeric_duration_rejected():
    with pytest.raises(ValidationError):
        CourseCreate(title="Course A", assignment_duration_days="abc")


def test_missing_duration_on_create_uses_backward_compatible_default():
    # PART 4/14: omission is handled by falling back to the same
    # backward-compatible default used for pre-existing courses (7).
    body = CourseCreate(title="Course A")
    assert body.assignment_duration_days == 7


@pytest.mark.parametrize("good_value", [1, 7, 30])
def test_valid_durations_accepted(good_value):
    body = CourseCreate(title="Course A", assignment_duration_days=good_value)
    assert body.assignment_duration_days == good_value


# ═════════════════════════════════════════════════════════════════════════
# 8 — Existing assignment retains its due_date after course duration changes
# ═════════════════════════════════════════════════════════════════════════

def test_existing_assignment_due_date_unchanged_after_course_duration_change(db_session, roles):
    admin = make_user(db_session, roles, email="admin-chg@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l-chg@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A", duration_days=7)

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)
    row = _assignment_for(db_session, course_id=course.id, user_id=learner.id)
    original_assigned_at = row.assigned_at
    original_due_date = row.due_date
    assert original_due_date == original_assigned_at + timedelta(days=7)

    # Admin changes the course duration -- course stays editable, no lock.
    update_course(course.id, CourseUpdate(assignment_duration_days=14), db=db_session, _=admin)
    db_session.refresh(course)
    assert course.assignment_duration_days == 14

    db_session.refresh(row)
    assert row.assigned_at == original_assigned_at
    assert row.due_date == original_due_date  # NOT recalculated to +14 days


# ═════════════════════════════════════════════════════════════════════════
# 9 — Newly created assignment uses the NEW duration
# ═════════════════════════════════════════════════════════════════════════

def test_new_assignment_after_duration_change_uses_new_duration(db_session, roles):
    admin = make_user(db_session, roles, email="admin-new@test.com", role_names=["Administrator"])
    l1 = make_user(db_session, roles, email="l1-new@test.com", role_names=["Learner"])
    l2 = make_user(db_session, roles, email="l2-new@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A", duration_days=7)

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[l1.id]), db=db_session, current_user=admin)
    row1 = _assignment_for(db_session, course_id=course.id, user_id=l1.id)
    assert row1.due_date == row1.assigned_at + timedelta(days=7)

    update_course(course.id, CourseUpdate(assignment_duration_days=14), db=db_session, _=admin)

    # A brand-new assignment (l2) must use the *current* 14-day duration,
    # while l1's row (asserted above) is untouched.
    individual_assign_course(
        course.id, AssignCoursesBody(user_ids=[l1.id, l2.id]), db=db_session, current_user=admin
    )
    row2 = _assignment_for(db_session, course_id=course.id, user_id=l2.id)
    assert row2.due_date == row2.assigned_at + timedelta(days=14)

    db_session.refresh(row1)
    assert row1.due_date == row1.assigned_at + timedelta(days=7)  # still unchanged


# ═════════════════════════════════════════════════════════════════════════
# 10 — A new group member gets due_date based on THEIR OWN assignment date
# ═════════════════════════════════════════════════════════════════════════

def test_new_group_member_due_date_based_on_own_assigned_at_not_groups(db_session, roles):
    from app.schemas import GroupMemberBody

    admin = make_user(db_session, roles, email="admin-nm@test.com", role_names=["Administrator"])
    early_learner = make_user(db_session, roles, email="early@test.com", role_names=["Learner"])
    late_learner = make_user(db_session, roles, email="late@test.com", role_names=["Learner"])
    group = _add_group(db_session, name="Sales", created_by=admin)
    db_session.add(GroupMember(group_id=group.id, user_id=early_learner.id))
    db_session.commit()
    course = _add_course(db_session, title="Angular Basics", duration_days=7)

    groups_routes.assign_group_course(
        group.id, GroupCourseAssignmentBody(course_id=course.id), db=db_session, current_user=admin
    )
    early_row = _assignment_for(db_session, course_id=course.id, user_id=early_learner.id)
    assert early_row.due_date == early_row.assigned_at + timedelta(days=7)

    # Neha (late_learner) joins the group later, after the course was
    # already assigned to the group.
    groups_routes.add_group_member(group.id, GroupMemberBody(user_id=late_learner.id), db=db_session, _=admin)
    late_row = _assignment_for(db_session, course_id=course.id, user_id=late_learner.id)

    assert late_row is not None
    assert late_row.assigned_at != early_row.assigned_at
    assert late_row.due_date == late_row.assigned_at + timedelta(days=7)
    # Must NOT reuse the original group assignment's due date.
    assert late_row.due_date != early_row.due_date


# ── Naive/aware datetime consistency (PART 17) ───────────────────────────

def test_due_date_uses_naive_datetimes_consistently_with_assigned_at(db_session, roles):
    """Follows the existing project-wide convention (datetime.utcnow(), naive
    DateTime columns throughout models.py) -- due_date must not mix naive
    and timezone-aware datetimes with assigned_at."""
    admin = make_user(db_session, roles, email="admin-tz@test.com", role_names=["Administrator"])
    learner = make_user(db_session, roles, email="l-tz@test.com", role_names=["Learner"])
    course = _add_course(db_session, title="Course A", duration_days=5)

    individual_assign_course(course.id, AssignCoursesBody(user_ids=[learner.id]), db=db_session, current_user=admin)
    row = _assignment_for(db_session, course_id=course.id, user_id=learner.id)

    assert row.assigned_at.tzinfo is None
    assert row.due_date.tzinfo is None
    # Subtraction between the two must work without a naive/aware TypeError.
    assert (row.due_date - row.assigned_at) == timedelta(days=5)
