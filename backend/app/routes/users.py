from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.response import success_response
from app.schemas import UserCreate, UserResponse, UserUpdate
from app.security import ROLE_NAMES, hash_password, require_roles

router = APIRouter()


def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[r.name for r in user.roles],
    )


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    users = db.query(User).order_by(User.id).all()
    payload = [user_to_response(u).model_dump() for u in users]
    return success_response(message="Users fetched successfully", data=payload)


@router.post("")
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    if body.role not in ROLE_NAMES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose from: {', '.join(ROLE_NAMES)}")
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    role = db.query(Role).filter(Role.name == body.role).first()
    user = User(
        email=email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name.strip(),
        is_active=True,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()
    db.refresh(user)
    payload = user_to_response(user).model_dump()
    return success_response(message="User created successfully", data=payload, status_code=status.HTTP_201_CREATED)


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("Administrator")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name.strip() or None
    if body.password:
        user.hashed_password = hash_password(body.password)
    if body.role is not None:
        if body.role not in ROLE_NAMES:
            raise HTTPException(status_code=400, detail=f"Invalid role. Choose from: {', '.join(ROLE_NAMES)}")
        role = db.query(Role).filter(Role.name == body.role).first()
        user.roles.clear()
        user.roles.append(role)
    db.commit()
    db.refresh(user)
    payload = user_to_response(user).model_dump()
    return success_response(message="User updated successfully", data=payload)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Administrator")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return success_response(message="User deleted successfully", data={"user_id": user_id})
