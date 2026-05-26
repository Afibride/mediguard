from app.data import DISEASES
from app.db.models import ChatFeedback, ChatLog, ContactMessage, Disease, NewsletterSubscriber, PasswordResetToken, PredictionFeedback, PredictionLog, User
from app.db.session import Base, engine
from app.db.session import SessionLocal
from sqlalchemy import inspect, text


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_chat_log_columns()
    ensure_user_columns()
    ensure_disease_columns()
    ensure_password_reset_token_columns()
    ensure_prediction_log_columns()
    seed_diseases()


def ensure_chat_log_columns() -> None:
    inspector = inspect(engine)
    if "chat_logs" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("chat_logs")}
    if engine.dialect.name == "postgresql":
        additions = {
            "follow_up_questions": "JSON DEFAULT '[]'::json",
            "pregnancy_context": "BOOLEAN DEFAULT false",
        }
    else:
        additions = {
            "follow_up_questions": "JSON DEFAULT '[]'",
            "pregnancy_context": "BOOLEAN DEFAULT 0",
        }
    with engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE chat_logs ADD COLUMN {column} {definition}"))


def ensure_user_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("users")}
    if engine.dialect.name == "postgresql":
        additions = {"notify_emails": "BOOLEAN NOT NULL DEFAULT true"}
    else:
        additions = {"notify_emails": "BOOLEAN NOT NULL DEFAULT 1"}
    with engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {column} {definition}"))


def ensure_password_reset_token_columns() -> None:
    inspector = inspect(engine)
    if "password_reset_tokens" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("password_reset_tokens")}
    additions = {"otp_code": "VARCHAR(6)"}
    with engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE password_reset_tokens ADD COLUMN {column} {definition}"))


def ensure_prediction_log_columns() -> None:
    inspector = inspect(engine)
    if "prediction_logs" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("prediction_logs")}
    additions = {"age_group": "VARCHAR(10)"}
    with engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE prediction_logs ADD COLUMN {column} {definition}"))


def ensure_disease_columns() -> None:
    inspector = inspect(engine)
    if "diseases" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("diseases")}
    additions = {"symptom_descriptions": "JSON DEFAULT '{}'"}
    with engine.begin() as connection:
        for column, definition in additions.items():
            if column not in existing:
                connection.execute(text(f"ALTER TABLE diseases ADD COLUMN {column} {definition}"))


def seed_diseases() -> None:
    db = SessionLocal()
    try:
        for item in DISEASES:
            disease = db.query(Disease).filter(Disease.slug == item["slug"]).first()
            payload = {
                "slug": item["slug"],
                "name": item["name"],
                "category": item["category"],
                "featured": bool(item.get("featured")),
                "severity": item.get("severity", "Medium"),
                "symptoms": item.get("symptoms", []),
                "description": item.get("description", ""),
                "causes": item.get("causes", ""),
                "treatment": item.get("treatment", ""),
                "prevention": item.get("prevention", []),
                "sections": item.get("sections", {}),
                "symptom_descriptions": item.get("symptom_descriptions", {}),
            }
            if disease:
                for key, value in payload.items():
                    setattr(disease, key, value)
            else:
                db.add(Disease(**payload))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
