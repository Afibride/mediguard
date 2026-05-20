"""
MediGuard RAG pipeline.

Uses Pinecone + OpenAI when configured, and falls back to local encyclopedia
chunks so the backend remains usable before the one-time Pinecone ingest runs.
"""

import json
import os
import re
import time
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

from app.data import DISEASES, SYMPTOM_DESCRIPTIONS, SYMPTOMS
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

# Cache for weak topics derived from low-rated chat feedback
_weak_topics_cache: list[str] = []
_weak_topics_ts: float = 0.0
_WEAK_CACHE_TTL = 600  # 10 minutes

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


SYMPTOM_DEFINITIONS: dict[str, str] = {
    "fever": (
        "A fever is a temporary rise in body temperature above the normal range of 36–37.5°C (97–99.5°F), "
        "usually above 38°C (100.4°F). It is the body's natural defence response — an elevated temperature "
        "makes the environment less hospitable for many bacteria and viruses. Fever often comes with chills, "
        "sweating, headache, muscle aches, and loss of appetite. Prolonged or very high fever (above 40°C/104°F) "
        "needs prompt medical attention."
    ),
    "rash": (
        "A rash is any change in the skin's colour, texture, or appearance — it may be flat (macular), "
        "raised (papular), blistered (vesicular), or pustular. Rashes can be localised to one area or spread "
        "across the body. They can be itchy, painful, or painless. The exact look of a rash is an important "
        "diagnostic clue: rashes from different diseases spread and appear differently."
    ),
    "cough": (
        "A cough is a reflex action to clear the airway of mucus, irritants, or foreign material. "
        "It can be dry (no mucus) or productive (with phlegm). A cough lasting more than 3 weeks is considered "
        "chronic and warrants evaluation. Key features to note: whether it is dry or wet, whether it produces "
        "blood-streaked sputum, whether it worsens at night, and whether it is associated with breathing difficulty."
    ),
    "headache": (
        "A headache is pain or discomfort felt in the head, scalp, or neck. It can be throbbing, pressing, "
        "squeezing, or stabbing in character. Tension headaches are the most common type. When headache occurs "
        "with fever, stiff neck, sensitivity to light, or confusion, it may signal a serious infection such as "
        "meningitis and requires urgent care."
    ),
    "fatigue": (
        "Fatigue is a state of persistent tiredness or exhaustion that is not relieved by normal rest. "
        "It can be physical (muscle weakness, heaviness) or mental (difficulty concentrating, low motivation). "
        "While lifestyle factors like poor sleep, dehydration, skipped meals, and overwork can cause fatigue, "
        "it is also a common symptom of infections, anemia, thyroid disorders, and many other conditions."
    ),
    "nausea": (
        "Nausea is an unpleasant queasy feeling in the stomach, often accompanied by the urge to vomit, "
        "increased saliva, and sweating. It can be triggered by infections (especially gastrointestinal), "
        "food poisoning, medications, motion sickness, pregnancy, or conditions affecting the inner ear or brain. "
        "Persistent nausea lasting more than 24 hours should be evaluated."
    ),
    "vomiting": (
        "Vomiting is the forceful expulsion of stomach contents through the mouth. It can be caused by "
        "infections, food poisoning, medications, motion sickness, appendicitis, or brain conditions. "
        "Repeated vomiting leads to dehydration and electrolyte imbalance — warning signs include no urination "
        "for 8+ hours, dry mouth, dizziness, and sunken eyes. Blood in vomit requires immediate medical attention."
    ),
    "diarrhea": (
        "Diarrhea is passing loose or watery stools three or more times in a day. It can be caused by "
        "bacterial, viral, or parasitic infections, contaminated food or water, or irritable bowel conditions. "
        "The main danger of diarrhea is dehydration. Seek urgent care for blood in stool, severe abdominal pain, "
        "high fever, or signs of dehydration (extreme thirst, no urine, sunken eyes, rapid pulse)."
    ),
    "chills": (
        "Chills are episodes of shivering with a feeling of cold, caused by the body's attempt to raise its "
        "temperature. They often signal the start of a fever as the body fights infection. Chills followed by "
        "a spiking fever that then 'breaks' with sweating are classic in malaria. Severe chills with no fever "
        "or very low temperature (hypothermia) also need attention."
    ),
    "sweating": (
        "Sweating is the body's mechanism for cooling down by releasing fluid through sweat glands. "
        "In illness, drenching sweats often accompany the breaking of a fever. Night sweats (soaking the "
        "clothes or bedding during sleep) can be a sign of tuberculosis, HIV, lymphoma, or other systemic "
        "conditions and should be investigated if persistent."
    ),
    "abdominal pain": (
        "Abdominal pain is discomfort or pain in the area between the chest and groin. It can be cramping, "
        "sharp, dull, or colicky. Causes include gastroenteritis, appendicitis, kidney stones, peptic ulcers, "
        "and liver or spleen enlargement (common in malaria and typhoid). Severe sudden-onset pain, pain with "
        "fever and rigid abdomen, or pain with vomiting of blood require urgent care."
    ),
    "chest pain": (
        "Chest pain is any discomfort or pain in the chest area. While benign causes exist (muscle strain, "
        "acid reflux, costochondritis), chest pain can also signal heart attack, pneumonia, pleuritis, "
        "pulmonary embolism, or pericarditis. Crushing central chest pain radiating to the arm or jaw, "
        "or pain with breathlessness, is a medical emergency."
    ),
    "shortness of breath": (
        "Shortness of breath (dyspnea) is the feeling of not getting enough air. It can occur with exertion "
        "or at rest. Causes include asthma, pneumonia, pleural effusion, anemia, heart failure, and allergic "
        "reactions. Sudden severe breathlessness — especially with chest pain, blue lips, or rapid heartbeat — "
        "is a medical emergency requiring immediate care."
    ),
    "joint pain": (
        "Joint pain (arthralgia) is aching, soreness, or stiffness in one or more joints. When accompanied "
        "by fever and rash it may indicate viral infections like dengue, chikungunya, or rheumatic fever. "
        "Inflammation with redness and warmth (arthritis) suggests an inflammatory cause. Severe pain in a "
        "single hot swollen joint may indicate septic arthritis, which is an emergency."
    ),
    "muscle pain": (
        "Muscle pain (myalgia) is aching or soreness in the muscles, often described as a feeling of "
        "'body aches'. In systemic infections the immune system releases inflammatory chemicals (cytokines) "
        "that cause widespread muscle discomfort. Severe localised muscle pain, especially with swelling or "
        "weakness, can indicate a more specific muscle condition."
    ),
    "loss of appetite": (
        "Loss of appetite (anorexia) is a reduced desire to eat. It is a very common non-specific symptom "
        "that accompanies many infections, as the body redirects energy toward fighting illness. Prolonged "
        "loss of appetite with unintentional weight loss should be evaluated, as it can also be a sign of "
        "tuberculosis, liver disease, cancer, or chronic infections."
    ),
    "weight loss": (
        "Unintentional weight loss is losing body weight without trying — generally more than 5% of body "
        "weight over 6–12 months. It can be caused by infections (tuberculosis, HIV), cancer, diabetes, "
        "thyroid disease, or severe malnutrition. When combined with night sweats and persistent cough, it "
        "is a classic warning sign for tuberculosis."
    ),
    "sore throat": (
        "A sore throat is pain, scratchiness, or irritation of the throat that often worsens when "
        "swallowing. It can be caused by viral infections (common cold, influenza, COVID-19), bacterial "
        "infections (streptococcal pharyngitis), or environmental irritants. A sore throat with white "
        "patches, high fever, or swollen lymph nodes may need antibiotic treatment."
    ),
    "runny nose": (
        "A runny nose (rhinorrhea) is excess nasal discharge — it can be clear, white, yellow, or green. "
        "Clear discharge often indicates a viral infection or allergy; thick coloured discharge may suggest "
        "a bacterial secondary infection. Runny nose combined with body aches and fever typically points to "
        "influenza rather than a simple cold."
    ),
    "skin lesion": (
        "A skin lesion is any abnormal area of skin — it can be a sore, ulcer, blister, spot, or growth. "
        "The type, location, edge, colour, and whether it is painful or painless all help identify the cause. "
        "Painless skin lesions can be associated with conditions like leprosy or some STIs."
    ),
    "swollen lymph nodes": (
        "Swollen lymph nodes (lymphadenopathy) are enlarged glands that are part of the immune system. "
        "They swell when fighting an infection nearby. Generalised lymph node swelling (in armpits, neck, "
        "and groin) combined with fever and weight loss raises concern for HIV, lymphoma, or tuberculosis."
    ),
    "jaundice": (
        "Jaundice is a yellow colouring of the skin and whites of the eyes caused by excess bilirubin in "
        "the blood. It indicates that the liver is not processing bilirubin normally — due to liver disease "
        "(hepatitis, cirrhosis), bile duct obstruction, or destruction of red blood cells (haemolytic anaemia "
        "or severe malaria). New-onset jaundice always warrants prompt medical evaluation."
    ),
    "seizure": (
        "A seizure is a sudden, uncontrolled electrical disturbance in the brain that can cause changes in "
        "behaviour, movements, feelings, and levels of consciousness. In the context of infection, seizures "
        "can be triggered by very high fever (febrile seizures, common in young children), meningitis, "
        "cerebral malaria, or encephalitis. A first seizure or any seizure with persistent loss of "
        "consciousness requires emergency evaluation."
    ),
}

