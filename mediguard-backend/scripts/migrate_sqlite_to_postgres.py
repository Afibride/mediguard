"""
Copy MediGuard data from local SQLite into a PostgreSQL database.

Usage from mediguard-backend:
    $env:TARGET_DATABASE_URL="postgresql://..."
    python scripts/migrate_sqlite_to_postgres.py

The migration creates missing tables and upserts rows by primary key. It does
not drop remote tables.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.models import (  # noqa: E402,F401 - imported to register metadata
    ChatFeedback,
    ChatLog,
    ContactMessage,
    Disease,
    PasswordResetToken,
    PredictionFeedback,
    PredictionLog,
    User,
)
from app.db.session import Base  # noqa: E402


SOURCE_DATABASE_URL = os.environ.get("SOURCE_DATABASE_URL", "sqlite:///./mediguard.db")
TARGET_DATABASE_URL = os.environ.get("TARGET_DATABASE_URL")

TABLE_ORDER = [
    User.__table__,
    Disease.__table__,
    PasswordResetToken.__table__,
    PredictionLog.__table__,
    ChatLog.__table__,
    ContactMessage.__table__,
    ChatFeedback.__table__,
    PredictionFeedback.__table__,
]


def normalize_postgres_url(raw_url: str) -> tuple[str, dict]:
    if raw_url.startswith("postgres://"):
        raw_url = raw_url.replace("postgres://", "postgresql://", 1)
    parsed = urlparse(raw_url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    connect_args = {}
    if "channel_binding" in qs:
        connect_args["channel_binding"] = qs.pop("channel_binding")[0]
    clean_query = urlencode({key: value[0] for key, value in qs.items()})
    return urlunparse(parsed._replace(scheme="postgresql+psycopg", query=clean_query)), connect_args


def make_engine(url: str):
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    postgres_url, connect_args = normalize_postgres_url(url)
    return create_engine(postgres_url, connect_args=connect_args, pool_pre_ping=True)


def upsert_rows(source_engine, target_engine, table) -> int:
    with source_engine.connect() as source:
        rows = [dict(row) for row in source.execute(select(table)).mappings().all()]
    if not rows:
        return 0

    primary_keys = [column.name for column in table.primary_key.columns]
    insert_stmt = pg_insert(table).values(rows)
    update_columns = {
        column.name: getattr(insert_stmt.excluded, column.name)
        for column in table.columns
        if column.name not in primary_keys
    }
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=primary_keys,
        set_=update_columns,
    )
    with target_engine.begin() as target:
        target.execute(upsert_stmt)
    return len(rows)


def reset_sequence(target_engine, table) -> None:
    if "id" not in table.c:
        return
    with target_engine.begin() as target:
        target.execute(
            text(
                "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
                "COALESCE((SELECT MAX(id) FROM \"{table}\"), 1), true)"
                .format(table=table.name)
            ),
            {"table_name": table.name},
        )


def main() -> None:
    if not TARGET_DATABASE_URL:
        raise SystemExit("TARGET_DATABASE_URL is required.")

    source_engine = make_engine(SOURCE_DATABASE_URL)
    target_engine = make_engine(TARGET_DATABASE_URL)
    Base.metadata.create_all(bind=target_engine)

    total = 0
    for table in TABLE_ORDER:
        count = upsert_rows(source_engine, target_engine, table)
        reset_sequence(target_engine, table)
        total += count
        print(f"{table.name}: migrated {count} row(s)")

    print(f"Migration complete: {total} total row(s) copied.")


if __name__ == "__main__":
    main()
