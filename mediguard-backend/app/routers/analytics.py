from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data import DISEASES
from app.db.models import Disease, PredictionFeedback, PredictionLog
from app.db.session import get_db

router = APIRouter()


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
