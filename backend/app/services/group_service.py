"""Group management and scoping lookups.

Answers "which groups does this user manage" and "which learners are in
those groups" so that the (future) Groups routes and Course Assignment
routes can share the same scoping logic instead of re-implementing it.

There is no separate "Manager" role. An Instructor acts as a group manager
when they hold a row in group_managers for one or more groups — see
is_scoped_manager(). Administrators keep the unrestricted access used
throughout the rest of the app (e.g. courses.list_courses ignores
CourseAssignment entirely for Administrators); this module does not
synthesize implicit "manages everything" rows for them, callers are
expected to check the role first the same way existing routes do.
"""

from datetime import datetime, timedelta
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models import Course, CourseAssignment, Group, GroupCourseAssignment, GroupManager, GroupMember, Role, User

ADMINISTRATOR_ROLE = "Administrator"
INSTRUCTOR_ROLE = "Instructor"
LEARNER_ROLE = "Learner"


def is_scoped_manager(user: User) -> bool:
    """
    True if `user` should be treated as a scoped group manager: an Instructor
    who does NOT also hold the Administrator role.

    Administrators are never scoped, even if they also have the Instructor
    role — they keep unrestricted access. Learners are never scoped managers.
    """
    role_names = {r.name for r in user.roles}
    return INSTRUCTOR_ROLE in role_names and ADMINISTRATOR_ROLE not in role_names


def get_managed_group_ids(db: Session, user: User) -> list[int]:
    """
    Return the IDs of groups where `user` has a row in group_managers.

    This is a literal lookup of group_managers — it does not special-case
    Administrators. "Sees every group" behavior for Administrators is a
    caller-side concern (check the role, skip this filter entirely), the same
    way list_courses() returns every course for Administrators without
    consulting CourseAssignment.
    """
    rows = db.query(GroupManager.group_id).filter(GroupManager.user_id == user.id).all()
    return [r[0] for r in rows]


def expand_group_ids(db: Session, group_ids: Iterable[int]) -> set[int]:
    """
    Resolve a collection of group IDs to the set of Learner user IDs who
    belong to those groups (via group_members), deduplicated.

    Only users who currently hold the Learner role are returned, even if a
    non-learner ends up with a group_members row. Does not touch
    CourseAssignment or notifications — pure lookup/expansion for callers
    (e.g. the future course-assignment flow) to use however they need.
    """
    ids = list(group_ids)
    if not ids:
        return set()
    rows = (
        db.query(GroupMember.user_id)
        .join(User, User.id == GroupMember.user_id)
        .join(User.roles)
        .filter(GroupMember.group_id.in_(ids), Role.name == LEARNER_ROLE)
        .distinct()
        .all()
    )
    return {r[0] for r in rows}


def get_managed_learner_ids(db: Session, user: User) -> set[int]:
    """
    Return the set of Learner user IDs belonging to any group `user` manages.

    Deduplicated across all of the user's managed groups. The manager is
    never included just for managing a group — they'd only appear if they
    also hold the Learner role AND are separately enrolled as a member.
    """
    group_ids = get_managed_group_ids(db, user)
    return expand_group_ids(db, group_ids)


def can_view_group(db: Session, user: User, group_id: int) -> bool:
    """
    True if `user` is allowed to view this specific group.

    Non-scoped users (Administrators — see is_scoped_manager) have
    unrestricted visibility. A scoped Instructor may only view groups they
    actually manage (a row in group_managers), reusing get_managed_group_ids
    rather than a separate query.
    """
    if not is_scoped_manager(user):
        return True
    return group_id in get_managed_group_ids(db, user)


# ── Group membership (G003) ──────────────────────────────────────────────────
#
# HTTPException handling stays in the routes (see notification_service.py's
# mark_read/mark_all_read for the existing precedent: services return
# plain booleans/objects and the route decides the HTTP status). None of
# these commit — the caller commits once, same convention as
# notification_service.notify_course_assigned.

def is_learner(user: User) -> bool:
    """True if `user` currently holds the Learner role, regardless of any
    other roles (e.g. Instructor) they may also hold."""
    return LEARNER_ROLE in {r.name for r in user.roles}


def get_group(db: Session, group_id: int) -> Optional[Group]:
    """Look up a Group by id, or None if it doesn't exist."""
    return db.query(Group).filter(Group.id == group_id).first()


def is_group_member(db: Session, *, group_id: int, user_id: int) -> bool:
    """True if `user_id` already has a group_members row for `group_id`."""
    return (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
        is not None
    )


