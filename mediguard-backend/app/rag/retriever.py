"""
MediGuard RAG pipeline.

Uses Pinecone + OpenAI when configured, and falls back to local encyclopedia
chunks so the backend remains usable before the one-time Pinecone ingest runs.
"""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

from app.data import DISEASES, SYMPTOMS
from app.db.models import Disease
from app.db.session import SessionLocal
from app.ml.predictor import DiseasePredictor
from app.rag.embeddings import embed_text

load_dotenv()

DISCLAIMER = (
    "This information is from the Gale Encyclopedia of Medicine and is provided "
    "for educational purposes only. It is not a substitute for professional "
    "medical advice, diagnosis, or treatment. MediGuard's automated results can "
    "sometimes be incomplete or faulty, so always consult a qualified healthcare "
    "professional for any health concerns."
)

PREGNANCY_WARNING_SIGNS = [
    "vaginal bleeding",
    "severe abdominal pain",
    "severe headache",
    "vision changes",
    "blurred vision",
    "swelling",
    "face swelling",
    "reduced fetal movement",
    "fainting",
    "chest pain",
    "shortness of breath",
    "fever",
]

PREGNANCY_TERMS = [
    "pregnant",
    "pregnancy",
    "expecting",
    "antenatal",
    "prenatal",
    "trimester",
]

FATIGUE_CONTEXT_TERMS = [
    "fatigue",
    "tired",
    "tiredness",
    "weak",
    "weakness",
    "poor sleep",
    "lack of sleep",
    "stress",
    "overworked",
    "overwork",
    "exhausted",
    "dehydrated",
    "heavy work",
]

CHUNKS_FILE = Path(__file__).resolve().parents[2] / "data_pipeline" / "mediguard_rag_chunks.json"

_pinecone_index = None
_pinecone_dimension = None
_embedding_model = None
_openai_client = None
_local_chunks = None
_predictor = None

GREETING_PATTERNS = [
    r"^\s*(hi|hello|hey|good morning|good afternoon|good evening)\s*[!.?]*\s*$",
    r"^\s*how are you\s*[?.!]*\s*$",
    r"^\s*(can|could)\s+you\s+help\s+me\s*[?.!]*\s*$",
    r"^\s*(help|what can you do)\s*[?.!]*\s*$",
]

THANKS_PATTERNS = [
    r"^\s*(thanks|thank you|thank u|appreciate it|much appreciated)\s*[!.?]*\s*$",
    r"^\s*(thanks|thank you)\s+(a lot|so much|very much)\s*[!.?]*\s*$",
]


def _conversational_response(query: str) -> dict | None:
    text = query.strip().lower()
    if not text:
        return {
            "answer": "I am here. Ask me about symptoms, diseases, prevention, or when to seek care.",
            "sources": [],
            "disclaimer": DISCLAIMER,
        }
    if any(re.match(pattern, text) for pattern in GREETING_PATTERNS):
        if "how are you" in text:
            answer = (
                "I am doing well and ready to help. I can explain symptoms, prevention, and general health information "
                "from MediGuard's encyclopedia knowledge base. Tell me what you would like to understand."
            )
        elif "help" in text or "what can you do" in text:
            answer = (
                "Yes, I can help. You can ask about symptoms, common conditions in Bamenda, prevention, treatment overview, "
                "or when to see a doctor. I can also explain your symptom-checker result in plain language."
            )
        else:
            answer = (
                "Hello, welcome to MediGuard. I can help with health education questions about symptoms, diseases, "
                "prevention, and when to seek professional care."
            )
        return {"answer": answer, "sources": [], "disclaimer": DISCLAIMER}
    if any(re.match(pattern, text) for pattern in THANKS_PATTERNS):
        return {
            "answer": (
                "You are welcome. I am here whenever you want to check symptoms, understand a condition, "
                "or learn prevention steps from the MediGuard knowledge base."
            ),
            "sources": [],
            "disclaimer": DISCLAIMER,
        }
    return None


def _mentions_pregnancy(query: str) -> bool:
    text = query.lower()
    return any(term in text for term in PREGNANCY_TERMS)


def _mentions_fatigue_context(query: str, symptoms: list[str] | None = None) -> bool:
    text = f"{query.lower()} {' '.join(symptom.lower() for symptom in symptoms or [])}"
    return any(term in text for term in FATIGUE_CONTEXT_TERMS)


