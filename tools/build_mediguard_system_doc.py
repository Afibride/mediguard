from __future__ import annotations

import html
import zipfile
from pathlib import Path


OUT = Path("MediGuard_System_Documentation.docx")


def esc(text: object) -> str:
    return html.escape("" if text is None else str(text), quote=False)


def run(text: str, bold: bool = False, color: str | None = None, size: int | None = None) -> str:
    props = []
    if bold:
        props.append("<w:b/>")
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    if size:
        props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
    return f"<w:r>{rpr}<w:t xml:space=\"preserve\">{esc(text)}</w:t></w:r>"


def para(
    text: str = "",
    style: str | None = None,
    bold: bool = False,
    color: str | None = None,
    size: int | None = None,
    align: str | None = None,
    shade: str | None = None,
    spacing_after: int = 120,
) -> str:
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr.append(f'<w:spacing w:after="{spacing_after}" w:line="276" w:lineRule="auto"/>')
    if shade:
        ppr.append(f'<w:shd w:fill="{shade}"/>')
    ppr_xml = f"<w:pPr>{''.join(ppr)}</w:pPr>"
    return f"<w:p>{ppr_xml}{run(text, bold=bold, color=color, size=size)}</w:p>"


def bullet(items: list[str]) -> str:
    return "".join(para(f"{i}. {item}", style="ListParagraph", spacing_after=60) for i, item in enumerate(items, 1))


def code_block(text: str) -> str:
    lines = text.strip("\n").splitlines()
    body = []
    for line in lines:
        body.append(
            '<w:p><w:pPr><w:pStyle w:val="Code"/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/>'
            '<w:shd w:fill="F3F6F8"/></w:pPr>'
            f'{run(line, color="1F2937", size=18)}</w:p>'
        )
    return "".join(body)


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def table(rows: list[list[str]], widths: list[int] | None = None, header: bool = True) -> str:
    if not rows:
        return ""
    cols = len(rows[0])
    if widths is None:
        widths = [int(9000 / cols)] * cols
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [
        '<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/>'
        '<w:tblW w:w="0" w:type="auto"/>'
        '<w:tblLook w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
        '</w:tblPr>',
        f"<w:tblGrid>{grid}</w:tblGrid>",
    ]
    for r_i, row in enumerate(rows):
        out.append("<w:tr>")
        for c_i, cell in enumerate(row):
            fill = "D9EAF7" if header and r_i == 0 else ("F8FAFC" if r_i % 2 == 0 else "FFFFFF")
            out.append(
                f'<w:tc><w:tcPr><w:tcW w:w="{widths[c_i]}" w:type="dxa"/>'
                f'<w:shd w:fill="{fill}"/><w:tcMar><w:top w:w="90" w:type="dxa"/>'
                '<w:left w:w="120" w:type="dxa"/><w:bottom w:w="90" w:type="dxa"/>'
                '<w:right w:w="120" w:type="dxa"/></w:tcMar></w:tcPr>'
                + para(cell, bold=(header and r_i == 0), spacing_after=0)
                + "</w:tc>"
            )
        out.append("</w:tr>")
    out.append("</w:tbl>")
    out.append(para("", spacing_after=160))
    return "".join(out)


def h1(text: str) -> str:
    return para(text, style="Heading1", color="0F766E", bold=True, spacing_after=180)


def h2(text: str) -> str:
    return para(text, style="Heading2", color="075985", bold=True, spacing_after=140)


def h3(text: str) -> str:
    return para(text, style="Heading3", color="334155", bold=True, spacing_after=100)


def note(text: str) -> str:
    return para(text, bold=True, color="0F766E", shade="E6FFFA", spacing_after=180)


