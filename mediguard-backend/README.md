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

Do not commit `.env`. Rotate any API key that has been shared publicly or in chat.