def _pregnancy_warning_matches(query: str, symptoms: list[str]) -> list[str]:
    text = f"{query.lower()} {' '.join(symptom.lower() for symptom in symptoms)}"
    return [sign for sign in PREGNANCY_WARNING_SIGNS if sign in text]


def _pregnancy_followup_response(query: str, symptoms: list[str], is_pregnant: bool, pregnancy_weeks: int | None) -> dict | None:
    pregnancy_context = is_pregnant or _mentions_pregnancy(query)
    if not pregnancy_context:
        return None

    warning_matches = _pregnancy_warning_matches(query, symptoms)
    if warning_matches:
        return {
            "answer": (
                "Because pregnancy is involved and you mentioned "
                f"{', '.join(warning_matches)}, please seek urgent care from a maternity unit, clinic, or qualified healthcare professional now. "
                "These can be warning signs in pregnancy. If you can, tell me how many weeks pregnant you are, when the symptom started, "
                "whether it is worsening, and whether there is fever, bleeding, severe pain, vision change, or reduced fetal movement."
            ),
            "sources": [],
            "disclaimer": DISCLAIMER,
            "mode": "pregnancy_triage",
            "pregnancy_context": True,
            "follow_up_questions": [
                "How many weeks pregnant are you?",
                "When did the symptom start, and is it getting worse?",
                "Is there bleeding, severe pain, fever, vision change, or reduced fetal movement?",
            ],
        }

    if len(symptoms) < 2:
        weeks_text = f" I noted you are around {pregnancy_weeks} weeks pregnant." if pregnancy_weeks else ""
        return {
            "answer": (
                f"I can help, but pregnancy symptoms need a little more detail before I give a useful response.{weeks_text} "
                "Please tell me: how many weeks pregnant you are, your main symptom, when it started, how severe it is, "
                "and whether you have bleeding, abdominal pain, fever, headache, vision changes, swelling, dizziness, "
                "shortness of breath, or reduced fetal movement."
            ),
            "sources": [],
            "disclaimer": DISCLAIMER,
            "mode": "pregnancy_follow_up",
            "pregnancy_context": True,
            "follow_up_questions": [
                "How many weeks pregnant are you?",
                "What exact symptoms are you feeling?",
                "Any bleeding, severe pain, fever, vision changes, swelling, or reduced fetal movement?",
            ],
        }
    return None


def _detect_disease(query: str) -> dict | None:
    text = query.lower()
    candidates = sorted(DISEASES, key=lambda item: len(item["name"]), reverse=True)
    for disease in candidates:
        names = {disease["name"].lower(), disease["slug"].replace("-", " ").lower()}
        if any(name and name in text for name in names):
            return disease
    return None


def _is_symptom_question(query: str) -> bool:
    text = query.lower()
    return any(term in text for term in ["symptom", "sign", "feel like", "present with"])


def _symptom_answer(query: str, chunks: list[dict], disease: dict | None) -> dict | None:
    if not disease or not _is_symptom_question(query):
        return None
    symptoms = disease.get("symptoms") or []
    if not symptoms:
        return None
    sources = []
    seen = set()
    for chunk in chunks:
        name = chunk["disease"]
        if name not in seen:
            seen.add(name)
            sources.append(name)
    return {
        "answer": (
            f"Common symptoms linked with {disease['name']} include {', '.join(symptoms)}. "
            "Symptoms can vary from person to person, and this is not a diagnosis. "
            "What you can do now: rest, drink fluids, monitor the symptoms, avoid taking prescription medicines without a clinician, "
            "and seek care quickly if symptoms are severe, persistent, or worsening. MediGuard results can sometimes be faulty, "
            "so use this as guidance only."
        ),
        "sources": sources or [disease["name"]],
        "disclaimer": DISCLAIMER,
    }


def _get_predictor() -> DiseasePredictor:
    global _predictor
    if _predictor is None:
        _predictor = DiseasePredictor()
    return _predictor