def build_body() -> str:
    body = []
    body.append(para("MediGuard", style="Title", color="0F766E", bold=True, size=52, align="center", spacing_after=120))
    body.append(para("System Documentation and Technical Design", style="Subtitle", color="334155", size=30, align="center", spacing_after=260))
    body.append(para("Frontend, Backend, Machine Learning, RAG, Data, Security, and Use Case Diagrams", align="center", size=24, spacing_after=500))
    body.append(table([
        ["Document Field", "Value"],
        ["System", "MediGuard Community Health Platform"],
        ["Target Area", "Bamenda / North West Region, Cameroon"],
        ["Prepared For", "Project documentation, implementation review, and thesis support"],
        ["Generated From", "Current local codebase in mediguard-frontend and mediguard-backend"],
        ["Date", "May 21, 2026"],
    ], [2600, 6200]))
    body.append(note("Clinical safety note: MediGuard provides educational guidance and pre-consultation support. It is not a diagnosis, prescription system, or replacement for qualified healthcare professionals."))
    body.append(page_break())

    body.append(h1("1. Executive Summary"))
    body.append(para(
        "MediGuard is a community health platform that helps users check symptoms, learn about diseases, chat with a health education assistant, find nearby health facilities, and monitor local disease trends. "
        "The system combines a React frontend, FastAPI backend, SQLite database, a symptom prediction model, Pinecone vector search, curated medical references, and optional OpenAI-powered generation/vision analysis."
    ))
    body.append(table([
        ["Capability", "How It Works"],
        ["Symptom checking", "Users select or describe symptoms. The backend normalizes misspellings, ranks likely diseases, logs the screening, and returns first-aid/safety guidance."],
        ["Chat AI", "The assistant handles greetings, platform help, disease questions, symptom follow-up, RAG reference answers, and nearest-hospital requests."],
        ["Disease library", "Frontend loads disease records from the backend disease database and uses local data only as an emergency fallback."],
        ["Trends dashboard", "Aggregates PredictionLog records into top diseases, weekly trends, heatmap data, outbreak alerts, and summaries."],
        ["Nearby facilities", "Uses browser geolocation and OpenStreetMap/Overpass to fetch nearby hospitals and clinics, with map and directions links."],
    ], [2300, 6500]))

    body.append(h1("2. System Scope and Objectives"))
    body.append(bullet([
        "Improve early symptom awareness for common and locally relevant diseases.",
        "Provide guided pre-consultation screening without presenting results as a confirmed diagnosis.",
        "Support disease education through curated medical references and database disease profiles.",
        "Help users locate nearby facilities from their live map location.",
        "Store user profiles, screening history, chat history, feedback, and trend data.",
        "Provide analytics and outbreak-style sensitization for community health monitoring.",
    ]))

    body.append(h1("3. Technology Stack"))
    body.append(table([
        ["Layer", "Technology / Implementation"],
        ["Frontend", "React, Vite, React Router, Framer Motion, Tailwind-style UI classes, lucide-react icons"],
        ["Backend", "FastAPI, Pydantic schemas, SQLAlchemy ORM, pydantic-settings"],
        ["Database", "SQLite by default via DATABASE_URL; migration scripts exist for PostgreSQL-style targets"],
        ["Authentication", "JWT bearer tokens, passlib/bcrypt password hashing, password reset tokens"],
        ["ML", "Simple Naive-Bayes-style symptom model stored as random_forest.pkl fallback artifact; decision_tree.pkl and naive_bayes.pkl comparison artifacts"],
        ["Vector Search", "Pinecone index mediguard-health-knowledge with curated medical-reference chunks"],
        ["Embeddings", "sentence-transformers when available; deterministic hash-based embedding fallback in app/rag/embeddings.py"],
        ["AI Generation", "Optional OpenAI chat/vision calls when OPENAI_API_KEY is configured; deterministic fallback when not configured"],
        ["Maps", "OpenStreetMap/Overpass for live facility search; Google Maps direction URLs for navigation links"],
    ], [2300, 6500]))

    body.append(page_break())
    body.append(h1("4. High-Level Architecture"))
    body.append(code_block("""
                 +-----------------------------+
                 |        User Browser         |
                 | React/Vite Web Application  |
                 +--------------+--------------+
                                |
                                | HTTPS/HTTP JSON API
                                v
                 +--------------+--------------+
                 |       FastAPI Backend       |
                 | Routers, Auth, ML, RAG      |
                 +---+----------+----------+---+
                     |          |          |
                     v          v          v
          +----------+--+   +---+------+  +------------------+
          | SQLite DB   |   | ML Model |  | Pinecone Vector  |
          | users/logs/ |   | symptom  |  | curated medical  |
          | diseases    |   | ranking  |  | reference chunks |
          +-------------+   +----------+  +------------------+
                     |                      |
                     v                      v
          +-------------------+    +-------------------------+
          | Analytics/History |    | Optional OpenAI Answer  |
          | Profile/Feedback  |    | generation and vision   |
          +-------------------+    +-------------------------+
    """))
    body.append(para("The frontend never accesses the database directly. It calls backend API endpoints in src/services/api.js. The backend is responsible for authentication, prediction, RAG retrieval, persistence, and analytics."))

    body.append(h1("5. Frontend Structure"))
    body.append(table([
        ["Page / Component", "Purpose"],
        ["HomePage", "Landing dashboard, featured diseases, alerts, trends summaries, nearby facility preview."],
        ["SymptomChecker", "Game-like symptom selection, free-text symptom normalization, image analysis, prediction request, pregnancy/fatigue context."],
        ["PredictionResults", "Displays ranked possible diseases, matched symptoms, notes, safety guidance, nearby facilities."],
        ["ChatAI", "Conversational health education, symptom follow-up, nearest-hospital request, chat history save, feedback."],
        ["DiseaseLibrary", "Loads diseases from backend /diseases and filters by search, category, severity, and common-in-Bamenda."],
        ["DiseaseDetail", "Loads backend disease details, symptoms, causes, treatment overview, prevention, related diseases."],
        ["TrendsDashboard", "Loads analytics endpoints and renders trends, top diseases, heatmap, alerts, prevention cards."],
        ["NearbyFacilitiesPage", "Requests geolocation, fetches OpenStreetMap facilities, shows one main map and selectable facility list."],
        ["ProfilePage / HistoryPage", "Authenticated profile management, screening history, chat history, notification preferences."],
    ], [2700, 6100]))

    body.append(h1("6. Backend Structure"))
    body.append(table([
        ["Module", "Responsibility"],
        ["app/main.py", "Creates FastAPI app, initializes DB, configures CORS, registers routers."],
        ["app/config.py", "Reads environment settings such as DATABASE_URL, PINECONE_API_KEY, OPENAI_API_KEY, FRONTEND_ORIGINS."],
        ["app/routers/auth.py", "Register, login, current user, profile update, password reset, notification preferences."],
        ["app/routers/predict.py", "Symptoms list, symptom normalization, prediction, follow-up clarification, prediction feedback."],
        ["app/routers/chat.py", "Chat endpoint and image analysis endpoint."],
        ["app/routers/diseases.py", "Disease list and detail records from database."],
        ["app/routers/history.py", "Authenticated prediction history, chat history, feedback."],
        ["app/routers/analytics.py", "Top diseases, weekly trends, heatmap, summaries, outbreak alerts, chat insights."],
        ["app/ml", "Prediction model loading, symptom preprocessing/fuzzy matching, simple model training."],
        ["app/rag", "Reference dataset building, Pinecone ingestion, retrieval, chat response orchestration."],
        ["app/db", "SQLAlchemy models, session, and database initialization/seeding."],
    ], [2700, 6100]))

    body.append(page_break())
    body.append(h1("7. Database Design"))
    body.append(table([
        ["Table", "Key Fields", "Purpose"],
        ["users", "id, email, full_name, hashed_pw, notify_emails, created_at", "Stores registered users and notification preferences."],
        ["password_reset_tokens", "user_id, token, expires_at, used_at", "Supports forgot/reset password flow."],
        ["diseases", "slug, name, category, severity, symptoms, description, causes, treatment, prevention, sections", "System disease library and enrichment source."],
        ["prediction_logs", "user_id, symptoms, predictions, top_disease, timestamp, region", "Stores screening results for history and analytics."],
        ["chat_logs", "user_id, title, message, response, sources, follow_up_questions, mode, pregnancy_context", "Stores authenticated chat history."],
        ["contact_messages", "name, email, subject, message, sent_at", "Stores contact form submissions."],
        ["chat_feedback", "session_id, user_id, query, response_preview, rating, query_keywords, mode", "Tracks helpful/unhelpful chat responses and weak topics."],
        ["prediction_feedback", "prediction_log_id, user_id, top_predicted, was_helpful, confirmed_disease, comment", "Captures user feedback after clinical confirmation."],
    ], [2100, 3400, 3300]))
    body.append(h2("ER Diagram"))
    body.append(code_block("""
User 1 ──────── * PredictionLog
User 1 ──────── * ChatLog
User 1 ──────── * PasswordResetToken
User 1 ──────── * ChatFeedback
User 1 ──────── * PredictionFeedback

Disease is a reference table used by:
  - Disease Library
  - Prediction enrichment
  - RAG disease profile responses
  - Analytics disease count

PredictionLog drives:
  - User history
  - Trends dashboard
  - Top diseases
  - Heatmap
  - Outbreak alerts
    """))

    body.append(h1("8. Dataset and Knowledge Base"))
    body.append(table([
        ["Dataset Asset", "Current Size / Role"],
        ["data/raw/mediguard_dataset_full.csv", "5,130 records, 55 diseases, 128 symptom features."],
        ["data/processed/mediguard_train.csv", "4,104 training rows."],
        ["data/processed/mediguard_test.csv", "1,026 testing rows."],
        ["data_pipeline/symptoms_list.json", "128 ordered symptom features used by the predictor and frontend."],
        ["data_pipeline/mediguard_reference_chunks.json", "169 curated reference chunks across 54 diseases."],
        ["data_pipeline/essentials_disease_chunks.json", "47 extracted disease-reference chunks from Essentials of Human Diseases and Conditions."],
        ["Pinecone index", "169 current vectors after refresh; contains disease_reference and lab_reference chunks."],
    ], [3400, 5400]))
    body.append(para("The reference dataset was built from curated medical PDFs, including Essentials of Human Diseases and Conditions and Monica Cheesbrough's District Laboratory Practice in Tropical Countries Parts 1 and 2. The extraction pipeline keeps concise disease/laboratory snippets rather than whole pages."))

    body.append(h1("9. Machine Learning Model Design"))
    body.append(h2("Models Used"))
    body.append(table([
        ["Model / Engine", "Use in System"],
        ["models/random_forest.pkl", "Primary configured model_path. In the current code this artifact is loaded as a SimpleSymptomModel variant named random_forest_fallback."],
        ["models/decision_tree.pkl", "Comparison artifact for reporting/thesis comparison; trained with the same SimpleSymptomModel mechanism."],
        ["models/naive_bayes.pkl", "Comparison artifact; also SimpleSymptomModel style."],
        ["models/label_encoder.pkl", "SimpleLabelEncoder containing disease class names."],
        ["Pinecone disease_profile semantic prediction", "Optional first choice if Pinecone and sentence-transformers are available and disease_profile vectors exist."],
        ["Rule-based overlap fallback", "Always-available deterministic fallback using symptom overlap and disease symptom coverage."],
    ], [3100, 5700]))
    body.append(h2("Prediction Decision Order"))
    body.append(code_block("""
User symptoms
  -> normalize misspellings and aliases
  -> if Pinecone + sentence-transformers + disease_profile vectors are available:
         use semantic Pinecone prediction
     else:
         use local trained SimpleSymptomModel from models/random_forest.pkl
     else:
         try Pinecone hash-vector fallback
     else:
         use deterministic rule-based symptom overlap scoring
  -> enrich predictions from diseases table
  -> save PredictionLog
  -> return ranked predictions, notes, and disclaimer
    """))
    body.append(note("Important implementation detail: despite the filenames random_forest.pkl, decision_tree.pkl, and naive_bayes.pkl, the current train.py builds SimpleSymptomModel fallback variants rather than scikit-learn RandomForestClassifier/DecisionTreeClassifier/GaussianNB estimators. The documentation should describe the actual implementation to avoid overstating the model type."))

    body.append(page_break())
    body.append(h1("10. RAG and Chat AI Design"))
    body.append(para("The chat assistant is orchestrated mainly in app/rag/retriever.py. It handles deterministic intents first, then uses vector retrieval and optional LLM generation when appropriate."))
    body.append(table([
        ["Chat Capability", "Implementation"],
        ["Greetings/help/thanks", "Pattern-based responses so simple conversational messages do not trigger medical retrieval."],
        ["Disease definitions", "Alias and fuzzy disease matching; pulls Pinecone disease profile if available, else database disease profile."],
        ["Symptoms of a disease", "Uses disease table and symptom descriptions, with numbered lists."],
        ["Symptom checking in chat", "Extracts reported symptoms, asks one follow-up question at a time, records pregnancy/fatigue context, then returns prediction results."],
        ["RAG answers", "Retrieves curated reference chunks from Pinecone or local mediguard_reference_chunks.json; optional OpenAI produces the answer from context."],
        ["Nearest hospital", "If no location, asks user to allow browser location. If location exists, fetches nearest map facilities from OpenStreetMap/Overpass."],
        ["Platform help", "Answers how to use history, profile, trends, disease library, symptom checker, and facilities pages."],
    ], [2700, 6100]))
    body.append(h2("RAG Flow Diagram"))
    body.append(code_block("""
User question
  -> intent routing
       |-- greeting/help/thanks -> direct answer
       |-- disease definition   -> disease profile from Pinecone/DB
       |-- symptom check        -> follow-up question loop -> predictor
       |-- nearest facility     -> geolocation + OpenStreetMap
       |-- general health query -> retrieve reference chunks
  -> Pinecone query using embed_text/sentence-transformers
  -> if Pinecone unavailable: local mediguard_reference_chunks.json keyword fallback
  -> optional OpenAI generation from retrieved context
  -> answer + sources + disclaimer
    """))

    body.append(h1("11. Use Case Model"))
    body.append(h2("Actors"))
    body.append(table([
        ["Actor", "Description"],
        ["Guest User", "Can browse public pages, use symptom checker, chat, disease library, trends, and nearby facilities."],
        ["Registered User", "Can log in, save/view history, manage profile, notification preferences, and authenticated records."],
        ["Healthcare/Community Stakeholder", "Uses trends dashboard and outbreak sensitization data."],
        ["System/Admin Maintainer", "Maintains datasets, trains models, refreshes Pinecone, configures environment and email."],
        ["External Services", "Pinecone, OpenAI, OpenStreetMap/Overpass, SMTP email provider."],
    ], [2600, 6200]))
    body.append(h2("Use Case Diagram"))
    body.append(code_block("""
                  +----------------------------------+
                  |           MediGuard              |
                  |----------------------------------|
Guest User ------>| Check symptoms                   |
Guest User ------>| Chat with MediGuard AI           |
Guest User ------>| Browse disease library           |
Guest User ------>| View trends and health tips      |
Guest User ------>| Find nearby facilities           |
                  |                                  |
Registered User ->| Register / login                 |
Registered User ->| View profile                     |
Registered User ->| Save and view screening history  |
Registered User ->| Save and view chat history       |
Registered User ->| Submit prediction/chat feedback  |
                  |                                  |
Stakeholder ----->| Monitor disease trends           |
Stakeholder ----->| Review outbreak alerts           |
                  |                                  |
Maintainer -----> | Train model / refresh Pinecone   |
Maintainer -----> | Seed disease database            |
                  +----------------------------------+

External Services:
  Pinecone -> Vector retrieval
  OpenAI -> Optional answer/image analysis
  OpenStreetMap -> Facility discovery
  SMTP -> Email notifications
    """))
    body.append(h2("Core Use Case Table"))
    body.append(table([
        ["Use Case", "Primary Actor", "Precondition", "Main Outcome"],
        ["Register/Login", "Guest/User", "Valid email and password", "JWT token and user session created."],
        ["Run symptom check", "Guest/User", "At least one symptom", "Ranked disease possibilities and safety guidance returned; PredictionLog saved."],
        ["Chat symptom triage", "Guest/User", "User describes symptoms", "Assistant asks one question at a time, then returns possible matches."],
        ["Ask disease question", "Guest/User", "Disease or symptom query", "Assistant responds from database/RAG references."],
        ["Find nearest hospital", "Guest/User", "Browser location permitted", "Nearest mapped facilities sorted by distance."],
        ["View history", "Registered User", "Authenticated", "Screening and chat records loaded."],
        ["View trends", "Any user", "Prediction logs or fallback sample data", "Charts, top diseases, heatmap, alerts displayed."],
    ], [2100, 2100, 2400, 2700]))

    body.append(page_break())
    body.append(h1("12. Workflow and Sequence Diagrams"))
    body.append(h2("Symptom Checker Sequence"))
    body.append(code_block("""
User -> Frontend: Selects/describes symptoms
Frontend -> Backend /normalize-symptoms: Free-text symptoms
Backend -> Frontend: Canonical symptoms
Frontend -> Backend /predict: Symptoms + pregnancy/fatigue context
Backend -> ML Predictor: Rank diseases
Backend -> Database: Enrich disease details + save PredictionLog
Backend -> Frontend: Predictions, notes, disclaimer
Frontend -> User: Results, first aid guidance, nearby facilities
    """))
    body.append(h2("Chat Symptom Follow-Up Sequence"))
    body.append(code_block("""
User -> ChatAI: "I have fever and chills"
ChatAI -> /chat: Query + recent history
Backend -> Retriever: Extract symptoms
Retriever -> ChatAI: Ask first follow-up question
User -> ChatAI: Answers duration/severity/etc.
ChatAI -> /chat: Answer + history
Retriever -> Predictor: After required questions, run model
Retriever -> ChatAI: Possible matches + first aid + disclaimer
    """))
    body.append(h2("Nearest Facility Sequence"))
    body.append(code_block("""
User -> ChatAI: "I want the nearest hospital"
ChatAI -> Browser: Request geolocation
Browser -> ChatAI: latitude/longitude
ChatAI -> /chat: query + user_lat + user_lng
Backend -> OpenStreetMap/Overpass: Nearby hospitals/clinics around user
Backend -> ChatAI: nearest mapped facilities + directions
ChatAI -> User: sorted list and /nearby-facilities link
    """))

    body.append(h1("13. API Summary"))
    body.append(table([
        ["Endpoint", "Method", "Purpose"],
        ["/auth/register", "POST", "Create account and return JWT."],
        ["/auth/login", "POST", "Authenticate user and return JWT."],
        ["/auth/me", "GET/PATCH", "Read or update profile."],
        ["/auth/forgot-password", "POST", "Generate reset token/send email."],
        ["/auth/reset-password", "POST", "Reset password with token."],
        ["/symptoms", "GET", "Return ordered symptom feature list."],
        ["/normalize-symptoms", "POST", "Normalize typo/informal symptom text."],
        ["/predict", "POST", "Run symptom prediction and save PredictionLog."],
        ["/predict/clarify", "POST", "Return discriminating follow-up questions."],
        ["/chat", "POST", "Chat AI, RAG, symptom follow-up, facility help."],
        ["/chat/analyze-image", "POST", "Optional OpenAI vision analysis for uploaded image."],
        ["/diseases", "GET", "List/filter backend disease records."],
        ["/diseases/{slug}", "GET", "Fetch disease detail."],
        ["/history", "GET/DELETE", "Authenticated prediction history."],
        ["/history/chats", "GET/POST", "Authenticated chat history."],
        ["/analytics/top-diseases", "GET", "Top disease counts."],
        ["/analytics/trends", "GET", "Weekly trend records."],
        ["/analytics/heatmap", "GET", "Region/disease aggregate counts."],
        ["/analytics/summary", "GET", "Dashboard summary metrics."],
        ["/contact", "POST", "Store contact form message."],
    ], [2500, 1200, 5100]))

    body.append(h1("14. Security and Privacy"))
    body.append(bullet([
        "Passwords are hashed using passlib/bcrypt before storage.",
        "JWT bearer tokens protect profile, history, password change, notifications, and alert sending endpoints.",
        "CORS origins are controlled through FRONTEND_ORIGINS in the backend environment.",
        "Forgot-password tokens expire after 30 minutes and are marked used after reset.",
        "The system stores medical screening history, so deployments should protect the database, .env, logs, and backups.",
        "API keys for Pinecone, OpenAI, SMTP, and database providers must never be committed or shared publicly.",
    ]))

    body.append(h1("15. Analytics and Trends Dashboard"))
    body.append(para("The analytics module uses PredictionLog records as its primary signal. If no screenings exist, some endpoints return sample data so the UI remains demonstrable during development."))
    body.append(table([
        ["Metric", "Source"],
        ["Top diseases", "Grouped count of PredictionLog.top_disease."],
        ["Weekly trends", "PredictionLog timestamps grouped by week and disease."],
        ["Heatmap", "PredictionLog grouped by region and top disease."],
        ["Summary", "Total predictions, active this week, top disease, diseases tracked, feedback accuracy."],
        ["Outbreak alerts", "Disease share thresholds, with rainy-season watch rules for malaria/cholera."],
        ["Chat insights", "ChatFeedback helpful/unhelpful ratings and weak keyword extraction."],
    ], [2600, 6200]))

    body.append(h1("16. Deployment and Environment"))
    body.append(table([
        ["Variable", "Purpose"],
        ["DATABASE_URL", "SQLite or database connection string. Default sqlite:///./mediguard.db."],
        ["SECRET_KEY", "JWT signing secret."],
        ["FRONTEND_ORIGINS", "Comma-separated allowed CORS origins."],
        ["FRONTEND_URL", "Used in reset password emails."],
        ["PINECONE_API_KEY / PINECONE_INDEX", "Vector database configuration."],
        ["OPENAI_API_KEY", "Optional chat/vision generation."],
        ["SMTP_*", "Optional welcome, reset, and outbreak alert email delivery."],
    ], [3000, 5800]))
    body.append(h2("Common Commands"))
    body.append(code_block("""
Backend:
  cd mediguard-backend
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  python app/ml/train.py
  python app/rag/build_medical_reference_dataset.py --clear-pinecone --upsert
  python -m pytest tests -q

Frontend:
  cd mediguard-frontend
  npm install
  npm run dev -- --host 0.0.0.0 --port 3000
  npm run lint
  npm run build
    """))

    body.append(h1("17. Testing and Quality Status"))
    body.append(table([
        ["Area", "Current Checks"],
        ["Chat AI", "tests/test_chat.py validates greetings, malaria prevention, spelling correction, facility routing, follow-up questions, pregnancy triage."],
        ["Auth", "tests/test_auth.py covers register, login, current user, reset password, chat history persistence."],
        ["Prediction", "tests/test_predict.py covers symptom list and ranked predictions; current codebase previously showed a symptom count expectation drift when dataset expanded."],
        ["Frontend", "npm run lint and npm run build are used after UI changes."],
        ["Manual QA", "Phone testing through local network URLs; geolocation may require HTTPS or localhost depending on browser policy."],
    ], [2300, 6500]))

    body.append(h1("18. Limitations and Future Improvements"))
    body.append(bullet([
        "Replace SimpleSymptomModel fallback artifacts with actual scikit-learn RandomForest, DecisionTree, and Naive Bayes estimators if thesis wording requires those exact model types.",
        "Add HTTPS deployment for reliable phone geolocation on LAN and production.",
        "Add admin interface for disease database edits, model retraining, Pinecone refresh, and feedback review.",
        "Separate clinical laboratory knowledge, disease education, and training vectors into explicit Pinecone namespaces.",
        "Improve medical safety layer with stronger red-flag triage and local emergency contact configuration.",
        "Add automated end-to-end frontend tests for symptom checker, chat, disease library, and nearby facilities.",
        "Add migration-managed production database schema through Alembic for PostgreSQL/Neon/Supabase style deployments.",
    ]))

    body.append(h1("19. Conclusion"))
    body.append(para(
        "MediGuard is a full-stack health education and pre-consultation platform. Its core value is the combination of symptom prediction, guided chat follow-up, curated medical-reference retrieval, disease education, local trend monitoring, and map-based facility discovery. "
        "The system is designed to support early awareness and safer care-seeking while clearly stating that automated results can be incomplete or faulty and must not replace professional medical care."
    ))

    return "".join(body)


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="22"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:qFormat/><w:pPr><w:jc w:val="center"/></w:pPr><w:rPr><w:rFonts w:ascii="Aptos Display" w:hAnsi="Aptos Display"/><w:b/><w:sz w:val="52"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:qFormat/><w:pPr><w:jc w:val="center"/></w:pPr><w:rPr><w:rFonts w:ascii="Aptos" w:hAnsi="Aptos"/><w:sz w:val="30"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="140"/></w:pPr><w:rPr><w:rFonts w:ascii="Aptos Display" w:hAnsi="Aptos Display"/><w:b/><w:sz w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="160" w:after="100"/></w:pPr><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="80"/></w:pPr><w:rPr><w:b/><w:sz w:val="23"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="360" w:hanging="0"/></w:pPr></w:style>
  <w:style w:type="paragraph" w:styleId="Code"><w:name w:val="Code"/><w:basedOn w:val="Normal"/><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/><w:sz w:val="18"/></w:rPr></w:style>
  <w:style w:type="table" w:styleId="TableGrid"><w:name w:val="Table Grid"/><w:tblPr><w:tblBorders><w:top w:val="single" w:sz="4" w:color="CBD5E1"/><w:left w:val="single" w:sz="4" w:color="CBD5E1"/><w:bottom w:val="single" w:sz="4" w:color="CBD5E1"/><w:right w:val="single" w:sz="4" w:color="CBD5E1"/><w:insideH w:val="single" w:sz="4" w:color="CBD5E1"/><w:insideV w:val="single" w:sz="4" w:color="CBD5E1"/></w:tblBorders></w:tblPr></w:style>
</w:styles>"""


def document_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {build_body()}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="900" w:right="900" w:bottom="900" w:left="900" w:header="450" w:footer="450" w:gutter="0"/>
      <w:cols w:space="720"/>
      <w:docGrid w:linePitch="360"/>
    </w:sectPr>
  </w:body>
</w:document>"""


def write_docx() -> None:
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/_rels/document.xml.rels", doc_rels)
        zf.writestr("word/styles.xml", styles_xml())
        zf.writestr("word/document.xml", document_xml())


if __name__ == "__main__":
    write_docx()
    print(OUT.resolve())
