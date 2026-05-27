"""Create and query in-app notifications."""

from sqlalchemy.orm import Session

from app.models import Course, Notification

NOTIFICATION_TYPE_COURSE_ASSIGNED = "course_assigned"


def notify_course_assigned(db: Session, *, user_ids: list[int], course: Course) -> None:
    """Insert a course-assigned notification for each user (caller commits)."""
    if not user_ids:
        return
    title = "New course assigned"
    message = f'You have been assigned to "{course.title}".'
    for uid in user_ids:
        db.add(
            Notification(
                user_id=uid,
                type=NOTIFICATION_TYPE_COURSE_ASSIGNED,
                title=title,
                message=message,
                course_id=course.id,
                read=False,
            )
        )


def list_for_user(db: Session, user_id: int, *, limit: int = 50) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


def unread_count_for_user(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read.is_(False))
        .count()
    )


def mark_read(db: Session, *, user_id: int, notification_id: int) -> bool:
    row = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not row:
        return False
    row.read = True
    return True


def mark_all_read(db: Session, *, user_id: int) -> int:
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read.is_(False))
        .all()
    )
    for row in rows:
        row.read = True
    return len(rows)
