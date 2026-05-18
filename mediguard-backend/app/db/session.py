from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings


def _build_engine():
    settings = get_settings()
    raw_url = settings.active_database_url

    if raw_url.startswith("sqlite"):
        return create_engine(raw_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)

    # Normalise postgres:// → postgresql+psycopg:// for psycopg3
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)

    # Parse the URL so we can lift driver-specific params into connect_args
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query, keep_blank_values=True)

    # channel_binding must go to connect_args, not the SQLAlchemy URL
    connect_args: dict = {}
    if "channel_binding" in qs:
        connect_args["channel_binding"] = qs.pop("channel_binding")[0]

    # Rebuild clean URL and switch to psycopg3 dialect
    clean_query = urlencode({k: v[0] for k, v in qs.items()})
    sa_url = urlunparse(parsed._replace(scheme="postgresql+psycopg", query=clean_query))

    return create_engine(
        sa_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        # Neon serverless pooler works best with a small pool
        pool_size=5,
        max_overflow=10,
    )


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
