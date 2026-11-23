from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Group, GroupManager, GroupMember, User
from app.response import success_response
from app.routes.courses import course_to_response
from app.schemas import (
    GroupCreate, GroupResponse, GroupUpdate,
    GroupCourseAssignmentBody, GroupCourseAssignmentResponse,
    GroupManagerBody, GroupManagerDetailResponse, GroupManagerResponse,
    GroupMemberBody, GroupMemberDetailResponse, GroupMemberResponse,
)
from app.security import require_roles
from app.services import group_service as gs

router = APIRouter()


def _get_group_or_404(db: Session, group_id: int) -> Group:
    group = gs.get_group(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


def _group_to_response(group: Group) -> dict:
    return GroupResponse.model_validate(group).model_dump()


# ── Group CRUD (G005) ─────────────────────────────────────────────────────────
# Create/Update/Delete are Administrator-only, following the same
# Administrator-only mutation convention already established by G003
# (membership) and G004 (manager assignment) — scoped Instructors are not
# given any additional mutation permissions here. List/Get are open to
# Administrator + Instructor: Administrators see every group unrestricted;
# a scoped Instructor (see group_service.is_scoped_manager) only sees groups
# they actually manage, filtered at the database level via
# get_managed_group_ids(). Learners have no established Group visibility, so
# they are not included in the required-roles list for either endpoint.
# Creating/renaming a group never creates GroupMember/GroupManager rows.

@router.get("")
def list_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator", "Instructor")),
):
    """List groups: all groups for Administrators, only managed groups for a scoped Instructor."""
    if gs.is_scoped_manager(current_user):
        managed_ids = gs.get_managed_group_ids(db, current_user)
        if not managed_ids:
            return success_response(message="Groups fetched successfully", data=[])
        groups = (
            db.query(Group)
            .filter(Group.id.in_(managed_ids))
            .order_by(Group.id.desc())
            .all()
        )
    else:
        groups = db.query(Group).order_by(Group.id.desc()).all()
    payload = [_group_to_response(g) for g in groups]
    return success_response(message="Groups fetched successfully", data=payload)


@router.post("")
def create_group(
    body: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator")),
):
    """Create a new, empty group. Does not add any members or managers."""
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")
    if db.query(Group).filter(Group.name == name).first():
        raise HTTPException(status_code=400, detail="A group with this name already exists")

    group = Group(name=name, created_by_id=current_user.id)
    db.add(group)
    db.commit()
    db.refresh(group)
    return success_response(
        message="Group created successfully",
        data=_group_to_response(group),
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{group_id}")
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator", "Instructor")),
):
    """Get a single group. A scoped Instructor may only view groups they manage."""
    group = _get_group_or_404(db, group_id)
    if not gs.can_view_group(db, current_user, group_id):
        raise HTTPException(status_code=403, detail="Not allowed")
    return success_response(message="Group fetched successfully", data=_group_to_response(group))


@router.patch("/{group_id}")
def update_group(
    group_id: int,
    body: GroupUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    """Rename a group."""
    group = _get_group_or_404(db, group_id)
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Group name is required")
        if db.query(Group).filter(Group.name == name, Group.id != group_id).first():
            raise HTTPException(status_code=400, detail="A group with this name already exists")
        group.name = name
    db.commit()
    db.refresh(group)
    return success_response(message="Group updated successfully", data=_group_to_response(group))


@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    """Delete a group. Cascades to its GroupMember/GroupManager rows only
    (see Group.members/Group.managers cascade="all, delete-orphan" in
    models.py) — never touches CourseAssignment or User/Course rows."""
    group = _get_group_or_404(db, group_id)
    db.delete(group)
    db.commit()
    return success_response(message="Group deleted successfully", data={"group_id": group_id})


# ── Group membership (G003) — Administrator only ─────────────────────────────
# Adding/removing a member only ever touches the group_members table: it does
# not create/delete CourseAssignment rows, does not send notifications, and
# does not touch the User or Group rows themselves. Listing members is a
# read of that same table, open to anyone who can already view the group.

@router.get("/{group_id}/members")
def list_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator", "Instructor")),
):
    """List learners currently in a group. Scoped Instructors only see groups they manage."""
    _get_group_or_404(db, group_id)
    if not gs.can_view_group(db, current_user, group_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    rows = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id)
        .order_by(GroupMember.added_at.desc(), GroupMember.id.desc())
        .all()
    )
    payload = []
    for member in rows:
        user = member.user
        payload.append(
            GroupMemberDetailResponse(
                id=member.id,
                group_id=member.group_id,
                user_id=member.user_id,
                full_name=user.full_name if user else None,
                email=user.email if user else "",
                added_at=member.added_at,
            ).model_dump()
        )
    return success_response(message="Group members fetched successfully", data=payload)


