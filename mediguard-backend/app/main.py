import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.init_db import init_db
from app.ml.model_store import ensure_model_files

logger = logging.getLogger(__name__)

settings = get_settings()
app = FastAPI(title="MediGuard API", version="1.0.0")
model_status = ensure_model_files()
init_db()

from app.routers import admin, analytics, auth, chat, contact, diseases, history, newsletter, predict  # noqa: E402

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "MediGuard API", "models": model_status}


@app.get("/seasonal-context", tags=["Health Context"])
def seasonal_context(month: int | None = None):
    """Return current seasonal disease risks for Bamenda, NW Cameroon.

    Query param ``month`` (1–12) overrides the current calendar month — useful
    for testing. Returns high/medium risk diseases, explanations, and a
    banner text string for the frontend.
    """
    from app.rag.retriever import get_seasonal_context
    return get_seasonal_context(month)


# ---------------------------------------------------------------------------
# POST /admin/model-update
# Manually trigger a model refresh from Hugging Face (admin-only).
# Useful after pushing a new training run to HF without restarting the server.
# ---------------------------------------------------------------------------
@app.post("/admin/model-update", tags=["Admin"])
async def trigger_model_update(
    _user=__import__("fastapi").Depends(
        __import__("app.utils.dependencies", fromlist=["get_current_user"]).get_current_user
    )
):
    """Force-check Hugging Face for updated model artefacts and reload the predictor."""
    results = await asyncio.to_thread(
        __import__("app.ml.model_store", fromlist=["check_and_update_models"]).check_and_update_models
    )
    updated = [k for k, v in results.items() if v in ("updated", "downloaded")]
    if updated:
        try:
            from app.rag.retriever import _get_predictor
            _get_predictor(_reload=True)
            reload_msg = "Predictor reloaded."
        except Exception:
            reload_msg = "Models updated on disk — restart server to apply."
        return {"message": f"{len(updated)} model(s) updated: {', '.join(updated)}. {reload_msg}", "results": results}
    return {"message": "All models are already up to date.", "results": results}


app.include_router(auth.router,        prefix="/auth",        tags=["Auth"])
app.include_router(predict.router,                            tags=["Predict"])
app.include_router(chat.router,                               tags=["Chat"])
app.include_router(diseases.router,    prefix="/diseases",    tags=["Diseases"])
app.include_router(history.router,     prefix="/history",     tags=["History"])
app.include_router(analytics.router,   prefix="/analytics",   tags=["Analytics"])
app.include_router(contact.router,     prefix="/contact",     tags=["Contact"])
app.include_router(newsletter.router,  prefix="/newsletter",  tags=["Newsletter"])
app.include_router(admin.router,                             tags=["Admin"])


# ---------------------------------------------------------------------------
# Scheduled monthly health digest
# Runs at 08:00 UTC on the 1st of every month.
# Sends disease trends + outbreak alerts to all opted-in registered users
# and all active newsletter subscribers.
# ---------------------------------------------------------------------------

async def _run_monthly_digest() -> None:
    """Background coroutine that sends the monthly digest to all subscribers."""
    from datetime import datetime
    from sqlalchemy import func
    from app.db.session import SessionLocal
    from app.db.models import NewsletterSubscriber, PredictionLog, User
    from app.routers.analytics import _compute_outbreak_alerts, _TIPS_RAINY, _TIPS_DRY, _TIPS_GENERAL
    from app.utils.email import is_rainy_season, monthly_digest_email, send_email

    db = SessionLocal()
    try:
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        rows = (
            db.query(PredictionLog.top_disease, func.count(PredictionLog.id).label("cnt"))
            .filter(PredictionLog.timestamp >= month_start)
            .filter(PredictionLog.top_disease.isnot(None))
            .group_by(PredictionLog.top_disease)
            .order_by(func.count(PredictionLog.id).desc())
            .limit(5)
            .all()
        )
        if not rows:
            logger.info("Monthly digest: no screening data this month — skipping send.")
            return

        total = db.query(func.count(PredictionLog.id)).filter(
            PredictionLog.timestamp >= month_start
        ).scalar() or 1
        top_diseases = [
            {"disease": d, "count": c, "pct": round((c / total) * 100)}
            for d, c in rows if d
        ]

        alerts = _compute_outbreak_alerts(db)
        tips = (_TIPS_RAINY if is_rainy_season() else _TIPS_DRY) + _TIPS_GENERAL
        month_year = datetime.utcnow().strftime("%B %Y")
        base_url = settings.frontend_url.rstrip("/")

        registered = (
            db.query(User)
            .filter(User.is_active == True, User.notify_emails == True)  # noqa: E712
            .all()
        )
        guests = (
            db.query(NewsletterSubscriber)
            .filter(NewsletterSubscriber.is_active == True)  # noqa: E712
            .all()
        )

        tasks = []
        for user in registered:
            subject, html, plain = monthly_digest_email(
                str(user.full_name), top_diseases, alerts, tips, month_year
            )
            tasks.append(send_email(str(user.email), subject, html, plain))

        for sub in guests:
            unsub_url = f"{base_url}/newsletter/unsubscribe?token={sub.unsubscribe_token}"
            subject, html, plain = monthly_digest_email(
                str(sub.name), top_diseases, alerts, tips, month_year, unsub_url
            )
            tasks.append(send_email(str(sub.email), subject, html, plain))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        sent = sum(1 for r in results if r is True)
        logger.info(
            "Monthly digest sent: %d/%d emails delivered (%d registered, %d newsletter)",
            sent, len(tasks), len(registered), len(guests),
        )
    except Exception as exc:
        logger.error("Monthly digest job failed: %s", exc, exc_info=True)
    finally:
        db.close()