def _enrich_predictions_from_database(predictions: list[dict]) -> list[dict]:
    db = SessionLocal()
    try:
        rows = db.query(Disease).all()
        by_name = {row.name.lower(): row for row in rows}
        by_slug = {row.slug.lower(): row for row in rows}
        enriched = []
        for item in predictions:
            key = (item.get("disease") or item.get("name") or "").lower()
            slug = (item.get("slug") or "").lower()
            disease = by_name.get(key) or by_slug.get(slug)
            if disease:
                item = {
                    **item,
                    "id": disease.slug,
                    "slug": disease.slug,
                    "name": disease.name,
                    "disease": disease.name,
                    "category": disease.category,
                    "severity": disease.severity,
                    "description": disease.description,
                    "symptoms": disease.symptoms or item.get("symptoms", []),
                    "database_source": "diseases",
                }
            enriched.append(item)
        return enriched
    finally:
        db.close()


def _extract_reported_symptoms(query: str) -> list[str]:
    text = f" {query.lower()} "
    # Normalize common connectors and punctuation so phrases such as
    # "fever and chills", "fever,chills", or "cough plus chest pain" match
    # the ordered symptom vocabulary consistently.
    text = re.sub(r"[,+/&]", " and ", text)
    text = re.sub(r"\b(with|plus|also|alongside|together with)\b", " and ", text)
    matches = []
    for symptom in sorted(SYMPTOMS, key=len, reverse=True):
        normalized = symptom.lower().replace("_", " ")
        pattern = rf"(?<![a-z]){re.escape(normalized)}(?![a-z])"
        if re.search(pattern, text) and symptom not in matches:
            matches.append(symptom)
    return matches


def _is_symptom_check_request(query: str, symptoms: list[str]) -> bool:
    text = query.lower()
    general_question_starts = (
        "what is",
        "what are",
        "what does",
        "define",
        "explain",
        "tell me about",
        "meaning of",
    )
    if text.strip().startswith(general_question_starts):
        return False
    intent_terms = [
        "i have",
        "i am having",
        "i'm having",
        "my symptoms",
        "check my symptoms",
        "what could this be",
        "what might this be",
        "predict",
        "diagnose",
        "assessment",
        "symptom checker",
    ]
    return len(symptoms) >= 2 or (bool(symptoms) and any(term in text for term in intent_terms))


def _is_new_general_question(query: str) -> bool:
    text = query.lower().strip()
    general_question_starts = (
        "what is",
        "what are",
        "what does",
        "define",
        "explain",
        "tell me about",
        "meaning of",
    )
    symptom_check_terms = ("what could this be", "what might this be", "check my symptoms", "predict", "diagnose")
    return text.startswith(general_question_starts) and not any(term in text for term in symptom_check_terms)


def _symptom_follow_up_questions(symptoms: list[str], is_pregnant: bool = False) -> list[str]:
    questions = [
        "How long have you had these symptoms?",
        "Are they mild, moderate, or severe?",
        "Do you have any other symptoms, such as fever, vomiting, diarrhea, chest pain, rash, dizziness, or trouble breathing?",
    ]
    symptom_set = {symptom.lower() for symptom in symptoms}
    if any(term in symptom_set for term in ["fever", "high fever", "prolonged fever", "sudden high fever"]):
        questions.append("What is your temperature, and does the fever come with chills or sweating?")
    if any(term in symptom_set for term in ["cough", "chronic cough", "shortness of breath", "chest pain"]):
        questions.append("Is there chest pain, wheezing, fast breathing, or coughing up blood?")
    if any(term in symptom_set for term in ["diarrhea", "vomiting", "abdominal pain", "nausea"]):
        questions.append("Are you able to drink fluids, and is there blood in stool or signs of dehydration?")
    if any(term in symptom_set for term in ["fatigue", "weakness", "body weakness", "dizziness", "headache"]):
        questions.append("Have you recently had poor sleep, heavy work, stress, missed meals, dehydration, or unusual exertion?")
    if is_pregnant:
        questions.append("How many weeks pregnant are you, and is there bleeding, severe pain, vision change, swelling, or reduced fetal movement?")
    return questions[:5]


