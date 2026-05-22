from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.init_db import init_db
from app.ml.model_store import ensure_model_files

settings = get_settings()
app = FastAPI(title="MediGuard API", version="1.0.0")
model_status = ensure_model_files()
init_db()

from app.routers import analytics, auth, chat, contact, diseases, history, predict  # noqa: E402

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


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(predict.router, tags=["Predict"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(diseases.router, prefix="/diseases", tags=["Diseases"])
app.include_router(history.router, prefix="/history", tags=["History"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(contact.router, prefix="/contact", tags=["Contact"])