@router.post("/{group_id}/members")
def add_group_member(
    group_id: int,
    body: GroupMemberBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    """
    Add an existing Learner to a group.

    G012 PART 7/13: if the group already has one or more courses assigned
    (GroupCourseAssignment), the learner receives a CourseAssignment for
    each one they don't already have, using THEIR OWN join time as
    assigned_at (and due_date derived from it) -- never the original group
    assignment's timestamp. See group_service.
    sync_new_member_to_existing_group_courses.
    """
    _get_group_or_404(db, group_id)

    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not gs.is_learner(user):
        raise HTTPException(status_code=400, detail="Only users with the Learner role can be added to a group")

    if gs.is_group_member(db, group_id=group_id, user_id=body.user_id):
        raise HTTPException(status_code=400, detail="User is already a member of this group")

    member = gs.add_group_member(db, group_id=group_id, user_id=body.user_id)
    gs.sync_new_member_to_existing_group_courses(
        db, group_id=group_id, user_id=body.user_id, assigned_by_id=_.id
    )
    db.commit()
    db.refresh(member)
    payload = GroupMemberResponse.model_validate(member).model_dump()
    return success_response(
        message="Learner added to group successfully",
        data=payload,
        status_code=status.HTTP_201_CREATED,
    )


@router.delete("/{group_id}/members/{user_id}")
def remove_group_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    """Remove a learner's membership from a group."""
    _get_group_or_404(db, group_id)

    removed = gs.remove_group_member(db, group_id=group_id, user_id=user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="User is not a member of this group")
    db.commit()
    return success_response(
        message="Learner removed from group successfully",
        data={"group_id": group_id, "user_id": user_id},
    )


# ── Group manager assignment (G004) — Administrator only ─────────────────────
# Assigning/removing a manager only ever touches group_managers: it does not
# add/remove GroupMember rows, does not touch CourseAssignment, and does not
# send notifications. Listing managers is a read of that same table, open to
# anyone who can already view the group.

@router.get("/{group_id}/managers")
def list_group_managers(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator", "Instructor")),
):
    """List instructors who manage a group. Scoped Instructors only see groups they manage."""
    _get_group_or_404(db, group_id)
    if not gs.can_view_group(db, current_user, group_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    rows = (
        db.query(GroupManager)
        .filter(GroupManager.group_id == group_id)
        .order_by(GroupManager.assigned_at.desc(), GroupManager.id.desc())
        .all()
    )
    payload = []
    for manager in rows:
        user = manager.user
        payload.append(
            GroupManagerDetailResponse(
                id=manager.id,
                group_id=manager.group_id,
                user_id=manager.user_id,
                full_name=user.full_name if user else None,
                email=user.email if user else "",
                assigned_at=manager.assigned_at,
            ).model_dump()
        )
    return success_response(message="Group managers fetched successfully", data=payload)


@router.post("/{group_id}/managers")
def assign_group_manager(
    group_id: int,
    body: GroupManagerBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    """Assign an existing Instructor as a manager of a group."""
    _get_group_or_404(db, group_id)

    user = db.query(User).filter(User.id == body.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not gs.is_instructor(user):
        raise HTTPException(
            status_code=400,
            detail="Only users with the Instructor role can be assigned as a group manager",
        )

    if gs.is_group_manager(db, group_id=group_id, user_id=body.user_id):
        raise HTTPException(status_code=400, detail="User is already a manager of this group")

    manager = gs.assign_group_manager(db, group_id=group_id, user_id=body.user_id)
    db.commit()
    db.refresh(manager)
    payload = GroupManagerResponse.model_validate(manager).model_dump()
    return success_response(
        message="Instructor assigned as group manager successfully",
        data=payload,
        status_code=status.HTTP_201_CREATED,
    )


@router.delete("/{group_id}/managers/{user_id}")
def remove_group_manager(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    """Remove an instructor's manager assignment from a group."""
    _get_group_or_404(db, group_id)

    removed = gs.remove_group_manager(db, group_id=group_id, user_id=user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="User is not a manager of this group")
    db.commit()
    return success_response(
        message="Group manager removed successfully",
        data={"group_id": group_id, "user_id": user_id},
    )


# ── Group course assignment (G006) + learner expansion (G007) ───────────────
# Assigning a course to a group records a group_course_assignments row AND
# creates a CourseAssignment (the existing, unchanged model) for every
# current Learner member who doesn't already have one for this course —
# see group_service.sync_group_course_assignment_to_learners() for the
# duplicate-safe expansion logic. Both inserts happen in one transaction
# (single db.commit() below), so a failure partway through leaves nothing
# committed. This never touches GroupMember/GroupManager and never sends
# notifications. Assign/remove are Administrator-only, following the same
# Administrator-only mutation convention as G003/G004/G005. List reuses the
# exact G005 visibility rule (can_view_group): Administrators see any
# group's courses, a scoped Instructor only sees courses for groups they
# actually manage.

@router.post("/{group_id}/courses")
def assign_group_course(
    group_id: int,
    body: GroupCourseAssignmentBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator")),
):
    """
    Assign a course to a group, then create a CourseAssignment for every
    current Learner member who doesn't already have one for this course.
    Reuses the existing CourseAssignment model/uniqueness rule — this does
    not create a second assignment system.
    """
    _get_group_or_404(db, group_id)

    course = gs.get_course(db, body.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if gs.is_group_course_assigned(db, group_id=group_id, course_id=body.course_id):
        raise HTTPException(status_code=400, detail="This course is already assigned to the group")

    assigned_at = datetime.utcnow()
    row = gs.assign_group_course(
        db,
        group_id=group_id,
        course_id=body.course_id,
        assigned_by_id=current_user.id,
        assigned_at=assigned_at,
    )
    gs.sync_group_course_assignment_to_learners(
        db,
        group_id=group_id,
        course=course,
        assigned_at=assigned_at,
        assigned_by_id=current_user.id,
    )
    db.commit()
    db.refresh(row)
    payload = GroupCourseAssignmentResponse.model_validate(row).model_dump()
    return success_response(
        message="Course assigned to group successfully",
        data=payload,
        status_code=status.HTTP_201_CREATED,
    )


@router.get("/{group_id}/courses")
def list_group_courses(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator", "Instructor")),
):
    """List the courses currently assigned to a group. A scoped Instructor may only view groups they manage."""
    _get_group_or_404(db, group_id)
    if not gs.can_view_group(db, current_user, group_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    courses = gs.get_group_courses(db, group_id)
    payload = [course_to_response(db, c).model_dump() for c in courses]
    return success_response(message="Group courses fetched successfully", data=payload)


@router.delete("/{group_id}/courses/{course_id}")
def remove_group_course(
    group_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    """Remove a course's assignment from a group. Does not delete the Course, existing individual
    CourseAssignments, GroupMember rows, or GroupManager rows."""
    _get_group_or_404(db, group_id)

    removed = gs.remove_group_course(db, group_id=group_id, course_id=course_id)
    if not removed:
        raise HTTPException(status_code=404, detail="This course is not assigned to the group")
    db.commit()
    return success_response(
        message="Course removed from group successfully",
        data={"group_id": group_id, "course_id": course_id},
    )