def _first_aid_guidance(symptoms: list[str], is_pregnant: bool = False) -> list[str]:
    symptom_text = " ".join(symptom.lower() for symptom in symptoms)
    guidance = [
        "Rest and avoid strenuous activity while you monitor the symptoms.",
        "Drink safe fluids; use oral rehydration solution if there is diarrhea, vomiting, or signs of dehydration.",
        "Check temperature when possible and keep notes on when symptoms started, severity, and anything that makes them better or worse.",
        "Do not start antibiotics, antimalarials, or strong pain medicines without advice from a qualified clinician.",
    ]
    if any(term in symptom_text for term in ["fever", "chills", "headache", "sweating"]):
        guidance.append("For fever, keep cool, hydrate, and arrange testing or clinical review if it persists or is high.")
    if any(term in symptom_text for term in ["diarrhea", "vomiting", "abdominal pain"]):
        guidance.append("For diarrhea or vomiting, prioritize rehydration and seek care urgently for blood in stool, severe weakness, or inability to keep fluids down.")
    if any(term in symptom_text for term in ["shortness of breath", "chest pain", "wheezing"]):
        guidance.append("Shortness of breath, chest pain, or severe wheezing needs urgent medical attention.")
    if any(term in symptom_text for term in ["fatigue", "weakness", "body weakness", "dizziness", "headache"]):
        guidance.append("If tiredness may be contributing, rest, rehydrate, eat a light meal if you missed food, and monitor whether symptoms improve.")
    if is_pregnant:
        guidance.append("Because pregnancy is involved, contact an antenatal clinic or maternity unit promptly, especially with bleeding, fever, severe pain, headache, swelling, vision changes, or reduced fetal movement.")
    return guidance[:6]


def _history_requested_followup(chat_history: list[dict] | None) -> bool:
    if not chat_history:
        return False
    assistant_messages = [
        (message.get("content") or "").lower()
        for message in chat_history[-4:]
        if message.get("role") == "assistant"
    ]
    return any("follow-up" in message or "need a little more information" in message for message in assistant_messages)


def _recent_user_symptom_context(query: str, chat_history: list[dict] | None) -> str:
    user_parts = [
        message.get("content", "")
        for message in (chat_history or [])[-4:]
        if message.get("role") == "user"
    ]
    user_parts.append(query)
    return " ".join(user_parts)


def _symptom_check_response(
    query: str,
    is_pregnant: bool = False,
    pregnancy_weeks: int | None = None,
    chat_history: list[dict] | None = None,
) -> dict | None:
    followup_already_asked = _history_requested_followup(chat_history)
    if followup_already_asked and _is_new_general_question(query):
        return None
    symptom_context = _recent_user_symptom_context(query, chat_history) if followup_already_asked else query
    reported_symptoms = _extract_reported_symptoms(symptom_context)
    pregnancy_followup = _pregnancy_followup_response(query, reported_symptoms, is_pregnant, pregnancy_weeks)
    if pregnancy_followup:
        return pregnancy_followup

    if not _is_symptom_check_request(query, reported_symptoms):
        return None

    pregnancy_context = bool(is_pregnant or _mentions_pregnancy(query))
    fatigue_context = _mentions_fatigue_context(symptom_context, reported_symptoms)
    follow_up_questions = _symptom_follow_up_questions(reported_symptoms, pregnancy_context)

    if not followup_already_asked:
        symptom_text = ", ".join(reported_symptoms) if reported_symptoms else "your symptom"
        return {
            "answer": (
                f"I found this in your message: {symptom_text}. "
                "Before I show possible matches, I need a little more information so the response is safer and more useful. "
                "Please answer the follow-up questions below."
            ),
            "sources": [],
            "disclaimer": DISCLAIMER,
            "symptoms": reported_symptoms,
            "predictions": [],
            "mode": "symptom_follow_up",
            "pregnancy_context": pregnancy_context,
            "fatigue_context": fatigue_context,
            "follow_up_questions": follow_up_questions,
            "data_source": "database",
        }

    predictions = _enrich_predictions_from_database(_get_predictor().predict(reported_symptoms))
    if fatigue_context:
        for prediction in predictions:
            prediction["fatigue_context"] = True
    if not predictions:
        return {
            "answer": (
                f"I found these symptoms in your message: {', '.join(reported_symptoms)}. "
                "I could not produce a confident match from the current model. Please answer a few follow-up questions or use the full symptom checker."
            ),
            "sources": [],
            "disclaimer": DISCLAIMER,
            "symptoms": reported_symptoms,
            "predictions": [],
            "mode": "symptom_check",
            "pregnancy_context": pregnancy_context,
            "fatigue_context": fatigue_context,
            "follow_up_questions": follow_up_questions,
            "data_source": "database",
        }

    lines = [
        f"I found these symptoms in your message: {', '.join(reported_symptoms)}.",
        "Here are the top possible matches from the MediGuard symptom model:",
    ]
    for index, prediction in enumerate(predictions[:5], start=1):
        lines.append(f"{index}. {prediction['disease']} - {prediction['probability']}% match")
    lines.append(
        "This is not a diagnosis. Automated results can sometimes be incomplete or faulty, so treat this as guidance only."
    )
    lines.append("First aid / what you can do now:")
    for item in _first_aid_guidance(reported_symptoms, pregnancy_context):
        lines.append(f"- {item}")
    lines.append("Seek urgent care if symptoms are severe, persistent, worsening, or involve breathing difficulty, chest pain, confusion, fainting, severe dehydration, bleeding, or pregnancy warning signs.")
    if is_pregnant or _mentions_pregnancy(query):
        lines.append(
            "Pregnancy context noted: please arrange prompt antenatal or clinical assessment, especially for fever, abdominal pain, bleeding, severe headache, vision changes, swelling, shortness of breath, or reduced fetal movement."
        )
    if fatigue_context:
        lines.append(
            "Fatigue context noted: poor sleep, dehydration, missed meals, stress, or heavy activity can worsen symptoms, but they do not rule out infection or another medical condition."
        )
    return {
        "answer": "\n".join(lines),
        "sources": [prediction["disease"] for prediction in predictions[:3]],
        "disclaimer": DISCLAIMER,
        "symptoms": reported_symptoms,
        "predictions": predictions,
        "mode": "symptom_check",
        "pregnancy_context": pregnancy_context,
        "fatigue_context": fatigue_context,
        "follow_up_questions": [],
        "data_source": "database",
    }


