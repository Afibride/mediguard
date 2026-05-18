# MediGuard Backend

FastAPI backend for MediGuard. It implements auth, symptom prediction, RAG chat, disease library, history, analytics, and contact endpoints.

## Setup

```powershell
cd mediguard-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for Swagger.

## Supabase Database

The backend uses SQLAlchemy, so Supabase should be connected through the Supabase Postgres connection string.

1. In Supabase, open **Project Settings > Database > Connection string**.
2. Copy the URI connection string and include your database password.
3. Set it in `.env` as `SUPABASE_DB_URL`.

Example:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-publishable-key
SUPABASE_DB_URL=postgresql://postgres.your-project:YOUR_PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres?sslmode=require
```

When `SUPABASE_DB_URL` is set, MediGuard uses Supabase Postgres instead of the local SQLite `DATABASE_URL`.

Do not commit `.env`. Rotate any API key that has been shared publicly or in chat.
