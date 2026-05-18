from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data import DISEASES
from app.db.models import ChatFeedback, Disease, PredictionFeedback, PredictionLog, User
from app.db.session import get_db
from app.utils.dependencies import get_current_user
from app.utils.email import is_rainy_season, outbreak_alert_email, send_email

router = APIRouter()

# ── Prevention tips (sent in outbreak notification emails) ───────────────────
_TIPS_RAINY = [
    {"disease": "Malaria Prevention", "tip": "Sleep under insecticide-treated nets every night. Empty or cover containers that collect rainwater — mosquitoes breed in stagnant water within days."},
    {"disease": "Cholera & Typhoid", "tip": "Drink only boiled, filtered, or treated water. Wash hands with soap before eating and after using the toilet. Avoid street food during peak rainy months."},
    {"disease": "Hygiene", "tip": "Keep your environment clean. Dispose of rubbish properly to prevent breeding sites for disease-carrying insects and rodents."},
]
_TIPS_DRY = [
    {"disease": "Meningitis & Respiratory", "tip": "Harmattan dust increases respiratory and meningitis risk. Wear a mask in dusty conditions, stay warm at night, and ensure your meningitis vaccination is up to date."},
    {"disease": "Dehydration", "tip": "Drink at least 2 litres of safe water daily. Eat fruits and vegetables, and rest in shade between 11am–3pm."},
    {"disease": "Skin & Eye Infections", "tip": "Dry air and dust irritate eyes and skin. Wash your face and hands regularly with clean water and avoid touching your eyes."},
]
_TIPS_GENERAL = [
    {"disease": "Vaccination", "tip": "Keep vaccination records up to date. Children should receive all scheduled vaccines. Adults should maintain tetanus coverage."},
    {"disease": "Early Screening", "tip": "Visit a health centre if symptoms persist more than 48 hours. Early diagnosis of malaria, typhoid, and TB greatly improves outcomes."},
]


def _compute_outbreak_alerts(db: Session) -> list[dict]:
    """Compute outbreak alert list — same logic as the frontend dashboard."""
    total = db.query(func.count(PredictionLog.id)).scalar() or 1
    rows = (
        db.query(PredictionLog.top_disease, func.count(PredictionLog.id).label("cnt"))
        .group_by(PredictionLog.top_disease)
        .order_by(func.count(PredictionLog.id).desc())
        .limit(10)
        .all()
    )
    rainy = is_rainy_season()
    alerts = []
    for disease, count in rows:
        if not disease:
            continue
        pct = round((count / total) * 100)
        level = None
        reason = f"{pct}% of all screenings"
        if pct >= 35:
            level = "high"
        elif pct >= 20:
            level = "medium"
        elif rainy and disease in {"Malaria", "Cholera"} and pct >= 10:
            level = "watch"
            reason = f"Rainy-season risk – {pct}% of screenings"
        if level:
            alerts.append({"disease": disease, "count": count, "pct": pct, "level": level, "reason": reason})
    return sorted(alerts, key=lambda a: {"high": 0, "medium": 1, "watch": 2}[a["level"]])


@router.get("/top-diseases")
def top_diseases(db: Session = Depends(get_db)):
    rows = (
        db.query(PredictionLog.top_disease, func.count(PredictionLog.id).label("count"))
        .group_by(PredictionLog.top_disease)
        .order_by(func.count(PredictionLog.id).desc())
        .limit(10)
        .all()
    )
    if rows:
        return [{"disease": disease, "name": disease, "count": count, "cases": count} for disease, count in rows]
    return [{"disease": d["name"], "name": d["name"], "count": max(20, 120 - i * 9), "cases": max(20, 120 - i * 9)} for i, d in enumerate(DISEASES[:10])]


@router.get("/trends")
def trends(db: Session = Depends(get_db)):
    rows = db.query(PredictionLog).order_by(PredictionLog.timestamp.asc()).all()
    if not rows:
        today = datetime.utcnow().date()
        return [
            {"week": str(today - timedelta(days=(7 * (5 - i)))), "disease": disease, "count": 10 + i * 4}
            for i, disease in enumerate(["Malaria", "Typhoid Fever", "Pneumonia", "Cholera", "Malaria", "Typhoid Fever"])
        ]
    buckets: dict[tuple[str, str], int] = {}
    for row in rows:
        week = (row.timestamp.date() - timedelta(days=row.timestamp.weekday())).isoformat()
        key = (week, row.top_disease or "Unknown")
        buckets[key] = buckets.get(key, 0) + 1
    return sorted(
        [{"week": week, "disease": disease, "count": count} for (week, disease), count in buckets.items()],
        key=lambda item: (item["week"], item["disease"]),
    )