def _optional_imports():
    try:
        from openai import OpenAI
        from pinecone import Pinecone
    except ImportError:
        return None, None
    return OpenAI, Pinecone


def _load_local_chunks() -> list[dict]:
    global _local_chunks
    if _local_chunks is None:
        _local_chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    return _local_chunks


def _get_index():
    global _pinecone_index, _pinecone_dimension
    OpenAI, Pinecone = _optional_imports()
    if Pinecone is None or not os.environ.get("PINECONE_API_KEY"):
        return None
    if _pinecone_index is None:
        try:
            pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
            index_name = os.environ.get("PINECONE_INDEX", "mediguard-health-knowledge")
            description = pc.describe_index(index_name)
            _pinecone_dimension = getattr(description, "dimension", None)
            _pinecone_index = pc.Index(index_name)
        except Exception:
            return None
    return _pinecone_index


def _get_embedder():
    global _embedding_model
    return None


def _get_llm():
    global _openai_client
    OpenAI, Pinecone = _optional_imports()
    if OpenAI is None or not os.environ.get("OPENAI_API_KEY"):
        return None
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _openai_client


def _local_retrieve(query: str, top_k: int = 5, filter_disease: str | None = None) -> list[dict]:
    terms = {term.strip(".,?!:;()[]").lower() for term in query.split() if len(term) > 2}
    matches = []
    for chunk in _load_local_chunks():
        disease = chunk.get("disease", "")
        if filter_disease and disease.lower() != filter_disease.lower():
            continue
        text = chunk.get("text", "")
        haystack = f"{disease} {chunk.get('section', '')} {text}".lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            matches.append({
                "text": text,
                "disease": disease,
                "source": chunk.get("source", "Gale Encyclopedia of Medicine"),
                "score": score,
                "retrieval_source": "local_fallback",
            })
    return sorted(matches, key=lambda item: item["score"], reverse=True)[:top_k]


def retrieve(query: str, top_k: int = 5, filter_disease: str | None = None) -> list[dict]:
    index = _get_index()
    if index is None:
        return _local_retrieve(query, top_k=top_k, filter_disease=filter_disease)

    query_vector = embed_text(query, dim=_pinecone_dimension or 384)
    # Restrict to encyclopedia RAG chunks — exclude disease_profile and training_example
    # vectors that were added by the prediction pipeline.
    pinecone_filter: dict = {"data_type": {"$nin": ["disease_profile", "training_example"]}}
    if filter_disease:
        pinecone_filter["disease"] = {"$eq": filter_disease}

    try:
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=pinecone_filter,
        )
    except Exception:
        return _local_retrieve(query, top_k=top_k, filter_disease=filter_disease)

    matches = results.matches if hasattr(results, "matches") else results.get("matches", [])
    chunks = []
    for match in matches:
        meta = match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
        text = meta.get("text", "")
        if not text:
            continue  # skip non-encyclopedia vectors that slipped through the filter
        chunks.append({
            "text": text,
            "disease": meta.get("disease", ""),
            "source": meta.get("source", "Gale Encyclopedia of Medicine"),
            "score": round(match.score if hasattr(match, "score") else match.get("score", 0), 4),
            "retrieval_source": "pinecone",
        })

    # Fall back to local keyword search if Pinecone returned nothing useful
    if not chunks:
        return _local_retrieve(query, top_k=top_k, filter_disease=filter_disease)

    return chunks


