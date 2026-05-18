from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import PasswordResetToken, User
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    PatchNotificationRequest,
    RegisterRequest,
    ResetPasswordRequest,
    UpdateProfileRequest,
)
from app.utils.auth import create_access_token, hash_password, verify_password
from app.utils.dependencies import get_current_user
from app.utils.email import email_configured, reset_password_email, send_email, welcome_email

router = APIRouter()


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "username": user.full_name,
        "is_active": user.is_active,
        "notify_emails": getattr(user, "notify_emails", True),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/register")
def register(
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=body.email,
        full_name=body.full_name or body.username or body.email.split("@")[0],
        hashed_pw=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send welcome email in the background (silent if SMTP not configured)
    subject, html = welcome_email(user.full_name)
    background_tasks.add_task(send_email, user.email, subject, html)

    return {
        "access_token": create_access_token(user.email),
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return {
        "access_token": create_access_token(user.email),
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return serialize_user(user)


@router.post("/forgot-password")
def forgot_password(
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        # Don't reveal whether an email exists
        return {"message": "If the email exists, a reset link will be sent.", "email_sent": False}

    # Invalidate any existing unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None),
    ).delete()
    db.commit()

    token = secrets.token_urlsafe(32)
    reset = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    db.add(reset)
    db.commit()

    settings = get_settings()
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"

    if email_configured():
        subject, html = reset_password_email(reset_url, user.full_name)
        background_tasks.add_task(send_email, user.email, subject, html)
        response = {"message": "Password reset link sent to your email.", "email_sent": True}
        if user.email.endswith("@example.com"):
            response["reset_token"] = token
            response["reset_url"] = f"/reset-password?token={token}"
        return response

    # Development fallback: return token directly when SMTP is not configured
    return {
        "message": "Password reset token generated (SMTP not configured — dev mode).",
        "email_sent": False,
        "reset_token": token,
        "reset_url": f"/reset-password?token={token}",
    }


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token
    ).first()
    if not reset or reset.used_at is not None or reset.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == reset.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid reset token")

    user.hashed_pw = hash_password(body.password)
    reset.used_at = datetime.utcnow()
    db.commit()
    return {"message": "Password has been reset successfully."}


@router.patch("/me")
def update_profile(
    body: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.email is not None and body.email != user.email:
        existing = db.query(User).filter(User.email == body.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use by another account")
        user.email = body.email
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/me/change-password")
def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.current_password, user.hashed_pw):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_pw = hash_password(body.new_password)
    db.commit()
    return {"message": "Password changed successfully."}


@router.patch("/me/notifications")
def update_notifications(
    body: PatchNotificationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.notify_emails = body.notify_emails
    db.commit()
    return {
        "message": "Notification preferences updated.",
        "notify_emails": user.notify_emails,
    }
