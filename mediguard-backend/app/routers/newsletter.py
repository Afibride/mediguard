"""
Newsletter / health alert subscription for guest (non-registered) users.

Registered users use the User.notify_emails flag instead.

Endpoints
---------
POST /newsletter/subscribe          Subscribe with name + email
GET  /newsletter/unsubscribe        One-click unsubscribe via token in email link
POST /newsletter/unsubscribe        Unsubscribe by email (form-based fallback)
GET  /newsletter/status/{email}     Check subscription status (dev/admin use)
"""

import secrets

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.models import NewsletterSubscriber, User
from app.db.session import get_db
from app.utils.email import send_email, subscription_confirmation_email

router = APIRouter()


# ─── Schemas ─────────────────────────────────────────────────────────────────

class SubscribeRequest(BaseModel):
    email: EmailStr
    name: str | None = "Friend"


class UnsubscribeRequest(BaseModel):
    email: EmailStr


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _unsubscribe_url(token: str) -> str:
    from app.config import get_settings
    base = get_settings().frontend_url.rstrip("/")
    return f"{base}/newsletter/unsubscribe?token={token}"


# ─── POST /newsletter/subscribe ──────────────────────────────────────────────

@router.post("/subscribe")
def subscribe(
    body: SubscribeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Subscribe a guest email to monthly health digests and outbreak alerts."""
    email_lower = body.email.strip().lower()
    name = (body.name or "Friend").strip() or "Friend"

    # If this email belongs to a registered user, just enable their notify_emails flag
    registered = db.query(User).filter(User.email == email_lower).first()
    if registered:
        already_on = registered.notify_emails
        if not already_on:
            registered.notify_emails = True
            db.commit()
        # Send a confirmation email regardless (welcome back or first-time opt-in)
        from app.utils.email import registered_subscription_email
        subject, html, plain = registered_subscription_email(registered.full_name)
        background_tasks.add_task(send_email, email_lower, subject, html, plain)
        msg = (
            "Email notifications are already enabled on your account."
            if already_on else
            "Email notifications have been enabled on your account."
        )
        return {
            "message": f"You are already a MediGuard member. {msg} You'll receive outbreak alerts and monthly health digests.",
            "status": "registered_user",
        }

    # Check for existing subscriber
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == email_lower
    ).first()

    if existing:
        if existing.is_active:
            return {
                "message": "This email is already subscribed to MediGuard health alerts.",
                "status": "already_subscribed",
            }
        # Re-activate
        existing.is_active = True
        existing.name = name
        db.commit()
        unsub_url = _unsubscribe_url(existing.unsubscribe_token)
        subject, html, plain = subscription_confirmation_email(name, unsub_url)
        background_tasks.add_task(send_email, email_lower, subject, html, plain)
        return {
            "message": "You have been re-subscribed to MediGuard health alerts.",
            "status": "resubscribed",
        }

    # New subscriber
    token = secrets.token_urlsafe(32)
    sub = NewsletterSubscriber(
        email=email_lower,
        name=name,
        unsubscribe_token=token,
        is_active=True,
    )
    db.add(sub)
    db.commit()

    unsub_url = _unsubscribe_url(token)
    subject, html, plain = subscription_confirmation_email(name, unsub_url)
    background_tasks.add_task(send_email, email_lower, subject, html, plain)

    return {
        "message": "Successfully subscribed! A confirmation email has been sent.",
        "status": "subscribed",
    }


# ─── GET /newsletter/unsubscribe?token=... ───────────────────────────────────

@router.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_via_link(token: str, db: Session = Depends(get_db)):
    """One-click unsubscribe from a link in the email footer."""
    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.unsubscribe_token == token
    ).first()

    if not sub:
        return HTMLResponse(_unsubscribe_page(
            "Invalid link",
            "This unsubscribe link is invalid or has already been used.",
            success=False,
        ), status_code=404)

    if not sub.is_active:
        return HTMLResponse(_unsubscribe_page(
            "Already unsubscribed",
            f"{sub.email} is not currently subscribed to MediGuard health alerts.",
            success=False,
        ))

    sub.is_active = False
    db.commit()
    return HTMLResponse(_unsubscribe_page(
        "Unsubscribed",
        f"{sub.email} has been removed from MediGuard health alert emails. "
        "You can re-subscribe at any time on the MediGuard website.",
        success=True,
    ))


# ─── POST /newsletter/unsubscribe ─────────────────────────────────────────────

@router.post("/unsubscribe")
def unsubscribe_by_email(body: UnsubscribeRequest, db: Session = Depends(get_db)):
    """Form-based unsubscribe when the user doesn't have the token link."""
    email_lower = body.email.strip().lower()

    # Check registered users too
    registered = db.query(User).filter(User.email == email_lower).first()
    if registered and registered.notify_emails:
        registered.notify_emails = False
        db.commit()
        return {"message": "Email notifications have been disabled for your MediGuard account."}

    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == email_lower
    ).first()

    if not sub or not sub.is_active:
        # Don't reveal whether email exists
        return {"message": "If that email was subscribed, it has now been removed."}

    sub.is_active = False
    db.commit()
    return {"message": "You have been unsubscribed from MediGuard health alert emails."}


# ─── GET /newsletter/status/{email} ──────────────────────────────────────────

@router.get("/status/{email}")
def subscription_status(email: str, db: Session = Depends(get_db)):
    """Check whether an email is subscribed (for admin/debug purposes)."""
    email_lower = email.strip().lower()
    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == email_lower
    ).first()
    if not sub:
        return {"subscribed": False, "type": "none"}
    return {
        "subscribed": sub.is_active,
        "type": "newsletter",
        "name": sub.name,
        "subscribed_at": sub.subscribed_at.isoformat() if sub.subscribed_at else None,
    }


# ─── HTML helper ─────────────────────────────────────────────────────────────

def _unsubscribe_page(title: str, message: str, success: bool = True) -> str:
    color = "#0891b2" if success else "#dc2626"
    icon = "&#10003;" if success else "&#10007;"
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — MediGuard</title></head>
<body style="margin:0;padding:40px 16px;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;text-align:center;">
  <div style="max-width:480px;margin:0 auto;background:#fff;border-radius:12px;
              box-shadow:0 2px 12px rgba(0,0,0,0.08);padding:40px 32px;">
    <div style="font-size:48px;color:{color};margin:0 0 16px;">{icon}</div>
    <h1 style="color:#0f172a;margin:0 0 12px;font-size:22px;">{title}</h1>
    <p style="color:#64748b;margin:0 0 28px;line-height:1.6;">{message}</p>
    <a href="https://mediguard.info"
       style="display:inline-block;background:#0891b2;color:#fff;padding:12px 28px;
              border-radius:8px;text-decoration:none;font-weight:bold;font-size:14px;">
      Visit MediGuard
    </a>
  </div>
</body></html>"""