DISEASE_ALIASES: dict[str, str] = {
    # Chickenpox variants
    "chicken pox": "Chickenpox", "chickenpox": "Chickenpox", "varicella": "Chickenpox",
    # HIV/AIDS
    "hiv": "HIV AIDS", "aids": "HIV AIDS", "hiv/aids": "HIV AIDS", "hiv aids": "HIV AIDS",
    # Common cold
    "cold": "Common Cold",
    # Shingles
    "shingles": "Herpes Zoster",
    # UTI
    "uti": "Cystitis UTI", "urinary tract infection": "Cystitis UTI", "cystitis": "Cystitis UTI",
    # Peptic ulcer
    "peptic ulcer": "Helicobacteriosis PepticUlcer", "stomach ulcer": "Helicobacteriosis PepticUlcer",
    "h. pylori": "Helicobacteriosis PepticUlcer", "helicobacter": "Helicobacteriosis PepticUlcer",
    # PID
    "pid": "Pelvic Inflammatory Disease",
    # Sickle cell
    "sickle cell": "Sickle Cell Crisis", "sca": "Sickle Cell Crisis",
    # Whooping cough
    "pertussis": "Whooping Cough",
    # Fungal
    "tinea": "Skin Fungal Infection", "fungal infection": "Skin Fungal Infection",
    # Diabetes
    "diabetes": "Diabetes Mellitus", "type 2 diabetes": "Diabetes Mellitus",
    # Hypertension
    "high blood pressure": "Hypertension",
    # BPH
    "bph": "Benign Prostatic Hyperplasia", "enlarged prostate": "Benign Prostatic Hyperplasia",
    # Others
    "typhoid": "Typhoid Fever", "dengue": "Dengue Fever",
    "hepatitis a": "Hepatitis A", "hepatitis b": "Hepatitis B",
    "kidney stone": "Kidney Stones", "renal calculi": "Kidney Stones",
    "tb": "Tuberculosis",
    "lockjaw": "Tetanus",
    "pink eye": "Conjunctivitis",
    "stomach flu": "Gastroenteritis",
    "anemia": "Iron Deficiency Anemia",
    "elephantiasis": "Filariasis",
    "river blindness": "Onchocerciasis",
    "blood poisoning": "Septicemia",
    "boil": "Skin Abscess",
    "german measles": "Rubella",
    "anaphylactic shock": "Anaphylaxis",
    "otitis": "Ear Infection",
}

