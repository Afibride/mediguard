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

## Model Artifacts

GitHub stores the backend code only. The generated `.pkl` model files are ignored because `random_forest.pkl` is larger than GitHub's normal file limit.

For deployment, upload these local files to cloud storage with direct download links:

```text
models/random_forest.pkl
models/decision_tree.pkl
models/naive_bayes.pkl
models/label_encoder.pkl
models/symptoms_list.json
```

Then set these environment variables on the deployed backend:

```env
MODEL_DOWNLOAD_ENABLED=true
MODEL_RANDOM_FOREST_URL=https://your-storage.example/random_forest.pkl
MODEL_DECISION_TREE_URL=https://your-storage.example/decision_tree.pkl
MODEL_NAIVE_BAYES_URL=https://your-storage.example/naive_bayes.pkl
MODEL_LABEL_ENCODER_URL=https://your-storage.example/label_encoder.pkl
MODEL_SYMPTOMS_LIST_URL=https://your-storage.example/symptoms_list.json
MODEL_DOWNLOAD_TOKEN=
MODEL_DOWNLOAD_TIMEOUT_SECONDS=180
```

On startup, MediGuard checks whether each model file exists in `models/`. Missing files are downloaded before prediction endpoints are used. Existing local files are not downloaded again. For private Hugging Face repos, set `MODEL_DOWNLOAD_TOKEN` to a Hugging Face token with read access.

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