def add_group_member(db: Session, *, group_id: int, user_id: int) -> GroupMember:
    """
    Create a group_members row linking `user_id` to `group_id`.

    Assumes the caller has already validated that the group exists, the
    user exists, the user holds the Learner role, and no duplicate row
    exists (is_group_member() returned False) — this function does not
    re-check those, it only performs the insert.
    """
    member = GroupMember(group_id=group_id, user_id=user_id)
    db.add(member)
    return member


def sync_new_member_to_existing_group_courses(
    db: Session, *, group_id: int, user_id: int, assigned_by_id: Optional[int]
) -> list[CourseAssignment]:
    """
    G012 PART 7/13: when a Learner is added to a group that already has one
    or more courses assigned (GroupCourseAssignment), create a
    CourseAssignment for each such course they don't already have.

    Uses the CURRENT moment as THIS learner's own assigned_at -- never the
    original GroupCourseAssignment.assigned_at -- so due_date (computed via
    compute_due_date) reflects when they actually joined, not when the
    group was first assigned the course. Reuses the existing
    CourseAssignment model/uniqueness rule exactly like
    sync_group_course_assignment_to_learners() -- this is not a second
    assignment system, just a second trigger point for the same one.

    Assumes the caller (routes.groups.add_group_member) has already
    validated that `user_id` holds the Learner role and was not already a
    member — mirrors the other helpers in this module.
    """
    course_ids = {
        r[0]
        for r in db.query(GroupCourseAssignment.course_id)
        .filter(GroupCourseAssignment.group_id == group_id)
        .all()
    }
    if not course_ids:
        return []

    already_assigned_course_ids = {
        r[0]
        for r in db.query(CourseAssignment.course_id)
        .filter(CourseAssignment.course_id.in_(course_ids), CourseAssignment.user_id == user_id)
        .all()
    }
    missing_course_ids = course_ids - already_assigned_course_ids
    if not missing_course_ids:
        return []

    courses = db.query(Course).filter(Course.id.in_(missing_course_ids)).all()
    assigned_at = datetime.utcnow()
    created: list[CourseAssignment] = []
    for course in courses:
        row = CourseAssignment(
            course_id=course.id,
            user_id=user_id,
            assigned_at=assigned_at,
            due_date=compute_due_date(course, assigned_at),
            assigned_by_id=assigned_by_id,
        )
        db.add(row)
        created.append(row)
    return created


def remove_group_member(db: Session, *, group_id: int, user_id: int) -> bool:
    """
    Delete the group_members row for (`group_id`, `user_id`) if it exists.

    Returns True if a row was deleted, False if the learner wasn't a member
    of the group — mirrors notification_service.mark_read()'s bool-return
    pattern so the route can translate the result into the right HTTP status.
    Only the GroupMember row is touched; the User and Group rows are
    untouched.
    """
    row = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if not row:
        return False
    db.delete(row)
    return True


# ── Group manager assignment (G004) ──────────────────────────────────────────
#
# Same conventions as the membership helpers above: no HTTPException here,
# no commits (the route validates and commits). Assigning/removing a manager
# only ever touches group_managers — it never creates, removes, or otherwise
# reads group_members. Being a Group Manager does not make someone a group
# member, and being a group member does not make someone a manager.

def is_instructor(user: User) -> bool:
    """True if `user` currently holds the Instructor role, regardless of any
    other roles (e.g. Administrator) they may also hold."""
    return INSTRUCTOR_ROLE in {r.name for r in user.roles}


def is_group_manager(db: Session, *, group_id: int, user_id: int) -> bool:
    """True if `user_id` already has a group_managers row for `group_id`."""
    return (
        db.query(GroupManager)
        .filter(GroupManager.group_id == group_id, GroupManager.user_id == user_id)
        .first()
        is not None
    )


def assign_group_manager(db: Session, *, group_id: int, user_id: int) -> GroupManager:
    """
    Create a group_managers row linking `user_id` to `group_id`.

    Assumes the caller has already validated that the group exists, the
    user exists, the user holds the Instructor role, and no duplicate row
    exists (is_group_manager() returned False) — this function does not
    re-check those, it only performs the insert. A user can manage any
    number of groups, and a group can have any number of managers; nothing
    here restricts that.
    """
    manager = GroupManager(group_id=group_id, user_id=user_id)
    db.add(manager)
    return manager