# Build lookup by canonical name for fast access
_DISEASE_BY_NAME: dict[str, dict] = {d["name"]: d for d in DISEASES}

DISEASE_SYMPTOM_QUERY_PATTERNS = [
    re.compile(r"^\s*symptoms\s+of\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*signs\s+of\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*what\s+are\s+(?:the\s+)?symptoms?\s+(?:of|for)\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*what\s+are\s+(?:the\s+)?signs?\s+(?:of|for)\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(.+?)\s+symptoms\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*how\s+does\s+(.+?)\s+(?:present|manifest|show|appear)\s*[?.!]*\s*$", re.I),
]

SYMPTOM_DEFINITION_PATTERNS = [
    re.compile(r"^\s*what\s+(?:is|are)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(?:define|explain)\s+(?:a\s+|an\s+|the\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*tell\s+me\s+about\s+(?:a\s+|an\s+|the\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*what\s+does\s+(.+?)\s+(?:mean|feel\s+like|look\s+like)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*meaning\s+of\s+(.+?)\s*[?.!]*\s*$", re.I),
]


def _extract_symptom_term(query: str) -> str | None:
    for pattern in SYMPTOM_DEFINITION_PATTERNS:
        match = pattern.match(query.strip())
        if match:
            return match.group(1).strip().lower()
    return None


