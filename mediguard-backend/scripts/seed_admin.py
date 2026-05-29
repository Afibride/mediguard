"""
seed_admin.py
=============
Creates the admin user and adds the is_admin column if it doesn't exist.

Run from mediguard-backend/:
    python scripts/seed_admin.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from app.db.session import SessionLocal, engine
from app.db.models import Base, User
from app.utils.auth import hash_password

ADMIN_EMAIL = "afibright07@gmail.com"
ADMIN_PASSWORD = "Mediguard.info"
ADMIN_NAME = "MediGuard Admin"


def run():
    # Ensure tables exist (creates is_admin column if schema is new)
    Base.metadata.create_all(bind=engine)

    # Add is_admin column if it doesn't exist (for existing DBs)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
            conn.commit()
            print("  Added is_admin column to users table.")
        except Exception:
            pass  # Column already exists — fine

        # Add read_at column to contact_messages if missing
        try:
            conn.execute(text("ALTER TABLE contact_messages ADD COLUMN read_at TIMESTAMP"))
            conn.commit()
            print("  Added read_at column to contact_messages table.")
        except Exception:
            pass

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing:
            existing.is_admin = True
            existing.hashed_pw = hash_password(ADMIN_PASSWORD)
            existing.is_active = True
            db.commit()
            print(f"  Updated existing user → admin: {ADMIN_EMAIL}")
        else:
            admin = User(
                email=ADMIN_EMAIL,
                full_name=ADMIN_NAME,
                hashed_pw=hash_password(ADMIN_PASSWORD),
                is_active=True,
                is_admin=True,
                notify_emails=False,
            )
            db.add(admin)
            db.commit()
            print(f"  Created admin user: {ADMIN_EMAIL}")
        print("  Admin seeding complete.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