@router.get("/heatmap")
def heatmap(db: Session = Depends(get_db)):
    rows = (
        db.query(PredictionLog.region, PredictionLog.top_disease, func.count(PredictionLog.id).label("count"))
        .group_by(PredictionLog.region, PredictionLog.top_disease)
        .order_by(func.count(PredictionLog.id).desc())
        .all()
    )
    if rows:
        return [{"region": region or "Bamenda", "disease": disease or "Unknown", "count": count} for region, disease, count in rows]
    return [{"region": "Bamenda", "disease": d["name"], "count": max(5, 80 - i * 6)} for i, d in enumerate(DISEASES[:10])]


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total_predictions = db.query(func.count(PredictionLog.id)).scalar() or 0
    disease_count = db.query(func.count(Disease.id)).scalar() or len(DISEASES)
    top = (
        db.query(PredictionLog.top_disease, func.count(PredictionLog.id).label("count"))
        .group_by(PredictionLog.top_disease)
        .order_by(func.count(PredictionLog.id).desc())
        .first()
    )
    week_start = datetime.utcnow() - timedelta(days=7)
    active_this_week = db.query(func.count(PredictionLog.id)).filter(PredictionLog.timestamp >= week_start).scalar() or 0

    total_feedback = db.query(func.count(PredictionFeedback.id)).scalar() or 0
    helpful_feedback = db.query(func.count(PredictionFeedback.id)).filter(PredictionFeedback.was_helpful == True).scalar() or 0  # noqa: E712
    feedback_accuracy = round((helpful_feedback / total_feedback) * 100, 1) if total_feedback > 0 else None

    return {
        "total_predictions": total_predictions,
        "top_disease": top[0] if top else "No predictions yet",
        "top_disease_count": top[1] if top else 0,
        "active_this_week": active_this_week,
        "diseases_tracked": disease_count,
        "region": "Bamenda",
        "total_feedback": total_feedback,
        "feedback_accuracy": feedback_accuracy,
    }


# ---------------------------------------------------------------------------
# POST /analytics/send-outbreak-alerts
# Compute outbreak alerts and email all opted-in users
# ---------------------------------------------------------------------------
@router.post("/send-outbreak-alerts")
def send_outbreak_alerts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    alerts = _compute_outbreak_alerts(db)
    if not alerts:
        return {"message": "No outbreak alerts detected — no emails sent.", "sent": 0}

    tips = (_TIPS_RAINY if is_rainy_season() else _TIPS_DRY) + _TIPS_GENERAL

    recipients = (
        db.query(User)
        .filter(User.is_active == True, User.notify_emails == True)  # noqa: E712
        .all()
    )

    for user in recipients:
        subject, html = outbreak_alert_email(user.full_name, alerts, tips)
        if subject:
            background_tasks.add_task(send_email, user.email, subject, html)

    return {
        "message": f"Outbreak alert emails queued for {len(recipients)} subscriber(s).",
        "sent": len(recipients),
        "alerts": alerts,
    }


# ---------------------------------------------------------------------------
# GET /analytics/outbreak-alerts (read-only, no auth needed)
# ---------------------------------------------------------------------------
@router.get("/outbreak-alerts")
def get_outbreak_alerts(db: Session = Depends(get_db)):
    """Return current outbreak alerts without sending emails."""
    alerts = _compute_outbreak_alerts(db)
    return {
        "alerts": alerts,
        "rainy_season": is_rainy_season(),
        "has_alerts": bool(alerts),
    }


# ---------------------------------------------------------------------------
# GET /analytics/chat-insights
# ---------------------------------------------------------------------------
@router.get("/chat-insights")
def chat_insights(db: Session = Depends(get_db)):
    """Return AI chat satisfaction metrics and weak topic analysis."""
    total = db.query(func.count(ChatFeedback.id)).scalar() or 0
    helpful = db.query(func.count(ChatFeedback.id)).filter(ChatFeedback.rating == True).scalar() or 0  # noqa: E712
    satisfaction = round((helpful / total) * 100, 1) if total > 0 else None

    cutoff = datetime.utcnow() - timedelta(days=30)
    low_rated = (
        db.query(ChatFeedback)
        .filter(ChatFeedback.rating == False, ChatFeedback.created_at >= cutoff)  # noqa: E712
        .order_by(ChatFeedback.created_at.desc())
        .limit(100)
        .all()
    )

    kw_counts: Counter = Counter()
    for row in low_rated:
        for kw in (row.query_keywords or []):
            kw_counts[kw.lower()] += 1

    top_weak_keywords = [{"keyword": k, "count": v} for k, v in kw_counts.most_common(10)]
    recent_low_rated = [
        {"query": r.query[:120], "created_at": r.created_at.isoformat()}
        for r in low_rated[:8]
    ]

    return {
        "total_ratings": total,
        "helpful_count": helpful,
        "unhelpful_count": total - helpful,
        "satisfaction_pct": satisfaction,
        "top_weak_keywords": top_weak_keywords,
        "recent_low_rated": recent_low_rated,
    }
