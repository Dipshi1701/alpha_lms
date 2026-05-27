from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.response import success_response
from app.schemas import NotificationPatchBody, NotificationResponse, NotificationsListResponse
from app.security import get_current_user
from app.services import notification_service as ns

router = APIRouter()


def _to_response(n) -> NotificationResponse:
    return NotificationResponse.model_validate(n)


@router.get("")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for the logged-in user plus unread count."""
    rows = ns.list_for_user(db, current_user.id)
    unread = ns.unread_count_for_user(db, current_user.id)
    payload = NotificationsListResponse(
        items=[_to_response(n) for n in rows],
        unread_count=unread,
    )
    return success_response(
        message="Notifications fetched successfully",
        data=payload.model_dump(),
    )


@router.patch("")
def patch_notifications(
    body: NotificationPatchBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark one notification read (id) or all (read_all)."""
    if body.read_all:
        count = ns.mark_all_read(db, user_id=current_user.id)
        db.commit()
        return success_response(
            message="All notifications marked as read",
            data={"marked_count": count},
        )
    if body.id is None:
        raise HTTPException(status_code=400, detail="Provide id or read_all=true")
    ok = ns.mark_read(db, user_id=current_user.id, notification_id=body.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.commit()
    return success_response(
        message="Notification marked as read",
        data={"id": body.id},
    )
