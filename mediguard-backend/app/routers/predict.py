from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.data import CARDINAL_SYMPTOMS, DISEASES, SYMPTOMS as ALL_SYMPTOMS
from app.db.models import Disease, PredictionLog
from app.db.session import get_db
from app.ml.fuzzy_match import normalize_symptom_list, normalize_symptom_text
from app.ml.predictor import DiseasePredictor
from app.schemas.predict import (
    ClarifyInput,
    ClarifyResponse,
    FeedbackInput,
    NormalizeInput,
    NormalizeResponse,
    SymptomInput,
)
from app.db.models import PredictionFeedback
from app.utils.dependencies import optional_user
from app.utils.translate import translate_list, translate_text

router = APIRouter()
predictor = DiseasePredictor()

# Build a lookup of disease_name → symptom set for quick clarify logic
_DISEASE_SYMPTOM_MAP: dict[str, set[str]] = {
    d["name"]: {s.lower() for s in d["symptoms"]}
    for d in DISEASES
}


def enrich_predictions_from_database(results: list[dict], db: Session) -> list[dict]:
    rows = db.query(Disease).all()
    by_name = {row.name.lower(): row for row in rows}
    by_slug = {row.slug.lower(): row for row in rows}
    enriched = []
    for item in results:
        key = (item.get("disease") or item.get("name") or "").lower()
        slug = (item.get("slug") or "").lower()
        disease = by_name.get(key) or by_slug.get(slug)
        if disease:
            disease_symptoms = disease.symptoms or item.get("symptoms", [])
            # Compute matched symptoms for explainability
            submitted = {s.lower() for s in item.get("symptoms", [])}
            matched = [s for s in disease_symptoms if s.lower() in submitted]
            item = {
                **item,
                "id": disease.slug,
                "slug": disease.slug,
                "name": disease.name,
                "disease": disease.name,
                "category": disease.category,
                "severity": disease.severity,
                "description": disease.description,
                "symptoms": disease_symptoms,
                "matched_symptoms": matched,
                "causes": disease.causes or "",
                "treatment": disease.treatment or "",
                "prevention": disease.prevention or [],
                "database_source": "diseases",
            }
        enriched.append(item)
    return enriched


# ---------------------------------------------------------------------------
# GET /symptoms
# ---------------------------------------------------------------------------
@router.get("/symptoms")
def list_symptoms():
    return {"symptoms": predictor.symptoms}


# ---------------------------------------------------------------------------
# POST /normalize-symptoms
# Convert free-text to canonical symptom names (fuzzy + alias matching)
# ---------------------------------------------------------------------------
@router.post("/normalize-symptoms", response_model=NormalizeResponse)
def normalize_symptoms(body: NormalizeInput):
    """
    Accept a free-text symptom description and return canonical symptom names.

    Examples:
      "I have a headche and running nose" → ["Headache", "Runny nose"]
      "feaver with body ache"             → ["Fever", "Muscle aches"]
      "diarrhoea and vommiting"           → ["Diarrhea", "Vomiting"]
    """
    matched = normalize_symptom_text(body.text, predictor.symptoms)

    # Also try treating the whole text as a comma-separated list
    if not matched:
        parts = [p.strip() for p in body.text.replace(";", ",").split(",") if p.strip()]
        matched = normalize_symptom_list(parts, predictor.symptoms)

    return NormalizeResponse(matched=matched, original=body.text)