def _extractive_answer(query: str, chunks: list[dict]) -> str:
    source_text = " ".join(chunk["text"] for chunk in chunks[:3])
    sentences = [part.strip() for part in source_text.replace("\n", " ").split(".") if part.strip()]
    summary = ". ".join(sentences[:5])
    if summary:
        summary += "."
    return (
        f"Based on the encyclopedia passages I found, {summary} "
        "For first aid, rest, drink safe fluids, monitor symptoms, and seek urgent care for severe, worsening, or persistent symptoms. "
        "MediGuard results can sometimes be faulty, so use this as educational guidance only and consult a qualified healthcare professional for personal symptoms."
    )


def generate_answer(
    query: str,
    filter_disease: str | None = None,
    chat_history: list[dict] | None = None,
    gender: str | None = None,
    is_pregnant: bool = False,
    pregnancy_weeks: int | None = None,
) -> dict:
    conversational = _conversational_response(query)
    if conversational:
        return conversational

    symptom_check = _symptom_check_response(
        query,
        is_pregnant=is_pregnant,
        pregnancy_weeks=pregnancy_weeks,
        chat_history=chat_history,
    )
    if symptom_check:
        return symptom_check

    detected_disease = _detect_disease(query)
    effective_filter = filter_disease or (detected_disease["name"] if detected_disease else None)
    chunks = retrieve(query, top_k=5, filter_disease=effective_filter)
    data_source = chunks[0].get("retrieval_source", "unknown") if chunks else "none"
    if not chunks:
        return {
            "answer": "I could not find relevant encyclopedia information for that question. Please try rephrasing or consult a healthcare professional.",
            "sources": [],
            "disclaimer": DISCLAIMER,
            "data_source": data_source,
        }

    symptom_response = _symptom_answer(query, chunks, detected_disease)
    if symptom_response:
        symptom_response["data_source"] = data_source
        return symptom_response

    context = "\n\n---\n\n".join(f"[Source: {c['disease']} - {c['source']}]\n{c['text']}" for c in chunks)
    llm = _get_llm()
    if llm is None:
        answer = _extractive_answer(query, chunks)
    else:
        messages = [{
            "role": "system",
            "content": (
                "You are MediGuard's health assistant for Bamenda, Cameroon. "
                "Answer clearly using only the context below. Never diagnose or prescribe medication. "
                "When relevant, include simple first aid or self-care steps such as rest, fluids, monitoring symptoms, and urgent-care red flags. "
                "Tell users that automated results can sometimes be incomplete or faulty. Always recommend professional care for personal symptoms. If the user is pregnant or asks about pregnancy, "
                "ask concise follow-up questions about gestational age, severity, onset, bleeding, abdominal pain, fever, "
                "headache, vision changes, swelling, shortness of breath, and fetal movement before giving non-urgent guidance.\n\n"
                f"User context: gender={gender or 'not provided'}, pregnant={is_pregnant}, pregnancy_weeks={pregnancy_weeks or 'not provided'}.\n\n"
                f"Context from the Gale Encyclopedia of Medicine:\n{context}"
            ),
        }]
        if chat_history:
            messages.extend(chat_history[-6:])
        messages.append({"role": "user", "content": query})
        try:
            response = llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=600,
                temperature=0.3,
            )
            answer = response.choices[0].message.content
        except Exception:
            answer = _extractive_answer(query, chunks)

    sources = []
    seen = set()
    for chunk in chunks:
        disease = chunk["disease"]
        if disease not in seen:
            seen.add(disease)
            sources.append(disease)

    return {"answer": answer, "sources": sources, "disclaimer": DISCLAIMER, "data_source": data_source}