def _symptom_definition_response(query: str) -> dict | None:
    term = _extract_symptom_term(query)
    if not term:
        return None

    # Check for an exact or near match in our definitions table
    definition = SYMPTOM_DEFINITIONS.get(term)
    if not definition:
        # Try substring match (e.g. "high fever" → "fever")
        for key, val in SYMPTOM_DEFINITIONS.items():
            if key in term or term in key:
                definition = val
                term = key
                break

    if not definition:
        return None

    # Gather how this symptom appears in specific diseases from SYMPTOM_DESCRIPTIONS
    disease_examples: list[str] = []
    for disease_name, desc_map in SYMPTOM_DESCRIPTIONS.items():
        for sym_key, sym_desc in desc_map.items():
            if term in sym_key.lower() or sym_key.lower() in term:
                disease_examples.append(f"• **{disease_name}**: {sym_desc}")
                break
    disease_examples = disease_examples[:5]

    answer_parts = [definition]
    if disease_examples:
        answer_parts.append(
            f"\n\nHow **{term}** specifically appears in different diseases:"
        )
        answer_parts.extend(disease_examples)
    answer_parts.append(
        "\n\nIf you are experiencing this symptom yourself, describe it to a qualified healthcare "
        "professional or use the MediGuard Symptom Checker for a guided assessment."
    )

    return {
        "answer": "\n".join(answer_parts),
        "sources": list({name for name, desc_map in SYMPTOM_DESCRIPTIONS.items()
                         for sym_key in desc_map if term in sym_key.lower() or sym_key.lower() in term})[:4],
        "disclaimer": DISCLAIMER,
    }


def _resolve_disease_name(term: str) -> dict | None:
    """Return a DISEASES entry for a user-supplied term, using aliases and fuzzy matching."""
    term = term.strip().lower()
    # 1. Alias lookup (longest-key-first to avoid partial hits)
    for alias in sorted(DISEASE_ALIASES, key=len, reverse=True):
        if alias in term or term in alias:
            d = _DISEASE_BY_NAME.get(DISEASE_ALIASES[alias])
            if d:
                return d
    # 2. Direct name / slug match
    for d in DISEASES:
        names = {
            d["name"].lower(),
            d["slug"].replace("-", " ").lower(),
            d["name"].lower().replace(" ", ""),
        }
        if any(n and len(n) > 2 and (n in term or term in n) for n in names):
            return d
    return None


def _disease_symptoms_response(query: str) -> dict | None:
    term = None
    for pattern in DISEASE_SYMPTOM_QUERY_PATTERNS:
        match = pattern.match(query.strip())
        if match:
            term = match.group(1).strip()
            break

    # Fuzzy fallback: if no pattern matched, check for "symptom*" anywhere + disease name
    if not term:
        text = query.lower()
        if re.search(r"\bsymptom", text) or re.search(r"\bsign(s)?\b", text) or re.search(r"\bpresent", text):
            d = _detect_disease(query)
            if d:
                term = d["name"]

    if not term:
        return None

    disease = _resolve_disease_name(term)
    if not disease:
        return None

    symptoms = disease.get("symptoms") or []
    if not symptoms:
        return None

    desc_map = SYMPTOM_DESCRIPTIONS.get(disease["name"], {})
    lines = [f"**{disease['name']}** commonly presents with these symptoms:\n"]
    for sym in symptoms:
        sym_lower = sym.lower().replace("_", " ")
        desc = next(
            (val for key, val in desc_map.items()
             if key.lower() == sym_lower or key.lower() in sym_lower or sym_lower in key.lower()),
            None,
        )
        if desc:
            lines.append(f"• **{sym.replace('_', ' ')}**: {desc}")
        else:
            lines.append(f"• {sym.replace('_', ' ')}")

    lines.append(
        "\n\nThis information is for educational purposes only. "
        "Always consult a qualified healthcare professional for proper diagnosis and treatment."
    )
    return {
        "answer": "\n".join(lines),
        "sources": [disease["name"]],
        "disclaimer": DISCLAIMER,
    }


DISEASE_GENERAL_PATTERNS = [
    re.compile(r"^\s*what\s+is\s+(?:a\s+|an\s+|the\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*what\s+are\s+(?:the\s+)?(?:main\s+)?facts?\s+about\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(?:describe|overview\s+of|explain)\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(?:tell\s+me\s+(?:more\s+)?about|info(?:rmation)?\s+on|about)\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(?:define)\s+(.+?)\s*[?.!]*\s*$", re.I),
]

# Terms that indicate other, more specific handlers should handle it
_GENERAL_SKIP_TERMS = {
    "symptom", "sign of", "prevent", "prevention", "treatment", "treat",
    "cure", "cause", "causes", "spread", "how do i", "how can i",
}


