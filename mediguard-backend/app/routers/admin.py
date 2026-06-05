"""
MediGuard Admin API
-------------------
All routes require a valid admin JWT (is_admin=True on the User row).
Frontend accesses this at /admin/* — no public link exists in the main UI.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    ChatFeedback,
    ChatLog,
    ContactMessage,
    Disease,
    NewsletterSubscriber,
    PredictionFeedback,
    PredictionLog,
    User,
)
from app.db.session import SessionLocal
from app.utils.auth import create_access_token, hash_password, verify_password
from app.utils.dependencies import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Admin guard — all admin endpoints pass through this
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: dict


class UserUpdateRequest(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class DiseaseUpdateRequest(BaseModel):
    featured: Optional[bool] = None
    severity: Optional[str] = None
    description: Optional[str] = None


class NewsletterSendRequest(BaseModel):
    subject: str
    body: str


class SubscriberUpdateRequest(BaseModel):
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Auth — admin-specific login
# ---------------------------------------------------------------------------

@router.post("/auth/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not an admin account")
    token = create_access_token(subject=user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
        },
    }


@router.get("/auth/me")
def admin_me(current_user: User = Depends(require_admin)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_admin": current_user.is_admin,
    }


# ---------------------------------------------------------------------------
# Dashboard stats
# ---------------------------------------------------------------------------

@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    total_predictions = db.query(func.count(PredictionLog.id)).scalar() or 0
    total_chats = db.query(func.count(ChatLog.id)).scalar() or 0
    total_subscribers = db.query(func.count(NewsletterSubscriber.id)).scalar() or 0
    active_subscribers = (
        db.query(func.count(NewsletterSubscriber.id))
        .filter(NewsletterSubscriber.is_active == True)
        .scalar() or 0
    )
    unread_messages = (
        db.query(func.count(ContactMessage.id))
        .filter(ContactMessage.read_at == None)
        .scalar() or 0
    )
    helpful_feedback = (
        db.query(func.count(ChatFeedback.id))
        .filter(ChatFeedback.rating == True)
        .scalar() or 0
    )
    total_feedback = db.query(func.count(ChatFeedback.id)).scalar() or 0

    # Top 5 diseases from prediction logs
    top_diseases = (
        db.query(PredictionLog.top_disease, func.count(PredictionLog.id).label("count"))
        .filter(PredictionLog.top_disease.isnot(None))
        .group_by(PredictionLog.top_disease)
        .order_by(func.count(PredictionLog.id).desc())
        .limit(5)
        .all()
    )

    # Recent 7-day activity
    seven_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    seven_days_ago -= timedelta(days=7)
    recent_predictions = (
        db.query(func.count(PredictionLog.id))
        .filter(PredictionLog.timestamp >= seven_days_ago)
        .scalar() or 0
    )
    recent_users = (
        db.query(func.count(User.id))
        .filter(User.created_at >= seven_days_ago)
        .scalar() or 0
    )

    return {
        "users": {"total": total_users, "active": active_users, "new_7d": recent_users},
        "predictions": {"total": total_predictions, "new_7d": recent_predictions},
        "chats": {"total": total_chats},
        "newsletter": {"total": total_subscribers, "active": active_subscribers},
        "messages": {"unread": unread_messages},
        "feedback": {
            "total": total_feedback,
            "helpful": helpful_feedback,
            "satisfaction_pct": round((helpful_feedback / total_feedback * 100) if total_feedback else 0),
        },
        "top_diseases": [{"name": d, "count": c} for d, c in top_diseases],
    }


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: str = Query(""),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(User)
    if search:
        q = q.filter(
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
    total = q.count()
    users = q.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "is_active": u.is_active,
                "is_admin": u.is_admin,
                "notify_emails": u.notify_emails,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ],
    }


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own admin account here")
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    db.commit()
    return {"message": "User updated", "user_id": user_id}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


# ---------------------------------------------------------------------------
# Newsletter management
# ---------------------------------------------------------------------------

@router.get("/newsletter")
def list_subscribers(
    page: int = Query(1, ge=1),
    limit: int = Query(30, le=200),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(NewsletterSubscriber)
    if active_only:
        q = q.filter(NewsletterSubscriber.is_active == True)
    total = q.count()
    subs = q.order_by(NewsletterSubscriber.subscribed_at.desc()).offset((page - 1) * limit).limit(limit).all()

    # Also count registered users who opted in to emails
    registered_opted_in = (
        db.query(func.count(User.id)).filter(User.notify_emails == True, User.is_active == True).scalar() or 0
    )

    return {
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
        "registered_opted_in": registered_opted_in,
        "subscribers": [
            {
                "id": s.id,
                "email": s.email,
                "name": s.name,
                "is_active": s.is_active,
                "subscribed_at": s.subscribed_at.isoformat() if s.subscribed_at else None,
            }
            for s in subs
        ],
    }


@router.patch("/newsletter/{subscriber_id}")
def update_subscriber(
    subscriber_id: int,
    payload: SubscriberUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    sub = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.id == subscriber_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    if payload.is_active is not None:
        sub.is_active = payload.is_active
    db.commit()
    return {"message": "Subscriber updated"}


@router.delete("/newsletter/{subscriber_id}")
def delete_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    sub = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.id == subscriber_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    db.delete(sub)
    db.commit()
    return {"message": "Subscriber removed"}


@router.post("/newsletter/send")
def send_newsletter(
    payload: NewsletterSendRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Send a custom newsletter to all active subscribers and opted-in registered users."""
    from app.utils.email import send_email

    subscribers = (
        db.query(NewsletterSubscriber)
        .filter(NewsletterSubscriber.is_active == True)
        .all()
    )
    registered = (
        db.query(User)
        .filter(User.notify_emails == True, User.is_active == True)
        .all()
    )

    sent_to = set()
    success = 0
    failed = 0

    all_recipients = (
        [(s.email, s.name) for s in subscribers]
        + [(u.email, u.full_name) for u in registered]
    )

    for email, name in all_recipients:
        if email in sent_to:
            continue
        sent_to.add(email)
        try:
            send_email(
                to_email=email,
                subject=payload.subject,
                html_body=f"<p>Hi {name},</p>{payload.body}<p>— MediGuard Team</p>",
            )
            success += 1
        except Exception:
            failed += 1

    return {
        "message": f"Newsletter sent to {success} recipients ({failed} failed)",
        "sent": success,
        "failed": failed,
    }