def remove_group_manager(db: Session, *, group_id: int, user_id: int) -> bool:
    """
    Delete the group_managers row for (`group_id`, `user_id`) if it exists.

    Returns True if a row was deleted, False if the user wasn't a manager of
    the group. Only the GroupManager row is touched — the User, Group, and
    any GroupMember row for the same (group, user) pair are left completely
    intact.
    """
    row = (
        db.query(GroupManager)
        .filter(GroupManager.group_id == group_id, GroupManager.user_id == user_id)
        .first()
    )
    if not row:
        return False
    db.delete(row)
    return True


# ── Group course assignment (G006) ───────────────────────────────────────────
#
# Same conventions as the membership/manager helpers above: no HTTPException
# here, no commits (the route validates and commits). These helpers only
# record that a Group has been assigned a Course (group_course_assignments).
# The learner-level expansion into individual CourseAssignment rows lives
# below in the G007 section — kept separate because it is a distinct
# concern (which learners currently get access) from this one (which
# Group/Course pairs exist).

def get_course(db: Session, course_id: int) -> Optional[Course]:
    """Look up a Course by id, or None if it doesn't exist."""
    return db.query(Course).filter(Course.id == course_id).first()


def is_group_course_assigned(db: Session, *, group_id: int, course_id: int) -> bool:
    """True if `group_id` already has a group_course_assignments row for `course_id`."""
    return (
        db.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group_id, GroupCourseAssignment.course_id == course_id)
        .first()
        is not None
    )


def assign_group_course(
    db: Session,
    *,
    group_id: int,
    course_id: int,
    assigned_by_id: int,
    assigned_at: Optional[datetime] = None,
) -> GroupCourseAssignment:
    """
    Create a group_course_assignments row linking `course_id` to `group_id`.

    Assumes the caller has already validated that the group exists, the
    course exists, and no duplicate row exists (is_group_course_assigned()
    returned False) — this function does not re-check those, it only
    performs the insert. Does not create any per-learner CourseAssignment
    rows itself (see sync_group_course_assignment_to_learners() below).

    `assigned_at` defaults to now — same as the column's own default — but
    callers may pin an explicit value so it can be reused as the timestamp
    for the learner-level CourseAssignment rows created as a result of this
    same group assignment (see G007).
    """
    row = GroupCourseAssignment(
        group_id=group_id,
        course_id=course_id,
        assigned_by_id=assigned_by_id,
        assigned_at=assigned_at or datetime.utcnow(),
    )
    db.add(row)
    return row


def get_group_courses(db: Session, group_id: int) -> list[Course]:
    """Return the Courses currently assigned to `group_id`, via group_course_assignments."""
    return (
        db.query(Course)
        .join(GroupCourseAssignment, GroupCourseAssignment.course_id == Course.id)
        .filter(GroupCourseAssignment.group_id == group_id)
        .order_by(Course.id.desc())
        .all()
    )


def remove_group_course(db: Session, *, group_id: int, course_id: int) -> bool:
    """
    Delete the group_course_assignments row for (`group_id`, `course_id`) if
    it exists.

    Returns True if a row was deleted, False if the course wasn't assigned
    to the group. Only the GroupCourseAssignment row is touched — the
    Course, Group, individual CourseAssignment rows, GroupMember rows, and
    GroupManager rows are all left completely intact.
    """
    row = (
        db.query(GroupCourseAssignment)
        .filter(GroupCourseAssignment.group_id == group_id, GroupCourseAssignment.course_id == course_id)
        .first()
    )
    if not row:
        return False
    db.delete(row)
    return True


# ── Course assignment duration / due date (G012) ─────────────────────────────
#
# due_date is always derived from the specific CourseAssignment row's own
# assigned_at plus the course's CURRENT assignment_duration_days at the
# moment that row is created. It is never derived from course.created_at,
# group.created_at, or a fixed calendar date -- see PART 3/5 of the G012
# spec. Changing assignment_duration_days later never touches previously
# computed due_date values (see routes/courses.py update_course).

def compute_due_date(course: Course, assigned_at: datetime) -> datetime:
    """due_date for a single CourseAssignment row: assigned_at + Course.assignment_duration_days."""
    return assigned_at + timedelta(days=course.assignment_duration_days)