def _disease_general_info_response(query: str) -> dict | None:
    """Handle 'what is malaria', 'tell me about typhoid', etc. directly from the database."""
    text = query.lower()
    # Let more specific handlers deal with symptom/prevention/treatment/cause queries
    if any(t in text for t in _GENERAL_SKIP_TERMS):
        return None

    # Extract candidate term from general patterns
    candidate = None
    for pat in DISEASE_GENERAL_PATTERNS:
        m = pat.match(query.strip())
        if m:
            candidate = m.group(1).strip()
            break

    # If no pattern matched, only proceed if the query is short (≤5 words) and contains a disease name
    if not candidate:
        if len(query.split()) > 5:
            return None
        candidate = query.strip()

    disease = _resolve_disease_name(candidate)
    if not disease:
        disease = _detect_disease(query)
    if not disease:
        return None

    profile = _database_disease_profile(disease["name"])
    if not profile:
        return None

    symptoms = disease.get("symptoms") or []
    lines = [f"**{disease['name']}**\n"]

    if profile.get("description"):
        lines.append(profile["description"])

    if symptoms:
        sym_display = [s.replace("_", " ") for s in symptoms[:8]]
        lines.append(f"\n**Common Symptoms:** {', '.join(sym_display)}")

    if profile.get("causes"):
        lines.append(f"\n**Causes/Spread:** {profile['causes']}")

    if profile.get("treatment"):
        lines.append(f"\n**Treatment Overview:** {profile['treatment']}")

    prevention = profile.get("prevention") or disease.get("prevention") or []
    if isinstance(prevention, str):
        prevention = [p.strip() for p in re.split(r"[;\n]", prevention) if p.strip()]
    if prevention:
        lines.append(f"\n**Prevention:** {', '.join(prevention[:4])}")

    lines.append(
        "\n\nThis is for educational purposes only. "
        "Use the MediGuard Symptom Checker for a guided assessment, and always consult a qualified healthcare professional for personal health concerns."
    )
    return {
        "answer": "\n".join(lines),
        "sources": [disease["name"]],
        "disclaimer": DISCLAIMER,
        "data_source": "database",
    }


def _disease_topic_intent(query: str) -> str | None:
    text = query.lower()
    if any(term in text for term in ["prevent", "prevention", "avoid", "protect against", "stop getting"]):
        return "prevention"
    if any(term in text for term in ["treat", "treatment", "cure", "manage", "medicine", "medication"]):
        return "treatment"
    if any(term in text for term in ["cause", "causes", "spread", "transmit", "transmitted", "get infected"]):
        return "causes"
    return None


def _pinecone_disease_profile(disease_name: str) -> dict | None:
    index = _get_index()
    if index is None:
        return None
    try:
        results = index.query(
            vector=embed_text(disease_name, dim=_pinecone_dimension or 384),
            top_k=1,
            include_metadata=True,
            filter={"data_type": {"$eq": "disease_profile"}, "disease": {"$eq": disease_name}},
        )
    except Exception:
        return None
    matches = results.matches if hasattr(results, "matches") else results.get("matches", [])
    if not matches:
        return None
    meta = matches[0].metadata if hasattr(matches[0], "metadata") else matches[0].get("metadata", {})
    return meta or None


def _database_disease_profile(disease_name: str) -> dict | None:
    db = SessionLocal()
    try:
        row = db.query(Disease).filter(Disease.name == disease_name).first()
        if row:
            return {
                "disease": row.name,
                "description": row.description,
                "causes": row.causes,
                "treatment": row.treatment,
                "prevention": row.prevention or [],
                "source": "database",
            }
    finally:
        db.close()
    disease = _DISEASE_BY_NAME.get(disease_name)
    if disease:
        return {
            "disease": disease["name"],
            "description": disease.get("description", ""),
            "causes": disease.get("causes", ""),
            "treatment": disease.get("treatment", ""),
            "prevention": disease.get("prevention", []),
            "source": "curated",
        }
    return None


def _disease_topic_response(query: str) -> dict | None:
    intent = _disease_topic_intent(query)
    if not intent:
        return None
    disease = _detect_disease(query)
    if not disease:
        return None

    profile = _pinecone_disease_profile(disease["name"])
    data_source = "pinecone" if profile else "database"
    if not profile:
        profile = _database_disease_profile(disease["name"])
    if not profile:
        return None

    name = profile.get("disease") or disease["name"]
    if intent == "prevention":
        prevention = profile.get("prevention") or disease.get("prevention") or []
        if isinstance(prevention, str):
            prevention = [item.strip() for item in re.split(r"[;\n]", prevention) if item.strip()]
        lines = [f"To help prevent **{name}**:"]
        if prevention:
            lines.extend(f"- {item}" for item in prevention[:6])
        elif profile.get("description"):
            lines.append(profile["description"])
        lines.append("Seek testing or clinical care early if symptoms appear, especially fever, weakness, vomiting, confusion, breathing difficulty, dehydration, or pregnancy warning signs.")
    elif intent == "treatment":
        treatment = profile.get("treatment") or disease.get("treatment") or ""
        lines = [f"Treatment overview for **{name}**:", treatment or "A qualified clinician should assess symptoms and choose appropriate care."]
        lines.append("Do not start prescription medicines without a qualified clinician. Seek urgent care for severe or worsening symptoms.")
    else:
        causes = profile.get("causes") or disease.get("causes") or ""
        lines = [f"Common causes or spread of **{name}**:", causes or profile.get("description") or "The exact cause depends on the condition and exposure history."]
        lines.append("Prevention and early care depend on the cause, so seek professional assessment for personal symptoms.")

    lines.append("MediGuard information can sometimes be incomplete or faulty, so use it as education, not a diagnosis.")
    return {
        "answer": "\n".join(lines),
        "sources": [name],
        "disclaimer": DISCLAIMER,
        "data_source": data_source,
    }