# ---------------------------------------------------------------------------
# Trends / Analytics
# ---------------------------------------------------------------------------

@router.get("/trends")
def admin_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(days=days)

    # Daily prediction counts
    daily = (
        db.query(
            func.date(PredictionLog.timestamp).label("day"),
            func.count(PredictionLog.id).label("count"),
        )
        .filter(PredictionLog.timestamp >= since)
        .group_by(func.date(PredictionLog.timestamp))
        .order_by(func.date(PredictionLog.timestamp))
        .all()
    )

    # Disease distribution
    disease_dist = (
        db.query(PredictionLog.top_disease, func.count(PredictionLog.id).label("count"))
        .filter(PredictionLog.top_disease.isnot(None), PredictionLog.timestamp >= since)
        .group_by(PredictionLog.top_disease)
        .order_by(func.count(PredictionLog.id).desc())
        .limit(10)
        .all()
    )

    # Age group distribution
    age_dist = (
        db.query(PredictionLog.age_group, func.count(PredictionLog.id).label("count"))
        .filter(PredictionLog.age_group.isnot(None), PredictionLog.timestamp >= since)
        .group_by(PredictionLog.age_group)
        .order_by(func.count(PredictionLog.id).desc())
        .all()
    )

    # Chat feedback over period
    helpful = (
        db.query(func.count(ChatFeedback.id))
        .filter(ChatFeedback.rating == True, ChatFeedback.created_at >= since)
        .scalar() or 0
    )
    not_helpful = (
        db.query(func.count(ChatFeedback.id))
        .filter(ChatFeedback.rating == False, ChatFeedback.created_at >= since)
        .scalar() or 0
    )

    return {
        "period_days": days,
        "daily_predictions": [{"day": str(d), "count": c} for d, c in daily],
        "disease_distribution": [{"name": d, "count": c} for d, c in disease_dist],
        "age_distribution": [{"group": g, "count": c} for g, c in age_dist],
        "feedback": {"helpful": helpful, "not_helpful": not_helpful},
    }


# ---------------------------------------------------------------------------
# Disease management
# ---------------------------------------------------------------------------

@router.get("/diseases")
def list_diseases(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    search: str = Query(""),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(Disease)
    if search:
        q = q.filter(Disease.name.ilike(f"%{search}%") | Disease.category.ilike(f"%{search}%"))
    total = q.count()
    diseases = q.order_by(Disease.name).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
        "diseases": [
            {
                "id": d.id,
                "slug": d.slug,
                "name": d.name,
                "category": d.category,
                "severity": d.severity,
                "featured": d.featured,
                "symptom_count": len(d.symptoms or []),
                "description": (d.description or "")[:150],
            }
            for d in diseases
        ],
    }


@router.patch("/diseases/{slug}")
def update_disease(
    slug: str,
    payload: DiseaseUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    disease = db.query(Disease).filter(Disease.slug == slug).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    if payload.featured is not None:
        disease.featured = payload.featured
    if payload.severity is not None:
        if payload.severity not in ("Low", "Medium", "High"):
            raise HTTPException(status_code=400, detail="severity must be Low, Medium, or High")
        disease.severity = payload.severity
    if payload.description is not None:
        disease.description = payload.description
    disease.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Disease updated", "slug": slug}


# ---------------------------------------------------------------------------
# Contact messages
# ---------------------------------------------------------------------------

@router.get("/messages")
def list_messages(
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(ContactMessage)
    if unread_only:
        q = q.filter(ContactMessage.read_at == None)
    total = q.count()
    messages = q.order_by(ContactMessage.sent_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
        "messages": [
            {
                "id": m.id,
                "name": m.name,
                "email": m.email,
                "subject": m.subject,
                "message": m.message,
                "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                "read": m.read_at is not None,
                "read_at": m.read_at.isoformat() if m.read_at else None,
            }
            for m in messages
        ],
    }


@router.patch("/messages/{message_id}/read")
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.read_at = datetime.utcnow()
    db.commit()
    return {"message": "Marked as read"}


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
    return {"message": "Message deleted"}


# ---------------------------------------------------------------------------
# Feedback review
# ---------------------------------------------------------------------------

@router.get("/feedback")
def list_feedback(
    page: int = Query(1, ge=1),
    limit: int = Query(30, le=100),
    helpful: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    q = db.query(ChatFeedback)
    if helpful is not None:
        q = q.filter(ChatFeedback.rating == helpful)
    total = q.count()
    items = q.order_by(ChatFeedback.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "total": total,
        "page": page,
        "pages": max(1, (total + limit - 1) // limit),
        "feedback": [
            {
                "id": f.id,
                "query": f.query,
                "response_preview": f.response_preview,
                "helpful": f.rating,
                "mode": f.mode,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in items
        ],
    }