async def _run_outbreak_alerts() -> None:
    """Background coroutine that sends current outbreak warnings to subscribers."""
    from app.db.session import SessionLocal
    from app.db.models import NewsletterSubscriber, User
    from app.routers.analytics import _compute_outbreak_alerts, _TIPS_RAINY, _TIPS_DRY, _TIPS_GENERAL
    from app.utils.email import is_rainy_season, outbreak_alert_email, send_email

    db = SessionLocal()
    try:
        alerts = _compute_outbreak_alerts(db)
        if not alerts:
            logger.info("Outbreak warning job: no alert threshold reached - skipping send.")
            return

        tips = (_TIPS_RAINY if is_rainy_season() else _TIPS_DRY) + _TIPS_GENERAL
        base_url = settings.frontend_url.rstrip("/")

        registered = (
            db.query(User)
            .filter(User.is_active == True, User.notify_emails == True)  # noqa: E712
            .all()
        )
        guests = (
            db.query(NewsletterSubscriber)
            .filter(NewsletterSubscriber.is_active == True)  # noqa: E712
            .all()
        )

        tasks = []
        for user in registered:
            subject, html, plain = outbreak_alert_email(str(user.full_name), alerts, tips)
            if subject:
                tasks.append(send_email(str(user.email), subject, html, plain))

        for sub in guests:
            unsub_url = f"{base_url}/newsletter/unsubscribe?token={sub.unsubscribe_token}"
            subject, html, plain = outbreak_alert_email(str(sub.name), alerts, tips, unsubscribe_url=unsub_url)
            if subject:
                tasks.append(send_email(str(sub.email), subject, html, plain))

        if not tasks:
            logger.info("Outbreak warning job: alerts found but no opted-in recipients.")
            return

        results = await asyncio.gather(*tasks, return_exceptions=True)
        sent = sum(1 for r in results if r is True)
        logger.info(
            "Outbreak warnings sent: %d/%d emails delivered (%d registered, %d newsletter)",
            sent, len(tasks), len(registered), len(guests),
        )
    except Exception as exc:
        logger.error("Outbreak warning job failed: %s", exc, exc_info=True)
    finally:
        db.close()


async def _run_model_update_check() -> None:
    """Check Hugging Face for updated model artefacts and hot-swap any that changed."""
    from app.ml.model_store import check_and_update_models
    results = await asyncio.to_thread(check_and_update_models)
    updated = [k for k, v in results.items() if v in ("updated", "downloaded")]
    if updated:
        logger.info(
            "Model update check: %d file(s) refreshed from Hugging Face: %s",
            len(updated), ", ".join(updated),
        )
        # Reload the predictor so it immediately uses the new models
        try:
            from app.rag.retriever import _get_predictor
            _get_predictor(_reload=True)
            logger.info("Predictor reloaded with updated models.")
        except Exception as exc:
            logger.warning("Could not auto-reload predictor: %s — restart server to apply.", exc)
    else:
        logger.debug("Model update check: all files up to date.")


def _setup_scheduler() -> None:
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.interval import IntervalTrigger

        scheduler = AsyncIOScheduler(timezone="UTC")

        # 1st of every month at 08:00 UTC — monthly health digest emails
        scheduler.add_job(
            _run_monthly_digest,
            CronTrigger(day=1, hour=8, minute=0),
            id="monthly_digest",
            name="Monthly Health Digest",
            replace_existing=True,
        )

        scheduler.add_job(
            _run_outbreak_alerts,
            CronTrigger(day_of_week="mon", hour=8, minute=30),
            id="weekly_outbreak_warnings",
            name="Weekly Outbreak Warning Emails",
            replace_existing=True,
        )

        # Every 6 hours — check Hugging Face for updated model files
        scheduler.add_job(
            _run_model_update_check,
            IntervalTrigger(hours=6),
            id="model_update_check",
            name="HuggingFace Model Update Check",
            replace_existing=True,
        )

        scheduler.start()
        logger.info(
            "APScheduler started — monthly digest on 1st of month at 08:00 UTC, "
            "weekly outbreak warnings every Monday at 08:30 UTC, "
            "model update check every 6 hours."
        )

        # Store on app so shutdown can stop it
        app.state.scheduler = scheduler
    except ImportError:
        logger.warning(
            "APScheduler not installed — monthly digest emails and model updates will not run automatically. "
            "Install with: pip install apscheduler"
        )
    except Exception as exc:
        logger.error("Failed to start scheduler: %s", exc)


@app.on_event("startup")
async def startup_event() -> None:
    _setup_scheduler()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped.")