BAMENDA_FACILITIES_DATA = [
    {"name": "Bamenda Regional Hospital", "type": "Regional / Government Hospital", "address": "X43V+WH7, Bamenda, Cameroon", "phone": "+237 2 33 36 11 08", "maps": "https://www.google.com/maps/search/?api=1&query=Bamenda+Regional+Hospital+Cameroon"},
    {"name": "Nkwen Baptist Hospital Bamenda", "type": "CBC Mission Hospital", "address": "Finance Junction, Bamenda II, Mezam Division", "phone": "+237 675 205 729 / +237 683 158 210", "maps": "https://www.google.com/maps/search/?api=1&query=Nkwen+Baptist+Hospital+Bamenda+Cameroon"},
    {"name": "Mezam Polyclinic", "type": "Private Polyclinic", "address": "Azire / W4XW+G5V, Bamenda, Cameroon", "phone": "+237 6 77 68 48 78 / +237 2 33 36 34 31", "maps": "https://www.google.com/maps/search/?api=1&query=Mezam+Polyclinic+Bamenda+Cameroon"},
    {"name": "Mbingo Baptist Hospital", "type": "CBC Referral / Teaching Hospital", "address": "Belo Subdivision, North West Region, via Bamenda", "phone": "+237 677 671 621 / +237 676 221 260", "maps": "https://www.google.com/maps/search/?api=1&query=Mbingo+Baptist+Hospital+Cameroon"},
    {"name": "Banso Baptist Hospital", "type": "CBC Mission Hospital", "address": "P.O. Box 9, Banso / Kumbo, Bui Division", "phone": "+237 677 720 005 / +237 678 479 628", "maps": "https://www.google.com/maps/search/?api=1&query=Banso+Baptist+Hospital+Kumbo+Cameroon"},
    {"name": "St. Martin de Porres Catholic Mission Hospital", "type": "Catholic Mission Hospital", "address": "Njinikom, North West Region", "phone": "+237 6 65 84 26 16 / +237 6 65 84 26 19", "maps": "https://www.google.com/maps/search/?api=1&query=St+Martin+de+Porres+Catholic+Mission+Hospital+Njinikom+Cameroon"},
]

FACILITY_TERMS = [
    "hospital", "clinic", "health facility", "health centre", "health center",
    "nearest hospital", "nearby hospital", "where to go", "where can i go",
    "where should i go", "seek care", "get treatment", "see a doctor",
    "go to hospital", "find a hospital", "find a clinic", "medical facility",
    "doctor near", "pharmacy near",
]


def _facilities_response(query: str) -> dict | None:
    text = query.lower()
    if not any(term in text for term in FACILITY_TERMS):
        return None
    lines = [
        "Here are nearby health facilities in Bamenda where you can seek professional care:\n"
    ]
    for f in BAMENDA_FACILITIES_DATA:
        lines.append(
            f"• **{f['name']}** ({f['type']})\n"
            f"  Address: {f['address']}\n"
            f"  Phone: {f['phone']}\n"
            f"  Maps: {f['maps']}"
        )
    lines.append(
        "\nFor emergencies, go directly to **Bamenda Regional Hospital** (Hospital Roundabout, Up Station). "
        "You can also open Google Maps on your phone and search 'hospital near me' for real-time directions."
    )
    return {
        "answer": "\n".join(lines),
        "sources": ["Bamenda Health Facilities Directory"],
        "disclaimer": DISCLAIMER,
    }


