from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, LoginResponse, MeResponse, UserBrief
from app.response import success_response
from app.security import create_token, get_current_user, verify_password

router = APIRouter()


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    payload = LoginResponse(
        access_token=create_token(user.id),
        user=UserBrief.model_validate(user),
        roles=[r.name for r in user.roles],
    )
    return success_response(message="Login successful", data=payload.model_dump())


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    payload = MeResponse(
        user=UserBrief.model_validate(current_user),
        roles=[r.name for r in current_user.roles],
    )
    return success_response(message="Profile fetched successfully", data=payload.model_dump())