# ---------------------------------------------------------------------------
# POST /predict
# ---------------------------------------------------------------------------
@router.post("/predict")
def predict(
    body: SymptomInput,
    db: Session = Depends(get_db),
    user=Depends(optional_user),
):
    # Normalize any misspellings/informal names in the submitted list
    normalized = normalize_symptom_list(body.symptoms, predictor.symptoms)
    if not normalized:
        normalized = body.symptoms  # fall back to raw if nothing matched

    results = enrich_predictions_from_database(predictor.predict(normalized), db)

    pregnancy_note = None
    fatigue_note = None
    fatigue_terms = {"Fatigue", "Weakness", "Body weakness", "Dizziness", "Headache", "Muscle aches"}
    fatigue_relevant = body.fatigue_context or any(symptom in fatigue_terms for symptom in normalized)
    if fatigue_relevant:
        fatigue_note = (
            "Some symptoms can be worsened by tiredness, poor sleep, dehydration, stress, heavy work, or recent exertion. "
            "Rest, drink safe fluids, eat if you have missed meals, and monitor whether symptoms improve. "
            "Still seek clinical care if symptoms are severe, persistent, worsening, or come with fever, chest pain, shortness of breath, fainting, confusion, bleeding, or pregnancy warning signs."
        )
        for item in results:
            item["fatigue_context"] = True
            item["fatigue_note"] = (
                "Consider whether fatigue, poor sleep, dehydration, stress, or heavy activity may be contributing, "
                "but do not ignore disease warning signs."
            )

    pregnancy_warning_symptoms = {
        "Vaginal bleeding", "Severe abdominal pain", "Reduced fetal movement",
        "Leaking fluid", "Contractions", "Face swelling", "Hand swelling",
        "Severe headache", "Vision changes", "Blurred vision", "Fever",
        "Chest pain", "Shortness of breath", "Dizziness",
    }
    pregnancy_suggestive_symptoms = {
        "Missed period", "Breast pain", "Breast tenderness", "Morning sickness",
        "Food cravings", "Frequent urination", "Fatigue", "Nausea", "Vomiting",
    }
    has_pregnancy_warning = any(symptom in pregnancy_warning_symptoms for symptom in normalized)
    has_pregnancy_suggestive = any(symptom in pregnancy_suggestive_symptoms for symptom in normalized)

    if body.is_pregnant:
        pregnancy_note = (
            "Pregnancy can change how symptoms should be assessed. Seek prompt antenatal or clinical care for "
            "vaginal bleeding, severe abdominal pain, severe headache, vision changes, swelling of face or hands, "
            "fever, reduced fetal movement, fainting, chest pain, or shortness of breath."
        )
        for item in results:
            item["pregnancy_context"] = True
            if item.get("disease") in {
                "Malaria", "Hypertension", "Iron Deficiency Anemia", "Cystitis UTI",
                "Hepatitis B", "HIV AIDS", "Sickle Cell Crisis",
            }:
                item["pregnancy_warning"] = (
                    "This condition can be more important during pregnancy. "
                    "Please seek clinical assessment promptly."
                )
            if has_pregnancy_warning:
                item["pregnancy_warning"] = (
                    "You reported a pregnancy warning symptom. Please seek urgent antenatal or clinical care."
                )
    elif has_pregnancy_warning or has_pregnancy_suggestive:
        pregnancy_note = (
            "Some reported symptoms can be related to pregnancy or can be more urgent if pregnancy is possible. "
            "Use a pregnancy test or antenatal clinic if pregnancy may apply, and seek urgent care for bleeding, "
            "severe abdominal pain, vision changes, swelling of face or hands, leaking fluid, contractions, "
            "reduced fetal movement, chest pain, fainting, or shortness of breath."
        )

    top = results[0]["disease"] if results else "Unknown"
    # Surface the actual prediction engine used so the frontend / logs can display it
    data_source = results[0].get("data_source", "rule_based") if results else "no_results"

    log = PredictionLog(
        user_id=user.id if user else None,
        symptoms=normalized,
        predictions=results,
        top_disease=top,
        age_group=body.age_group or None,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    translated_results = _translate_results(results, body.lang)

    return {
        "predictions": translated_results,
        "normalized_symptoms": normalized,
        "prediction_log_id": log.id,
        "pregnancy_note": translate_text(pregnancy_note, body.lang),
        "fatigue_note": translate_text(fatigue_note, body.lang),
        "data_source": data_source,
        "disclaimer": translate_text(
            "MediGuard is not a medical diagnosis. Consult a qualified health professional.", body.lang
        ),
    }


# ---------------------------------------------------------------------------
# POST /predict/clarify
# Generate follow-up yes/no questions to narrow down diagnosis
# ---------------------------------------------------------------------------
@router.post("/predict/clarify", response_model=ClarifyResponse)
def clarify(body: ClarifyInput):
    """
    Given current symptoms and top candidate diseases, return 3-5 yes/no
    follow-up questions about discriminating symptoms.

    A discriminating symptom is one that is present in some candidate diseases
    but absent in others — answering it helps the model narrow the prediction.

    Rules:
    - Never ask about symptoms the user already reported (current_symptoms).
    - Never ask about symptoms already asked in a prior round (already_asked).
    - Only include candidate diseases that satisfy their cardinal symptom
      requirement (at least one cardinal symptom must be in current_symptoms).
    """
    current_lower = {s.lower() for s in body.current_symptoms}
    already_asked_lower = {s.lower() for s in body.already_asked}

    # Use provided top diseases or run a quick prediction to get them
    if body.top_diseases:
        raw_candidates = body.top_diseases[:5]
    else:
        preds = predictor.predict(body.current_symptoms)
        raw_candidates = [p["disease"] for p in preds[:5]]

    # Filter candidates through the cardinal symptom gate so we never generate
    # questions for diseases the user couldn't possibly have based on their
    # reported symptoms (e.g. don't ask "do you have jaw stiffness?" to help
    # distinguish Tetanus when the user has no jaw stiffness at all).
    candidates: list[str] = []
    for name in raw_candidates:
        cardinals = CARDINAL_SYMPTOMS.get(name)
        if cardinals:
            cardinals_lower = {c.lower() for c in cardinals}
            if not (current_lower & cardinals_lower):
                continue  # Cardinal symptom missing — exclude from clarification too
        candidates.append(name)

    if not candidates:
        return ClarifyResponse(questions=[], should_ask=False)

    # Build candidate symptom sets
    cand_symptoms: dict[str, set[str]] = {}
    for name in candidates:
        if name in _DISEASE_SYMPTOM_MAP:
            cand_symptoms[name] = _DISEASE_SYMPTOM_MAP[name]
        else:
            # Try case-insensitive lookup
            for k, v in _DISEASE_SYMPTOM_MAP.items():
                if k.lower() == name.lower():
                    cand_symptoms[name] = v
                    break

    # Find discriminating symptoms:
    # - Not yet reported by user
    # - Not already asked
    # - Present in at least 1 candidate disease (but not all) ← discriminating
    all_cand_symptoms: set[str] = set()
    for s_set in cand_symptoms.values():
        all_cand_symptoms |= s_set

    discriminating: list[tuple[str, list[str], int]] = []  # (symptom_lower, diseases, priority)
    for symptom_lower in all_cand_symptoms:
        if symptom_lower in current_lower or symptom_lower in already_asked_lower:
            continue
        diseases_with = [d for d, sset in cand_symptoms.items() if symptom_lower in sset]
        diseases_without = [d for d in candidates if d not in diseases_with]

        # Only ask if it distinguishes at least one disease from at least one other
        if not diseases_with or not diseases_without:
            continue

        # Priority: prefer symptoms that split candidates 50/50 (most info gain)
        total = len(candidates)
        split_balance = min(len(diseases_with), total - len(diseases_with))
        discriminating.append((symptom_lower, diseases_with, split_balance))

    # Sort by best split balance descending, then alphabetically for determinism
    discriminating.sort(key=lambda x: (-x[2], x[0]))

    # Build canonical questions (up to 5)
    questions: list[dict] = []
    seen_symptoms: set[str] = set()
    canonical_map = {s.lower(): s for s in predictor.symptoms}

    for symptom_lower, diseases_with, _ in discriminating:
        if len(questions) >= 5:
            break
        if symptom_lower in seen_symptoms:
            continue

        canonical = canonical_map.get(symptom_lower, symptom_lower.title())
        question_text = translate_text(_make_question(canonical), body.lang)
        questions.append({
            "symptom": canonical,
            "question": question_text,
            "helps_distinguish": diseases_with,
        })
        seen_symptoms.add(symptom_lower)

    # Only bother asking if top 2 predictions are within 25% confidence
    preds = predictor.predict(body.current_symptoms)
    should_ask = False
    if len(preds) >= 2:
        top_prob = preds[0].get("probability", 0)
        second_prob = preds[1].get("probability", 0)
        should_ask = (top_prob - second_prob) < 25 and bool(questions)
    elif bool(questions):
        should_ask = True

    return ClarifyResponse(questions=questions, should_ask=should_ask)


# ---------------------------------------------------------------------------
# POST /predict/feedback
# ---------------------------------------------------------------------------
@router.post("/predict/feedback")
def submit_feedback(
    body: FeedbackInput,
    db: Session = Depends(get_db),
    user=Depends(optional_user),
):
    fb = PredictionFeedback(
        prediction_log_id=body.prediction_log_id,
        user_id=user.id if user else None,
        top_predicted=body.top_predicted,
        was_helpful=body.was_helpful,
        confirmed_disease=body.confirmed_disease,
        comment=body.comment,
    )
    db.add(fb)
    db.commit()
    return {"message": "Feedback recorded. Thank you for helping improve MediGuard."}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _translate_results(results: list[dict], lang: str | None) -> list[dict]:
    """Translate the human-readable text fields of each prediction to French.

    Identifiers used for lookups/styling (name, disease, slug, category,
    severity, symptoms, matched_symptoms) are left untouched.
    """
    if lang != "fr" or not results:
        return results

    translated = []
    for item in results:
        new_item = dict(item)
        new_item["description"] = translate_text(item.get("description"), lang)
        new_item["causes"] = translate_text(item.get("causes"), lang)
        new_item["treatment"] = translate_text(item.get("treatment"), lang)
        if item.get("prevention"):
            new_item["prevention"] = translate_list(item["prevention"], lang)
        if item.get("fatigue_note"):
            new_item["fatigue_note"] = translate_text(item["fatigue_note"], lang)
        if item.get("pregnancy_warning"):
            new_item["pregnancy_warning"] = translate_text(item["pregnancy_warning"], lang)
        translated.append(new_item)
    return translated


def _make_question(symptom: str) -> str:
    """Convert a symptom name to a friendly yes/no question."""
    _Q_MAP = {
        "Fever": "Do you have a fever (raised body temperature)?",
        "Chills": "Are you experiencing chills or shivering?",
        "Sweating": "Are you sweating more than usual?",
        "Headache": "Do you have a headache?",
        "Severe headache": "Is the headache very severe or throbbing?",
        "Nausea": "Are you feeling sick or nauseous?",
        "Vomiting": "Have you been vomiting?",
        "Fatigue": "Are you feeling unusually tired or fatigued?",
        "Muscle aches": "Do you have muscle pain or body aches?",
        "Joint pain": "Are your joints painful or swollen?",
        "Rash": "Do you have a skin rash?",
        "Itchy rash": "Is the rash itchy?",
        "Blisters": "Do you have blisters on your skin?",
        "Diarrhea": "Do you have diarrhoea (loose or watery stools)?",
        "Bloody or mucus-filled diarrhea": "Does your stool contain blood or mucus?",
        "Cough": "Do you have a cough?",
        "Chronic cough": "Have you had a persistent cough for more than 2 weeks?",
        "Coughing up blood": "Have you coughed up blood?",
        "Shortness of breath": "Are you experiencing shortness of breath?",
        "Chest pain": "Do you have chest pain or discomfort?",
        "Chest tightness": "Does your chest feel tight?",
        "Wheezing": "Do you hear a whistling sound when breathing?",
        "Stiff neck": "Is your neck stiff or painful to move?",
        "Sensitivity to light": "Does bright light hurt your eyes?",
        "Confusion": "Are you feeling confused or disoriented?",
        "Seizures": "Have you had any fits or convulsions?",
        "Jaundice": "Has your skin or the whites of your eyes turned yellow?",
        "Dark urine": "Is your urine unusually dark (brown or tea-coloured)?",
        "Yellow eyes": "Do the whites of your eyes look yellow?",
        "Weight loss": "Have you lost significant weight recently without trying?",
        "Night sweats": "Do you wake up at night drenched in sweat?",
        "Pale skin": "Has your skin appeared unusually pale?",
        "Swollen lymph nodes": "Do you have any swollen or tender lumps in your neck, armpits, or groin?",
        "Painful urination": "Is urinating painful or burning?",
        "Frequent urination": "Are you urinating much more often than usual?",
        "Blood in urine": "Have you noticed blood in your urine?",
        "Back pain": "Do you have pain in your back or sides?",
        "Pelvic pain": "Do you have pain in your lower abdomen or pelvis?",
        "Vaginal discharge": "Do you have unusual vaginal discharge?",
        "Jaw stiffness": "Is your jaw stiff or difficult to open (like lockjaw)?",
        "Difficulty swallowing": "Is it painful or difficult to swallow?",
        "Hoarse voice": "Has your voice become hoarse or raspy?",
        "Ear pain": "Do you have pain in one or both ears?",
        "Hearing loss": "Have you noticed any hearing loss or muffled sounds?",
        "Red eyes": "Are your eyes red or irritated?",
        "Eye discharge": "Do you have discharge coming from your eyes?",
        "Nasal congestion": "Is your nose blocked or congested (even without a runny nose)?",
        "Facial pain": "Do you have pain or pressure in your face (cheeks, forehead, around eyes)?",
        "Ring-shaped rash": "Do you have a ring-shaped or circular red rash?",
        "Hair loss": "Have you noticed unusual hair loss or bald patches?",
        "Low blood pressure": "Have you felt faint, dizzy, or is your blood pressure known to be low?",
        "Fast heartbeat": "Is your heart beating very fast or racing?",
        "Swollen feet": "Are your feet or legs swollen?",
        "Abdominal pain": "Do you have pain in your stomach or abdomen?",
        "Loss of appetite": "Have you lost your appetite or stopped wanting to eat?",
        "Skin lesions": "Do you have any skin sores, marks, or unusual skin changes?",
        "Skin sores": "Do you have painful sores on your skin?",
        "Pus or discharge": "Is there pus or discharge from any wound or sore?",
        "Blurred vision": "Is your vision blurred?",
        "Dizziness": "Are you feeling dizzy or lightheaded?",
        "Increased thirst": "Are you feeling very thirsty all the time?",
        "Slow-healing sores": "Do wounds or sores heal very slowly?",
    }
    return _Q_MAP.get(symptom, f"Are you experiencing {symptom.lower()}?")