def _facilities_response(query: str) -> dict | None:
    text = query.lower()
    if not any(term in text for term in FACILITY_TERMS):
        return None
    lines = [
        "Here are nearby health facilities connected to MediGuard's Nearby Facilities page:\n"
    ]
    for f in BAMENDA_FACILITIES_DATA:
        lines.append(
            f"- **{f['name']}** ({f['type']})\n"
            f"  Address: {f['address']}\n"
            f"  Phone: {f['phone']}\n"
            f"  Maps: {f['maps']}"
        )
    lines.append(
        "\nYou can open **Nearby Facilities** inside MediGuard at `/nearby-facilities` to view embedded map previews without leaving the system. "
        "For emergencies, go to the closest open emergency facility or call local emergency support immediately."
    )
    return {
        "answer": "\n".join(lines),
        "sources": ["Bamenda Health Facilities Directory"],
        "disclaimer": DISCLAIMER,
        "mode": "facilities",
        "data_source": "platform",
    }


def _platform_response(query: str) -> dict | None:
    text = query.strip().lower()
    platform_terms = [
        "mediguard", "this platform", "the platform", "this app", "the app", "website",
        "symptom checker", "history", "profile", "trends", "dashboard", "nearby facilities",
        "facilities page", "disease library", "chat history", "how do i use", "what can i do here",
    ]
    if not any(term in text for term in platform_terms):
        return None

    if any(term in text for term in ["nearby facilities", "hospital", "clinic", "maps", "facility"]):
        answer = (
            "Use the **Nearby Facilities** page to see hospitals and clinics with embedded map previews, phone numbers, services, "
            "and direction links. In MediGuard, open `/nearby-facilities` or use the Facilities link in the navigation."
        )
    elif "history" in text or "chat history" in text:
        answer = (
            "Your MediGuard history is available from **History** after login. It combines saved symptom screenings and chat records "
            "so you can review previous checks."
        )
    elif "profile" in text or "account" in text:
        answer = (
            "Open **Profile** after login to view your account details. The profile page is protected, so you need to be signed in first."
        )
    elif "trend" in text or "dashboard" in text:
        answer = (
            "The **Trends Dashboard** summarizes recorded screenings, top reported conditions, weekly patterns, and heatmap-style analytics "
            "from MediGuard usage data."
        )
    elif "symptom checker" in text or "diagnosis" in text or "screening" in text:
        answer = (
            "Use **Symptom Checker** to select symptoms by category and run a screening. MediGuard may ask follow-up questions, then shows "
            "possible matches, first-aid guidance, and when to seek care."
        )
    elif "disease library" in text or "diseases" in text:
        answer = (
            "The **Disease Library** lets you browse disease details, symptoms, causes, treatment overview, and prevention information "
            "stored in the MediGuard database."
        )
    else:
        answer = (
            "MediGuard can help you check symptoms, chat with the health assistant, browse disease information, view trends, review history, "
            "manage your profile, and find nearby health facilities with in-app maps."
        )

    return {
        "answer": answer,
        "sources": ["MediGuard Platform"],
        "disclaimer": DISCLAIMER,
        "mode": "platform_help",
        "data_source": "platform",
    }


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
                "or when to see a doctor. I can also explain your symptom-checker result, point you to nearby facilities, "
                "and answer questions about using MediGuard."
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
    # Alias lookup first (handles "chicken pox" → "Chickenpox" etc.)
    for alias in sorted(DISEASE_ALIASES, key=len, reverse=True):
        if alias in text:
            d = _DISEASE_BY_NAME.get(DISEASE_ALIASES[alias])
            if d:
                return d
    # Fallback: name / slug matching
    candidates = sorted(DISEASES, key=lambda item: len(item["name"]), reverse=True)
    for disease in candidates:
        names = {
            disease["name"].lower(),
            disease["slug"].replace("-", " ").lower(),
            disease["name"].lower().replace(" ", ""),
        }
        if any(name and len(name) > 2 and name in text for name in names):
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
    return any(
        "follow-up" in message
        or "need a little more information" in message
        or "i will ask one question at a time" in message
        or message.startswith("noted.")
        or "?" in message
        for message in assistant_messages
    )


# Master list of every possible follow-up question the assistant may ask.
# Any question asked will appear as a substring in an assistant message.
_ALL_FOLLOWUP_QUESTIONS = [
    "How long have you had these symptoms?",
    "Are they mild, moderate, or severe?",
    "Do you have any other symptoms, such as fever, vomiting, diarrhea, chest pain, rash, dizziness, or trouble breathing?",
    "What is your temperature, and does the fever come with chills or sweating?",
    "Is there chest pain, wheezing, fast breathing, or coughing up blood?",
    "Are you able to drink fluids, and is there blood in stool or signs of dehydration?",
    "Have you recently had poor sleep, heavy work, stress, missed meals, dehydration, or unusual exertion?",
    "How many weeks pregnant are you, and is there bleeding, severe pain, vision change, swelling, or reduced fetal movement?",
]