def resolve_assignment_source(
    db: Session, *, course_id: int, user_id: int, assigned_at: datetime
) -> tuple[str, Optional[str]]:
    """
    Best-effort, DERIVED classification of where a learner's
    CourseAssignment for `course_id` came from: "individual" or "group".

    No new column is added to CourseAssignment to store this (G012 PART 10
    prefers deriving the source over adding redundant data). The
    derivation relies on the fact that sync_group_course_assignment_to_
    learners() below always reuses the *exact* GroupCourseAssignment.
    assigned_at timestamp for every learner-level CourseAssignment row it
    creates. So: if there is a GroupCourseAssignment for this course, for a
    group the user is CURRENTLY a member of, whose assigned_at exactly
    equals this CourseAssignment's assigned_at, the assignment is
    attributed to that group (its name is returned). Otherwise it is
    reported as "individual".

    Known limitations (accepted rather than adding a persisted source
    column):
      * if a learner is later removed from the group that originally
        granted them the course, this will subsequently report
        "individual" since the group_members row it needs to match
        against is gone -- the CourseAssignment itself is untouched either
        way (see PART 13).
      * in the extremely unlikely event that an individual assignment and
        an unrelated group assignment for the same course are created
        within the same datetime.utcnow() clock tick, this could
        misattribute the individual one as group-sourced. In practice this
        requires two separate admin actions to land in the same
        sub-millisecond window, which real HTTP-driven usage does not
        produce.
    """
    match = (
        db.query(GroupCourseAssignment.group_id, Group.name)
        .join(Group, Group.id == GroupCourseAssignment.group_id)
        .join(GroupMember, GroupMember.group_id == GroupCourseAssignment.group_id)
        .filter(
            GroupCourseAssignment.course_id == course_id,
            GroupCourseAssignment.assigned_at == assigned_at,
            GroupMember.user_id == user_id,
        )
        .first()
    )
    if match:
        _, group_name = match
        return "group", group_name
    return "individual", None


# ── Group course assignment -> learner CourseAssignments (G007) ─────────────
#
# Connects the G006 Group->Course relationship to the EXISTING learner-level
# CourseAssignment system — no second assignment table, no new model. No
# HTTPException here, no commit (the route commits once, alongside the
# GroupCourseAssignment insert, in a single transaction).

def sync_group_course_assignment_to_learners(
    db: Session,
    *,
    group_id: int,
    course: Course,
    assigned_at: datetime,
    assigned_by_id: Optional[int],
) -> list[CourseAssignment]:
    """
    For every current Learner member of `group_id` (via expand_group_ids(),
    which already filters to the Learner role — Instructors/Administrators/
    Group Managers are never included even if they somehow hold a
    group_members row), create a CourseAssignment for `course.id` unless
    one already exists for that (course_id, user_id) pair.

    Reuses the existing CourseAssignment model/uniqueness rule exactly as
    courses.assign_course() does — this does not create a second
    assignment system. A learner who already has an individual
    CourseAssignment for this course (assigned before or after the group
    assignment) is left with exactly one row; nothing is deleted or
    duplicated. A learner in multiple groups that are each assigned the
    same course still ends up with exactly one CourseAssignment, because
    the check below is keyed on (course_id, user_id), not on group
    membership.

    `assigned_at` is reused as-is for every created row (the Group Course
    Assignment's own timestamp) -- this remains unchanged from G007/G008.
    G012 adds: `due_date` is computed per learner from that SAME
    assigned_at and the course's *current* assignment_duration_days (see
    compute_due_date). A learner who joins the group later and receives
    this same already-assigned course gets their own, later assigned_at
    (set by the caller — see routes/groups.assign_group_course is not
    involved in that path; membership changes don't create assignments —
    this function is only ever invoked at group-course-assignment time),
    and therefore their own, later due_date -- never the original group
    assignment's due date.

    Returns the list of newly created CourseAssignment rows (empty if the
    group has no Learner members or all of them already had this course).
    """
    learner_ids = expand_group_ids(db, [group_id])
    if not learner_ids:
        return []

    already_assigned_ids = {
        r[0]
        for r in db.query(CourseAssignment.user_id)
        .filter(CourseAssignment.course_id == course.id, CourseAssignment.user_id.in_(learner_ids))
        .all()
    }

    created: list[CourseAssignment] = []
    for user_id in sorted(learner_ids - already_assigned_ids):
        row = CourseAssignment(
            course_id=course.id,
            user_id=user_id,
            assigned_at=assigned_at,
            due_date=compute_due_date(course, assigned_at),
            assigned_by_id=assigned_by_id,
        )
        db.add(row)
        created.append(row)
    return created