def _get_asked_question_set(chat_history: list[dict] | None) -> set[str]:
    """Return the set of follow-up questions already present in assistant messages."""
    if not chat_history:
        return set()
    assistant_text = "\n".join(
        m.get("content", "") for m in chat_history if m.get("role") == "assistant"
    ).lower()
    return {q for q in _ALL_FOLLOWUP_QUESTIONS if q.lower() in assistant_text}


def _next_unanswered_question(questions: list[str], asked: set[str]) -> str | None:
    for q in questions:
        if q not in asked:
            return q
    return None


def _answered_followup_count(chat_history: list[dict] | None, questions: list[str]) -> int:
    asked = _get_asked_question_set(chat_history)
    return sum(1 for q in questions if q in asked)


def _next_followup_response(
    symptoms: list[str],
    questions: list[str],
    asked_count: int,
    pregnancy_context: bool,
    fatigue_context: bool,
) -> dict:
    next_question = questions[min(asked_count, len(questions) - 1)]
    symptom_text = ", ".join(symptoms) if symptoms else "your symptoms"
    if asked_count == 0:
        answer = (
            f"I found this in your message: {symptom_text}. "
            "I will ask one question at a time before showing possible matches.\n\n"
            f"{next_question}"
        )
    else:
        answer = f"Noted. {next_question}"
    return {
        "answer": answer,
        "sources": [],
        "disclaimer": DISCLAIMER,
        "symptoms": symptoms,
        "predictions": [],
        "mode": "symptom_follow_up",
        "pregnancy_context": pregnancy_context,
        "fatigue_context": fatigue_context,
        "follow_up_questions": [next_question],
        "data_source": "database",
    }


def _recent_user_symptom_context(query: str, chat_history: list[dict] | None) -> str:
    user_parts = [
        message.get("content", "")
        for message in (chat_history or [])[-10:]
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

    asked_set = _get_asked_question_set(chat_history)
    next_q = _next_unanswered_question(follow_up_questions, asked_set)
    if next_q:
        is_first = not asked_set
        return _next_followup_response(
            reported_symptoms,
            [next_q],
            0 if is_first else 1,
            pregnancy_context,
            fatigue_context,
        )

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


def _load_weak_topics() -> list[str]:
    global _weak_topics_cache, _weak_topics_ts
    now = time.time()
    if now - _weak_topics_ts < _WEAK_CACHE_TTL:
        return _weak_topics_cache
    try:
        from datetime import datetime, timedelta
        from app.db.models import ChatFeedback
        cutoff = datetime.utcnow() - timedelta(days=30)
        db = SessionLocal()
        try:
            rows = db.query(ChatFeedback).filter(
                ChatFeedback.rating == False,  # noqa: E712
                ChatFeedback.created_at >= cutoff,
            ).all()
        finally:
            db.close()
        kw_counts: Counter = Counter()
        for row in rows:
            for kw in (row.query_keywords or []):
                kw_counts[kw.lower()] += 1
        _weak_topics_cache = [kw for kw, cnt in kw_counts.most_common(15) if cnt >= 2]
    except Exception:
        pass
    _weak_topics_ts = now
    return _weak_topics_cache


def _get_weak_topic_note(query: str) -> str:
    """Return a prompt hint when the query touches topics users previously found unhelpful."""
    weak = _load_weak_topics()
    if not weak:
        return ""
    text = query.lower()
    matched = [kw for kw in weak if kw in text]
    if not matched:
        return ""
    topics = ", ".join(matched[:3])
    return (
        f"\n\n[IMPROVEMENT NOTE: Users have previously rated responses about '{topics}' as unhelpful. "
        "Be especially clear, step-by-step, and practical on this topic. "
        "If the knowledge base lacks detail, explicitly acknowledge the limitation and recommend "
        "consulting a qualified clinician at a nearby facility.]"
    )


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

    facilities = _facilities_response(query)
    if facilities:
        return facilities

    platform = _platform_response(query)
    if platform:
        return platform

    symptom_definition = _symptom_definition_response(query)
    if symptom_definition:
        return symptom_definition

    disease_symptoms = _disease_symptoms_response(query)
    if disease_symptoms:
        return disease_symptoms

    disease_info = _disease_general_info_response(query)
    if disease_info:
        return disease_info

    disease_topic = _disease_topic_response(query)
    if disease_topic:
        return disease_topic

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
        weak_note = _get_weak_topic_note(query)
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
                f"{weak_note}"
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
