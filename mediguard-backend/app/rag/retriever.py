"""
MediGuard RAG pipeline.

Uses Pinecone + OpenAI when configured, and falls back to local curated
medical reference chunks so the backend remains usable before Pinecone ingest.
"""

import json
import math
import os
import re
import time
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv

from app.data import DISEASES, SYMPTOM_DESCRIPTIONS, SYMPTOMS
from app.data_firstaid import (
    FIRST_AID_DATA,
    detect_first_aid_type,
    format_first_aid_response,
    is_first_aid_request,
)
from app.db.models import Disease
from app.db.session import SessionLocal
from app.ml.fuzzy_match import normalize_symptom_text
from app.ml.predictor import DiseasePredictor
from app.rag.embeddings import embed_text

load_dotenv()

# Plain-language aliases for clinical disease names used in chat responses
DISEASE_COMMON_NAMES: dict[str, str] = {
    "Helicobacteriosis PepticUlcer": "Stomach Ulcer",
    "Onchocerciasis":                "River Blindness",
    "Filariasis":                    "Elephantiasis",
    "Cystitis UTI":                  "Bladder / Urinary Infection",
    "HIV AIDS":                      "HIV/AIDS",
    "Benign Prostatic Hyperplasia":  "Enlarged Prostate",
    "Septicemia":                    "Blood Poisoning",
    "Herpes Zoster":                 "Shingles",
    "Leptospirosis":                 "Weil's Disease",
    "Brucellosis":                   "Undulant Fever",
    "Iron Deficiency Anemia":        "Low Blood / Anaemia",
    "Pelvic Inflammatory Disease":   "Pelvic Infection (PID)",
    "Sickle Cell Crisis":            "Sickle Cell Disease Crisis",
    "Whooping Cough":                "Pertussis",
    "Diabetes Mellitus":             "Diabetes / High Blood Sugar",
    "Hypertension":                  "High Blood Pressure",
    "Dengue Fever":                  "Breakbone Fever",
    "Conjunctivitis":                "Pink Eye",
    "Appendicitis":                  "Inflamed Appendix",
    "Typhus":                        "Rickettsial Fever",
    "Gastroenteritis":               "Stomach Bug / Food Poisoning",
    "Anaphylaxis":                   "Severe Allergic Reaction",
    "Diphtheria":                    "Throat Membrane Infection",
    "Rubella":                       "German Measles",
    "Mumps":                         "Swollen Jaw Glands",
    "Tonsillitis":                   "Inflamed Tonsils",
    "Sinusitis":                     "Sinus Infection",
    "Ringworm":                      "Fungal Ring Rash",
    "Dysentery":                     "Bloody Diarrhoea",
    "Skin Abscess":                  "Skin Boil",
    "Skin Fungal Infection":         "Fungal Skin Rash",
    "Ear Infection":                 "Middle Ear Infection",
    "Kidney Stones":                 "Kidney Gravel",
    "Meningitis":                    "Brain Lining Infection",
    "Typhoid Fever":                 "Enteric Fever",
    "Yellow Fever":                  "Yellow Jack",
    "Epilepsy":                      "Seizure Disorder",
    "Migraine":                      "Severe One-Sided Headache",
    # STIs
    "Gonorrhea":                     "The Clap",
    "Syphilis":                      "The Pox",
    "Chlamydia":                     "Silent STI",
    "Genital Herpes":                "Herpes (HSV-2)",
    "Trichomoniasis":                "Trich",
}


def _disease_display_name(name: str) -> str:
    """Return 'Official Name (Common Name)' or just 'Official Name' if no alias."""
    common = DISEASE_COMMON_NAMES.get(name)
    return f"{name} ({common})" if common else name


DISCLAIMER = (
    "This information is from MediGuard's curated medical references and is "
    "provided for educational purposes only. It is not a substitute for "
    "professional medical advice, diagnosis, or treatment. MediGuard's automated "
    "results can sometimes be incomplete or faulty, so always consult a qualified "
    "healthcare professional for any health concerns."
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

# ---------------------------------------------------------------------------
# Pregnancy-symptom detection for users who may not know they are pregnant
# ---------------------------------------------------------------------------

# Phrases that are *strong single-indicator* signals of possible pregnancy.
# Even one match is enough to trigger the suggestion (for users who say
# "missed period" or "morning sickness" without using the word "pregnant").
_PREGNANCY_STRONG_INDICATORS: frozenset[str] = frozenset({
    "missed period", "missed my period", "late period", "my period is late",
    "period is late", "no period", "haven't had my period", "haven't gotten my period",
    "delayed period", "period stopped", "no menstruation", "missed menstruation",
    "skipped period", "period hasn't come",
    "morning sickness", "nausea in the morning", "vomiting in the morning",
    "sick every morning", "throwing up every morning",
    "sore breasts", "tender breasts", "breast tenderness", "breasts are sore",
    "breasts are tender", "breast soreness", "my breasts hurt",
    "nipple tenderness", "nipples are sore", "nipple pain",
    "implantation bleeding",
    "think i might be pregnant", "could i be pregnant", "am i pregnant",
    "might be pregnant", "possibly pregnant",
    "pregnancy test", "home pregnancy test", "positive test",
    "deux lignes sur le test", "test positif",  # French
    "règles en retard", "pas de règles", "absence de règles",
})

# Additional pregnancy-related phrases: 2+ of these together also trigger
_PREGNANCY_SOFT_SYMPTOMS: list[str] = [
    "nausea", "nauseous", "feeling sick",
    "fatigue", "tired all the time", "extreme tiredness",
    "frequent urination", "urinating a lot", "peeing a lot",
    "pee frequently", "always need to urinate", "urinating frequently",
    "food cravings", "craving food", "craving",
    "food aversion", "food makes me sick", "smell makes me nauseous",
    "bloating", "swollen abdomen",
    "mood swings", "emotional", "crying for no reason",
    "dizziness", "lightheaded",
    "lower back pain",
    "metallic taste", "taste in my mouth",
]


def _has_unaware_pregnancy_symptoms(query: str) -> bool:
    """Return True when query contains symptoms that could signal pregnancy
    in someone who does not yet know they are pregnant.

    Triggers on:
    - any single *strong indicator* (missed period, morning sickness, etc.), OR
    - 2 or more *soft symptoms* together.

    Only skips when the user assertively states they ARE already pregnant
    (e.g. "I am pregnant") — not when they are merely asking ("could I be pregnant?").
    """
    text = query.lower()
    # Skip only when the user clearly asserts they are already pregnant —
    # let the existing pregnancy-followup pathway handle those.
    _ALREADY_PREGNANT_PHRASES = {
        "i am pregnant", "i'm pregnant", "im pregnant",
        "i am expecting", "i'm expecting",
        "antenatal", "prenatal", "trimester",
        "je suis enceinte", "enceinte de",   # French
    }
    if any(phrase in text for phrase in _ALREADY_PREGNANT_PHRASES):
        return False
    # A single strong indicator is enough
    for indicator in _PREGNANCY_STRONG_INDICATORS:
        if indicator in text:
            return True
    # Two or more soft symptoms together
    soft_hits = sum(1 for s in _PREGNANCY_SOFT_SYMPTOMS if s in text)
    return soft_hits >= 2


def _unaware_pregnancy_response(query: str, gender: str | None) -> dict | None:
    """Suggest possible pregnancy when symptoms match, asking for gender to confirm.

    Returns None when:
    - Symptoms don't match pregnancy pattern
    - Gender is already confirmed as male
    """
    if not _has_unaware_pregnancy_symptoms(query):
        return None

    # If we already know the user is male, skip the suggestion entirely
    _MALE_TERMS = {"male", "man", "boy", "homme", "garçon"}
    if gender and gender.lower().strip() in _MALE_TERMS:
        return None

    # Ask for gender if not yet provided or ambiguous
    gender_question = ""
    _FEMALE_TERMS = {"female", "woman", "girl", "femme", "fille"}
    if not gender or gender.lower().strip() not in _FEMALE_TERMS:
        gender_question = (
            "\n\n**To give you more accurate advice**, could you also tell me your gender? "
            "*(Reply: female / male — this helps me personalise the guidance)*"
        )

    answer = (
        "🤰 **These Symptoms Could Be Early Signs of Pregnancy**\n\n"
        "The symptoms you've described — such as a missed/late period, breast tenderness, "
        "morning nausea, fatigue, or frequent urination — are among the **most common early "
        "signs of pregnancy**. It's possible you may be pregnant without yet knowing.\n\n"
        "**What you can do right now:**\n"
        "1. 💊 Take a **home pregnancy test** (available at pharmacies) — it can detect "
        "pregnancy as early as the first day of a missed period.\n"
        "2. 🏥 Visit a **health clinic or maternity unit** for a confirmed blood (HCG) test.\n"
        "3. ✅ If the test is positive, **start antenatal care early** — early check-ups "
        "protect both mother and baby.\n\n"
        "⚠️ *These symptoms can also have other causes (hormonal changes, stress, illness, "
        "or anaemia). A pregnancy test is the fastest and most reliable way to find out.*"
        f"{gender_question}"
    )

    follow_up = [
        "What is your gender?",
        "Have you taken a pregnancy test?",
        "When did you last have your period?",
    ] if gender_question else [
        "Have you taken a pregnancy test?",
        "When did you last have your period?",
    ]

    return {
        "answer": answer,
        "sources": ["MediGuard Reproductive Health Guidelines"],
        "disclaimer": (
            "This is educational guidance only. Only a clinical pregnancy test can confirm "
            "pregnancy. Consult a qualified healthcare professional for personal health concerns."
        ),
        "mode": "pregnancy_suggestion",
        "follow_up_questions": follow_up,
    }

FATIGUE_CONTEXT_TERMS = [
    "fatigue",
    "tired",
    "tiredness",
    "weak",
    "weakness",
    "poor sleep",
    "lack of sleep",
    "lack sleep",
    "not sleeping",
    "sleep deprived",
    "stress",
    "stressed",
    "stressful",
    "overworked",
    "overwork",
    "exhausted",
    "exhaustion",
    "burned out",
    "burnout",
    "burnt out",
    "anxious",
    "anxiety",
    "exam pressure",
    "exam stress",
    "workload",
    "too much work",
    "long hours",
    "no rest",
    "dehydrated",
    "dehydration",
    "heavy work",
    "skipped meals",
    "missed meals",
    "not eating",
    "no appetite",
]

# Symptoms that are typical of a non-specific stress / fatigue presentation.
# If most of the user's reported symptoms fall in this set, we add a note that
# lifestyle factors may be contributing — but we still show predictions.
_STRESS_TYPICAL_SYMPTOMS: frozenset[str] = frozenset({
    "fatigue", "tiredness", "tired", "weakness", "weak",
    "headache", "mild headache", "tension headache",
    "dizziness", "lightheadedness",
    "nausea", "mild nausea",
    "muscle aches", "body aches", "body pain", "muscle pain",
    "mild fever", "low-grade fever", "low grade fever",
    "loss of appetite", "poor appetite",
    "difficulty concentrating", "brain fog", "poor focus",
    "irritability", "mood swings",
    "insomnia", "poor sleep",
    "palpitations", "heart racing",
    "shortness of breath", "shallow breathing",
})

REFERENCE_CHUNKS_FILE = Path(__file__).resolve().parents[2] / "data_pipeline" / "mediguard_reference_chunks.json"

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
    # French greetings
    r"^\s*(bonjour|salut|bonsoir|bonne\s+nuit|allÃ´)\s*[!.?]*\s*$",
    r"^\s*comment\s+(allez.vous|vas.tu|Ã§a\s+va)\s*[?.!]*\s*$",
    r"^\s*(pouvez.vous|peux.tu)\s+m['']aider\s*[?.!]*\s*$",
]

THANKS_PATTERNS = [
    r"^\s*(thanks|thank you|thank u|appreciate it|much appreciated)\s*[!.?]*\s*$",
    r"^\s*(thanks|thank you)\s+(a lot|so much|very much)\s*[!.?]*\s*$",
    # French thanks
    r"^\s*(merci|merci\s+beaucoup|je\s+vous\s+remercie|c['']est\s+bien)\s*[!.?]*\s*$",
]

# French detection â€” uses accented chars (never in English) + unambiguous French words
_FRENCH_STRONG = [
    # Accented characters â€” near-certain French indicator
    "Ã ", "Ã¢", "Ã©", "Ã¨", "Ãª", "Ã«", "Ã®", "Ã¯", "Ã´", "Ã¹", "Ã»", "Ã¼", "Ã§", "Å“", "Ã¦",
    # Unambiguous French words / phrases (not found in English)
    "bonjour", "bonsoir", "salut", "merci", "s'il vous plaÃ®t", "s'il te plaÃ®t",
    "qu'est-ce", "c'est", "est-ce", "qu'il", "n'est", "je suis", "je vais",
    "je voudrais", "je veux", "je peux", "je dois", "je ne ",
    "vous avez", "vous Ãªtes", "vous pouvez", "nous avons",
    "quel symptÃ´me", "quels symptÃ´mes", "quels sont", "quelles sont",
    "pourquoi ", "voudrais", "voudrait", "pouvez-vous",
    "maladie", "maladies", "fiÃ¨vre", "douleur", "douleurs", "traitement",
    "prÃ©vention", "paludisme", "mÃ©decin", "hÃ´pital", "santÃ©", "symptÃ´me",
    "symptÃ´mes", "guÃ©rir", "prÃ©venir", "contagieux",
    "comment soigner", "comment traiter", "comment prÃ©venir",
    "qu'est ce que", "qu est-ce",
]


def _is_french(query: str) -> bool:
    text = query.lower()
    return any(w in text for w in _FRENCH_STRONG)


SYMPTOM_DEFINITIONS: dict[str, str] = {
    "fever": (
        "A fever is a temporary rise in body temperature above the normal range of 36â€“37.5Â°C (97â€“99.5Â°F), "
        "usually above 38Â°C (100.4Â°F). It is the body's natural defence response â€” an elevated temperature "
        "makes the environment less hospitable for many bacteria and viruses. Fever often comes with chills, "
        "sweating, headache, muscle aches, and loss of appetite. Prolonged or very high fever (above 40Â°C/104Â°F) "
        "needs prompt medical attention."
    ),
    "rash": (
        "A rash is any change in the skin's colour, texture, or appearance â€” it may be flat (macular), "
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
        "Repeated vomiting leads to dehydration and electrolyte imbalance â€” warning signs include no urination "
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
        "reactions. Sudden severe breathlessness â€” especially with chest pain, blue lips, or rapid heartbeat â€” "
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
        "Unintentional weight loss is losing body weight without trying â€” generally more than 5% of body "
        "weight over 6â€“12 months. It can be caused by infections (tuberculosis, HIV), cancer, diabetes, "
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
        "A runny nose (rhinorrhea) is excess nasal discharge â€” it can be clear, white, yellow, or green. "
        "Clear discharge often indicates a viral infection or allergy; thick coloured discharge may suggest "
        "a bacterial secondary infection. Runny nose combined with body aches and fever typically points to "
        "influenza rather than a simple cold."
    ),
    "skin lesion": (
        "A skin lesion is any abnormal area of skin â€” it can be a sore, ulcer, blister, spot, or growth. "
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
        "the blood. It indicates that the liver is not processing bilirubin normally â€” due to liver disease "
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
    # French disease names
    "paludisme": "Malaria",
    "fiÃ¨vre typhoÃ¯de": "Typhoid Fever", "typhoÃ¯de": "Typhoid Fever",
    "cholÃ©ra": "Cholera",
    "pneumonie": "Pneumonia",
    "tuberculose": "Tuberculosis",
    "mÃ©ningite": "Meningitis",
    "dengue": "Dengue Fever",
    "varicelle": "Chickenpox",
    "rougeole": "Measles",
    "hÃ©patite a": "Hepatitis A", "hÃ©patite b": "Hepatitis B",
    "fiÃ¨vre jaune": "Yellow Fever",
    "coqueluche": "Whooping Cough",
    "oreillons": "Mumps",
    "rubÃ©ole": "Rubella",
    "sinusite": "Sinusitis",
    "angine": "Tonsillitis",
    "otite": "Ear Infection",
    "conjonctivite": "Conjunctivitis",
    "zona": "Herpes Zoster",
    "appendicite": "Appendicitis",
    "diabÃ¨te": "Diabetes Mellitus",
    "hypertension": "Hypertension",
    "anÃ©mie": "Iron Deficiency Anemia",
    "paludisme cÃ©rÃ©bral": "Malaria",
    "grippe": "Common Cold",
    "asthme": "Asthma",
    "Ã©pilepsie": "Epilepsy",
    "migraine": "Migraine",
    "gonorrhÃ©e": "Gonorrhea", "blennorragie": "Gonorrhea",
    "syphilis": "Syphilis",
    "chlamydia": "Chlamydia",
    "herpÃ¨s gÃ©nital": "Genital Herpes",
    "trichomonase": "Trichomoniasis",
    # STIs
    "gonorrhea": "Gonorrhea", "gonorrhoea": "Gonorrhea", "gonorhea": "Gonorrhea",
    "gonorea": "Gonorrhea", "gonnorhea": "Gonorrhea", "gonorrea": "Gonorrhea",
    "gonnorrea": "Gonorrhea", "gonorrhe": "Gonorrhea", "gonorrhoe": "Gonorrhea",
    "the clap": "Gonorrhea", "clap": "Gonorrhea",
    "the pox": "Syphilis", "syph": "Syphilis", "ciphilis": "Syphilis",
    "siphilis": "Syphilis", "syfilis": "Syphilis", "sifilis": "Syphilis",
    "syphillis": "Syphilis", "syphylis": "Syphilis", "sifilis": "Syphilis",
    "silent sti": "Chlamydia", "clamydia": "Chlamydia", "chlamidia": "Chlamydia",
    "genital herpes": "Genital Herpes", "herpes": "Genital Herpes", "hsv": "Genital Herpes",
    "trich": "Trichomoniasis", "trichomonas": "Trichomoniasis", "trichomoniasis": "Trichomoniasis",
    "trichonomiasis": "Trichomoniasis",
    # Others
    "maleria": "Malaria", "malaira": "Malaria", "malarya": "Malaria", "mallaria": "Malaria",
    "typhoid": "Typhoid Fever", "typhiod": "Typhoid Fever", "typoid": "Typhoid Fever",
    "dengue": "Dengue Fever", "denge": "Dengue Fever",
    "cholera": "Cholera", "colera": "Cholera",
    "pneumonia": "Pneumonia", "pnemonia": "Pneumonia", "pnumonia": "Pneumonia",
    "tuberculosis": "Tuberculosis", "tuberculoses": "Tuberculosis",
    "tuberclosis": "Tuberculosis", "tubercolosis": "Tuberculosis",
    "meningitis": "Meningitis", "menigitis": "Meningitis",
    "measles": "Measles", "measels": "Measles",
    "chickenpox": "Chickenpox", "chikenpox": "Chickenpox", "chiken pox": "Chickenpox",
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

MEDICAL_TYPO_REPLACEMENTS: dict[str, str] = {
    "diarhea": "diarrhea",
    "diarrhoea": "diarrhea",
    "diarhoea": "diarrhea",
    "diahrea": "diarrhea",
    "diahorrhea": "diarrhea",
    "stomack pain": "stomach pain",
    "stomac pain": "stomach pain",
    "abdomnal pain": "abdominal pain",
    "headace": "headache",
    "head ache": "headache",
    "hedache": "headache",
    "feaver": "fever",
    "fiver": "fever",
    "tempreture": "temperature",
    "temprature": "temperature",
    "nauseous": "nausea",
    "nausious": "nausea",
    "nausia": "nausea",
    "vommiting": "vomiting",
    "vomitting": "vomiting",
    "vommitting": "vomiting",
    "caugh": "cough",
    "coff": "cough",
    "troat pain": "sore throat",
    "sore troat": "sore throat",
    "sweating": "sweating",
    "sweatting": "sweating",
    "dizzyness": "dizziness",
    "diziness": "dizziness",
    "breathless": "shortness of breath",
    "breathing problem": "shortness of breath",
    "chestpain": "chest pain",
}

# Build lookup by canonical name for fast access
_DISEASE_BY_NAME: dict[str, dict] = {d["name"]: d for d in DISEASES}


def _normalize_medical_term(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _correct_common_medical_typos(text: str) -> str:
    corrected = f" {text.lower()} "
    for typo, replacement in sorted(MEDICAL_TYPO_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        corrected = re.sub(rf"(?<![a-z]){re.escape(typo)}(?![a-z])", replacement, corrected)
    return re.sub(r"\s+", " ", corrected).strip()


def _strip_short_question_noise(query: str) -> str:
    text = _correct_common_medical_typos(query)
    text = re.sub(r"^[\s?.!,]*(what'?s|whats|what is|tell me|about|define|explain)\s+", "", text)
    text = re.sub(r"[\s?.!,]+$", "", text)
    return text.strip()


def _fuzzy_disease_match(term: str, threshold: float = 0.78) -> dict | None:
    normalized = _normalize_medical_term(term)
    compact = normalized.replace(" ", "")
    if len(compact) < 4:
        return None

    best_score = 0.0
    best_name: str | None = None
    candidates: list[tuple[str, str]] = []
    for disease in DISEASES:
        candidates.extend([
            (disease["name"], disease["name"]),
            (disease["slug"].replace("-", " "), disease["name"]),
        ])
    candidates.extend((alias, canonical) for alias, canonical in DISEASE_ALIASES.items())

    for candidate, canonical in candidates:
        candidate_norm = _normalize_medical_term(candidate)
        candidate_compact = candidate_norm.replace(" ", "")
        if not candidate_compact:
            continue
        score = max(
            SequenceMatcher(None, compact, candidate_compact).ratio(),
            SequenceMatcher(None, normalized, candidate_norm).ratio(),
        )
        if score > best_score:
            best_score = score
            best_name = canonical

    if best_name and best_score >= threshold:
        return _DISEASE_BY_NAME.get(best_name)
    return None

DISEASE_SYMPTOM_QUERY_PATTERNS = [
    re.compile(r"^\s*symptoms\s+of\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*signs\s+of\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*what\s+are\s+(?:the\s+)?symptoms?\s+(?:of|for)\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*what\s+are\s+(?:the\s+)?signs?\s+(?:of|for)\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(.+?)\s+symptoms\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*how\s+does\s+(.+?)\s+(?:present|manifest|show|appear)\s*[?.!]*\s*$", re.I),
    # French patterns
    re.compile(r"^\s*sympt[oÃ´]mes?\s+du?\s+(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*sympt[oÃ´]mes?\s+de\s+(?:la\s+|l[e']?\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*quels?\s+sont\s+(?:les\s+)?sympt[oÃ´]mes?\s+(?:du?|de|d[e'])\s+(?:la\s+|l[e']?\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(.+?)\s+sympt[oÃ´]mes?\s*[?.!]*\s*$", re.I),
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
            return _strip_short_question_noise(match.group(1))
    short_term = _strip_short_question_noise(query)
    if re.search(r"\b(and|with|plus|also)\b|[,/&+]", short_term):
        return None
    if 1 <= len(short_term.split()) <= 3 and _resolve_symptom_definition_term(short_term):
        return short_term
    return None


def _resolve_symptom_definition_term(term: str) -> str | None:
    term = _strip_short_question_noise(term)
    if not term:
        return None
    if term in SYMPTOM_DEFINITIONS:
        return term

    for key in SYMPTOM_DEFINITIONS:
        if key in term or term in key:
            return key

    normalized_symptoms = {
        symptom.lower().replace("_", " "): symptom.lower().replace("_", " ")
        for symptom in SYMPTOMS
    }
    candidates = list(SYMPTOM_DEFINITIONS) + list(normalized_symptoms)
    best = max(
        candidates,
        key=lambda candidate: SequenceMatcher(None, term, candidate).ratio(),
        default=None,
    )
    if best and SequenceMatcher(None, term, best).ratio() >= 0.76:
        if best in SYMPTOM_DEFINITIONS:
            return best
        for definition_key in SYMPTOM_DEFINITIONS:
            if definition_key in best or best in definition_key:
                return definition_key
    return None


def _symptom_definition_response(query: str) -> dict | None:
    term = _extract_symptom_term(query)
    if not term:
        return None

    # Check for an exact or near match in our definitions table
    resolved_term = _resolve_symptom_definition_term(term)
    if not resolved_term:
        return None
    term = resolved_term
    definition = SYMPTOM_DEFINITIONS.get(term)
    if not definition:
        # Try substring match (e.g. "high fever" â†’ "fever")
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
                disease_examples.append(f"**{disease_name}**: {sym_desc}")
                break
    disease_examples = disease_examples[:5]

    answer_parts = [definition]
    if disease_examples:
        answer_parts.append(
            f"\n\nHow **{term}** specifically appears in different diseases:"
        )
        answer_parts.extend(
            f"{index}. {example}"
            for index, example in enumerate(disease_examples, start=1)
        )
    answer_parts.append(
        "\n\nIf you are experiencing this symptom yourself, describe it to a qualified healthcare "
        "professional or use the MediGuard Symptom Checker for a guided assessment."
    )

    return {
        "answer": "\n".join(answer_parts),
        "sources": list({name for name, desc_map in SYMPTOM_DESCRIPTIONS.items()
                         for sym_key in desc_map if term in sym_key.lower() or sym_key.lower() in term})[:4],
        "disclaimer": DISCLAIMER,
        "mode": "symptom_definition",
    }


def _resolve_disease_name(term: str) -> dict | None:
    """Return a DISEASES entry for a user-supplied term, using aliases and fuzzy matching."""
    term = _normalize_medical_term(_strip_short_question_noise(term))
    if len(term.replace(" ", "")) < 4:
        return None
    # 1. Alias lookup (longest-key-first to avoid partial hits)
    for alias in sorted(DISEASE_ALIASES, key=len, reverse=True):
        normalized_alias = _normalize_medical_term(alias)
        exact_or_contained = normalized_alias in term
        contained_in_alias = len(term) >= 4 and term in normalized_alias
        if exact_or_contained or contained_in_alias:
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
    fuzzy = _fuzzy_disease_match(term, threshold=0.74)
    if fuzzy:
        return fuzzy
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
        if re.search(r"\bsymptom", text) or "symptÃ´me" in text or re.search(r"\bsign(s)?\b", text) or re.search(r"\bpresent", text):
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
    lines = [f"**{_disease_display_name(disease['name'])}** commonly presents with these symptoms:\n"]
    for index, sym in enumerate(symptoms, start=1):
        sym_lower = sym.lower().replace("_", " ")
        desc = next(
            (val for key, val in desc_map.items()
             if key.lower() == sym_lower or key.lower() in sym_lower or sym_lower in key.lower()),
            None,
        )
        if desc:
            lines.append(f"{index}. **{sym.replace('_', ' ')}**: {desc}")
        else:
            lines.append(f"{index}. {sym.replace('_', ' ')}")

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
    # French patterns
    re.compile(r"^\s*qu[''e]est.ce\s+que\s+(?:le\s+|la\s+|l[e']?\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(?:c[''e]est\s+quoi|keski|kÃ©sako)\s+(?:le\s+|la\s+|l[e']?\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(?:expliquez?|dÃ©crivez?|parlez.moi\s+de)\s+(?:le\s+|la\s+|l[e']?\s+)?(.+?)\s*[?.!]*\s*$", re.I),
    re.compile(r"^\s*(?:qu[''e]est.ce\s+que\s+c[''e]est|dÃ©finissez?)\s+(?:le\s+|la\s+|l[e']?\s+)?(.+?)\s*[?.!]*\s*$", re.I),
]

# Terms that indicate other, more specific handlers should handle it
_GENERAL_SKIP_TERMS = {
    "symptom", "sign of", "prevent", "prevention", "treatment", "treat",
    "cure", "cause", "causes", "spread", "how do i", "how can i",
    "lab", "laboratory", "test", "testing", "diagnosis", "diagnostic",
    "screen", "screening", "specimen", "culture", "smear",
}


def _disease_general_info_response(query: str) -> dict | None:
    """Handle 'what is malaria', 'tell me about typhoid', etc. directly from the database."""
    text = _correct_common_medical_typos(query)
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

    # If no pattern matched, only proceed if the query is short (â‰¤5 words) and contains a disease name
    if not candidate:
        if len(query.split()) > 5:
            return None
        candidate = _strip_short_question_noise(query)
    else:
        candidate = _strip_short_question_noise(candidate)

    disease = _resolve_disease_name(candidate)
    if not disease:
        disease = _detect_disease(query)
    if not disease:
        return None

    profile = _pinecone_disease_profile(disease["name"])
    if profile:
        data_source = "pinecone"
    else:
        profile = _database_disease_profile(disease["name"])
        if not profile:
            return None
        # "database" → SQLite/Postgres diseases table; "curated" → built-in DISEASES list
        data_source = profile.get("source", "local_db")

    symptoms = disease.get("symptoms") or []
    display = _disease_display_name(disease["name"])
    lines = [f"**{display}**\n"]
    if candidate and _normalize_medical_term(candidate) != _normalize_medical_term(disease["name"]):
        lines.append(f"You may mean **{display}**.")

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
        "data_source": data_source,
        "mode": "disease_definition",
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
    except Exception:
        pass
    finally:
        try:
            db.close()
        except Exception:
            pass
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
    if profile:
        data_source = "pinecone"
    else:
        profile = _database_disease_profile(disease["name"])
        if not profile:
            return None
        # "database" → SQLite/Postgres diseases table; "curated" → built-in DISEASES list
        data_source = profile.get("source", "local_db")

    name = profile.get("disease") or disease["name"]
    display_name = _disease_display_name(name)
    if intent == "prevention":
        prevention = profile.get("prevention") or disease.get("prevention") or []
        if isinstance(prevention, str):
            prevention = [item.strip() for item in re.split(r"[;\n]", prevention) if item.strip()]
        lines = [f"To help prevent **{display_name}**:"]
        if prevention:
            lines.extend(f"- {item}" for item in prevention[:6])
        elif profile.get("description"):
            lines.append(profile["description"])
        lines.append("Seek testing or clinical care early if symptoms appear, especially fever, weakness, vomiting, confusion, breathing difficulty, dehydration, or pregnancy warning signs.")
    elif intent == "treatment":
        treatment = profile.get("treatment") or disease.get("treatment") or ""
        lines = [f"Treatment overview for **{display_name}**:", treatment or "A qualified clinician should assess symptoms and choose appropriate care."]
        lines.append("Do not start prescription medicines without a qualified clinician. Seek urgent care for severe or worsening symptoms.")
    else:
        causes = profile.get("causes") or disease.get("causes") or ""
        lines = [f"Common causes or spread of **{display_name}**:", causes or profile.get("description") or "The exact cause depends on the condition and exposure history."]
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


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lng / 2) ** 2
    )
    return earth_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _facility_type_from_tags(tags: dict) -> str:
    healthcare = (tags.get("healthcare") or "").lower()
    amenity = (tags.get("amenity") or "").lower()
    if healthcare == "hospital" or amenity == "hospital":
        return "Hospital"
    if healthcare == "clinic" or amenity == "clinic":
        return "Clinic"
    if healthcare in {"doctor", "doctors"} or amenity == "doctors":
        return "Doctors / Medical Practice"
    return "Health Facility"


def _address_from_tags(tags: dict) -> str:
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:state"),
        tags.get("addr:country"),
    ]
    parts = [part for part in parts if part]
    return ", ".join(parts) if parts else tags.get("address") or "Address not listed on map"


def _fetch_map_facilities(user_lat: float, user_lng: float, radius: int = 15000, limit: int = 5) -> list[dict]:
    overpass_query = f"""
    [out:json][timeout:20];
    (
      node(around:{radius},{user_lat},{user_lng})["amenity"~"hospital|clinic|doctors"];
      way(around:{radius},{user_lat},{user_lng})["amenity"~"hospital|clinic|doctors"];
      relation(around:{radius},{user_lat},{user_lng})["amenity"~"hospital|clinic|doctors"];
      node(around:{radius},{user_lat},{user_lng})["healthcare"~"hospital|clinic|doctor|doctors"];
      way(around:{radius},{user_lat},{user_lng})["healthcare"~"hospital|clinic|doctor|doctors"];
      relation(around:{radius},{user_lat},{user_lng})["healthcare"~"hospital|clinic|doctor|doctors"];
    );
    out center tags {limit * 4};
    """
    request = Request(
        "https://overpass-api.de/api/interpreter",
        data=urlencode({"data": overpass_query}).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8", "User-Agent": "MediGuard/1.0"},
        method="POST",
    )
    with urlopen(request, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))

    seen: set[str] = set()
    facilities: list[dict] = []
    for element in payload.get("elements", []):
        tags = element.get("tags") or {}
        facility_lat = element.get("lat") or (element.get("center") or {}).get("lat")
        facility_lng = element.get("lon") or (element.get("center") or {}).get("lon")
        name = tags.get("name") or tags.get("operator")
        if not facility_lat or not facility_lng or not name:
            continue
        facility_type = _facility_type_from_tags(tags)
        if facility_type not in {"Hospital", "Clinic", "Doctors / Medical Practice"}:
            continue
        dedupe_key = f"{name.lower()}-{float(facility_lat):.4f}-{float(facility_lng):.4f}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        facilities.append({
            "name": name,
            "type": facility_type,
            "address": _address_from_tags(tags),
            "phone": tags.get("phone") or tags.get("contact:phone") or tags.get("mobile") or "Phone not listed on map",
            "hours": tags.get("opening_hours") or "Hours not listed on map",
            "lat": float(facility_lat),
            "lng": float(facility_lng),
            "distance_km": _distance_km(user_lat, user_lng, float(facility_lat), float(facility_lng)),
            "source_url": f"https://www.openstreetmap.org/{element.get('type')}/{element.get('id')}",
        })

    return sorted(facilities, key=lambda item: item["distance_km"])[:limit]


FACILITY_TERMS = [
    "hospital", "clinic", "health facility", "health centre", "health center",
    "nearest hospital", "nearby hospital", "where to go", "where can i go",
    "where should i go", "seek care", "get treatment", "see a doctor",
    "go to hospital", "find a hospital", "find a clinic", "medical facility",
    "doctor near", "pharmacy near",
]


TREND_TERMS = [
    "trending", "trend", "outbreak", "most common disease", "common disease",
    "disease this week", "disease statistics", "health statistics",
    "current diseases", "which disease is common", "disease report",
    "disease situation", "disease surge", "disease in bamenda",
    "cases", "how many cases",
]


def _trends_response(query: str) -> dict | None:
    text = query.lower()
    if not any(term in text for term in TREND_TERMS):
        return None
    try:
        from sqlalchemy import func
        from app.db.models import PredictionLog
        db = SessionLocal()
        try:
            total = db.query(func.count(PredictionLog.id)).scalar() or 0
            rows = (
                db.query(PredictionLog.top_disease, func.count(PredictionLog.id).label("cnt"))
                .filter(PredictionLog.top_disease.isnot(None))
                .group_by(PredictionLog.top_disease)
                .order_by(func.count(PredictionLog.id).desc())
                .limit(5)
                .all()
            )
        finally:
            db.close()

        if not rows or total == 0:
            return {
                "answer": (
                    "No screening data has been recorded yet in MediGuard. "
                    "Once users complete health screenings, disease trend data will appear here and on the **Trends Dashboard**.\n\n"
                    "You can visit **/trends** in MediGuard to see live community disease statistics."
                ),
                "sources": [],
                "disclaimer": DISCLAIMER,
                "data_source": "prediction_log",
            }

        lines = [f"**MediGuard Community Disease Trends â€” Bamenda** (based on {total} screening{'s' if total != 1 else ''}):\n"]
        for i, (disease, count) in enumerate(rows, 1):
            pct = round((count / total) * 100)
            lines.append(f"{i}. **{disease}** â€” {count} case{'s' if count != 1 else ''} ({pct}%)")

        lines.append(
            "\nThese figures reflect symptom screenings submitted through MediGuard, not confirmed diagnoses. "
            "Visit the **Trends Dashboard** at /trends for charts, outbreak alerts, and weekly breakdown."
        )
        return {
            "answer": "\n".join(lines),
            "sources": [r[0] for r in rows[:3] if r[0]],
            "disclaimer": DISCLAIMER,
            "data_source": "database_trends",
        }
    except Exception:
        return None


def _facilities_response(query: str, user_lat: float | None = None, user_lng: float | None = None) -> dict | None:
    text = query.lower()
    if not any(term in text for term in FACILITY_TERMS):
        return None

    has_location = user_lat is not None and user_lng is not None
    if not has_location:
        return {
            "answer": (
                "I need your current location to choose the nearest hospital from the map. "
                "Please allow location access in your browser, then ask again or open **/nearby-facilities** and tap **Use my location**. "
                "For an emergency, go to the closest open hospital you already know or call local emergency support immediately."
            ),
            "sources": ["OpenStreetMap / Overpass"],
            "disclaimer": DISCLAIMER,
            "mode": "facilities",
            "data_source": "location_required",
        }

    try:
        facilities = _fetch_map_facilities(float(user_lat), float(user_lng), limit=5)
    except Exception:
        facilities = []

    if not facilities:
        return {
            "answer": (
                "I could not fetch live nearby hospitals from the map right now. "
                "Open **/nearby-facilities** in MediGuard and tap **Use my location** to retry with the embedded map. "
                "For an emergency, go to the closest open hospital or call local emergency support immediately."
            ),
            "sources": ["OpenStreetMap / Overpass"],
            "disclaimer": DISCLAIMER,
            "mode": "facilities",
            "data_source": "map_unavailable",
        }

    lines = ["**Nearest mapped health facilities from your location**\n"]

    for index, f in enumerate(facilities, start=1):
        destination = f"{f['lat']},{f['lng']}"
        dir_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={user_lat},{user_lng}"
            f"&destination={destination}"
        )
        distance_label = f"{round(f['distance_km'] * 1000)} m" if f["distance_km"] < 1 else f"{f['distance_km']:.1f} km"
        lines.append(
            f"{index}. **{f['name']}** ({f['type']}) - {distance_label} away\n"
            f"   Address: {f['address']}\n"
            f"   Phone: {f['phone']}\n"
            f"   Hours: {f['hours']}\n"
            f"   Directions: {dir_url}\n"
            f"   Map source: {f['source_url']}"
        )

    lines.append(
        "\nThese are live OpenStreetMap results sorted by distance from your detected location. "
        "Open **/nearby-facilities** in MediGuard to view them on the embedded map. "
        "For emergencies, go to the nearest open facility immediately."
    )

    return {
        "answer": "\n".join(lines),
        "sources": [f["name"] for f in facilities[:3]],
        "disclaimer": DISCLAIMER,
        "mode": "facilities",
        "data_source": "openstreetmap",
        "facilities": facilities,
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
    french = _is_french(query)

    if not text:
        answer = ("Je suis ici. Posez une question sur les symptÃ´mes, les maladies ou la prÃ©vention."
                  if french else
                  "I am here. Ask me about symptoms, diseases, prevention, or when to seek care.")
        return {"answer": answer, "sources": [], "disclaimer": DISCLAIMER}

    if any(re.match(pattern, text) for pattern in GREETING_PATTERNS):
        if "how are you" in text:
            answer = (
                "Je vais bien, merci. Je peux expliquer les symptÃ´mes, la prÃ©vention et les informations de santÃ© "
                "de la base de donnÃ©es MediGuard. Dites-moi ce que vous souhaitez savoir."
                if french else
                "I am doing well and ready to help. I can explain symptoms, prevention, and general health information "
                "from MediGuard's curated medical references. Tell me what you would like to understand."
            )
        elif "help" in text or "aider" in text or "what can you do" in text or "que pouvez" in text:
            answer = (
                "Oui, je peux vous aider. Vous pouvez poser des questions sur les symptÃ´mes, les maladies courantes Ã  Bamenda, "
                "la prÃ©vention, les traitements, ou quand consulter un mÃ©decin. Je peux aussi vous orienter vers les "
                "Ã©tablissements de santÃ© proches et rÃ©pondre aux questions sur MediGuard."
                if french else
                "Yes, I can help. You can ask about symptoms, common conditions in Bamenda, prevention, treatment overview, "
                "or when to see a doctor. I can also explain your symptom-checker result, point you to nearby facilities, "
                "and answer questions about using MediGuard."
            )
        else:
            answer = (
                "Bonjour, bienvenue sur MediGuard. Je peux vous aider avec des questions de santÃ© sur les symptÃ´mes, "
                "les maladies, la prÃ©vention et quand consulter un professionnel de santÃ©."
                if french else
                "Hello, welcome to MediGuard. I can help with health education questions about symptoms, diseases, "
                "prevention, and when to seek professional care."
            )
        return {"answer": answer, "sources": [], "disclaimer": DISCLAIMER}
    if any(re.match(pattern, text) for pattern in THANKS_PATTERNS):
        answer = (
            "De rien. Je suis disponible chaque fois que vous souhaitez vÃ©rifier des symptÃ´mes, comprendre une maladie ou apprendre des mesures de prÃ©vention."
            if french else
            "You are welcome. I am here whenever you want to check symptoms, understand a condition, "
            "or learn prevention steps from the MediGuard knowledge base."
        )
        return {"answer": answer, "sources": [], "disclaimer": DISCLAIMER}
    return None


def _mentions_pregnancy(query: str) -> bool:
    text = query.lower()
    return any(term in text for term in PREGNANCY_TERMS)


def _mentions_fatigue_context(query: str, symptoms: list[str] | None = None) -> bool:
    text = f"{query.lower()} {' '.join(symptom.lower() for symptom in symptoms or [])}"
    return any(term in text for term in FATIGUE_CONTEXT_TERMS)


def _is_stress_typical_presentation(symptoms: list[str], query: str = "") -> bool:
    """Return True when the user presents with 4 or fewer symptoms AND most of
    them are non-specific symptoms that are commonly caused by stress, fatigue,
    dehydration, or lifestyle factors.

    This never blocks a prediction — it only controls whether we show an
    extra context note so the user knows those factors might be contributing.
    """
    if not symptoms:
        return False
    # Only trigger for short symptom lists (few reported symptoms)
    if len(symptoms) > 4:
        return False
    normalised = {s.lower().strip() for s in symptoms}
    stress_count = sum(1 for s in normalised if s in _STRESS_TYPICAL_SYMPTOMS)
    # 60 % or more of reported symptoms match the stress-typical set
    ratio = stress_count / len(normalised)
    if ratio < 0.60:
        return False
    # Also trigger if the user's message itself mentions a fatigue/stress term
    # even without meeting the ratio threshold (e.g. "I have a headache from stress")
    query_text = query.lower()
    if any(term in query_text for term in FATIGUE_CONTEXT_TERMS):
        return True
    return True


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
    text = _normalize_medical_term(_strip_short_question_noise(query))
    # Alias lookup first (handles "chicken pox" â†’ "Chickenpox" etc.)
    for alias in sorted(DISEASE_ALIASES, key=len, reverse=True):
        normalized_alias = _normalize_medical_term(alias)
        if normalized_alias and re.search(rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])", text):
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
    fuzzy = _fuzzy_disease_match(query, threshold=0.82)
    if fuzzy:
        return fuzzy
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
            f"Common symptoms linked with {_disease_display_name(disease['name'])} include {', '.join(symptoms)}. "
            "Symptoms can vary from person to person, and this is not a diagnosis. "
            "What you can do now: rest, drink fluids, monitor the symptoms, avoid taking prescription medicines without a clinician, "
            "and seek care quickly if symptoms are severe, persistent, or worsening. MediGuard results can sometimes be faulty, "
            "so use this as guidance only."
        ),
        "sources": sources or [disease["name"]],
        "disclaimer": DISCLAIMER,
    }


def _get_predictor(_reload: bool = False) -> DiseasePredictor:
    """Return the shared DiseasePredictor instance.

    Pass ``_reload=True`` after a model file has been updated on disk to force
    the singleton to be rebuilt from the new artefact.
    """
    global _predictor
    if _predictor is None or _reload:
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
    except Exception:
        return predictions
    finally:
        try:
            db.close()
        except Exception:
            pass


def _extract_reported_symptoms(query: str) -> list[str]:
    normalized_query = _correct_common_medical_typos(query)
    text = f" {normalized_query} "
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
    for symptom in normalize_symptom_text(normalized_query, SYMPTOMS):
        if symptom not in matches:
            matches.append(symptom)
    temp_match = re.search(r"\b(3[89]|4[0-5])\s*(?:degrees?|c|°c|celsius)?\b", text)
    if temp_match:
        if "Fever" in SYMPTOMS and "Fever" not in matches:
            matches.append("Fever")
        if "High fever" in SYMPTOMS and "High fever" not in matches:
            matches.append("High fever")
    return matches


def _is_symptom_check_request(query: str, symptoms: list[str]) -> bool:
    text = _correct_common_medical_typos(query)
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
        "i feel",
        "i am feeling",
        "feeling",
        "sick",
        "ill",
    ]
    short_symptom_list = len(text.split()) <= 5 and len(symptoms) >= 2
    return short_symptom_list or len(symptoms) >= 2 or (bool(symptoms) and any(term in text for term in intent_terms))


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
    """
    Generate context-aware follow-up questions that:
    1. Never ask about symptoms the user already reported.
    2. Adapt conditional questions (fever/respiratory/GI) so they only mention
       symptoms that are still unknown, avoiding redundant phrasing like
       "does your fever come with sweating?" when the user already said they have sweating.
    """
    questions = [
        "How long have you had these symptoms?",
        "Are they mild, moderate, or severe?",
    ]

    symptom_set = {s.lower() for s in symptoms}

    # ── "Any other symptoms?" — exclude already-reported ones ────────────────
    # Ordered list of common symptoms to probe; only include ones NOT yet reported.
    _OTHER_POOL: list[tuple[str, str]] = [
        # (lookup key,            display label)
        ("fever",               "fever"),
        ("vomiting",            "vomiting"),
        ("diarrhea",            "diarrhoea"),
        ("chest pain",          "chest pain"),
        ("rash",                "rash"),
        ("dizziness",           "dizziness"),
        ("shortness of breath", "trouble breathing"),
        ("headache",            "headache"),
        ("nausea",              "nausea"),
        ("chills",              "chills"),
        ("sweating",            "sweating"),
        ("fatigue",             "fatigue"),
        ("weakness",            "weakness"),
        ("muscle aches",        "muscle aches"),
        ("joint pain",          "joint pain"),
        ("stiff neck",          "stiff neck"),
    ]
    available_others = [
        label for key, label in _OTHER_POOL
        if key not in symptom_set
    ]
    if available_others:
        sample = available_others[:6]
        questions.append(
            f"Do you have any other symptoms, such as {', '.join(sample)}?"
        )
    else:
        questions.append("Have you noticed any additional changes in how you feel?")

    # ── Fever follow-up — only ask about missing fever companions ────────────
    _FEVER_KEYS = {"fever", "high fever", "prolonged fever", "sudden high fever", "mild fever"}
    if symptom_set & _FEVER_KEYS:
        has_chills   = "chills" in symptom_set
        has_sweating = "sweating" in symptom_set or "night sweats" in symptom_set
        if not has_chills and not has_sweating:
            questions.append(
                "What is your temperature, and does the fever come with chills or sweating?"
            )
        elif not has_chills:
            questions.append(
                "What is your temperature, and does the fever come with chills?"
            )
        elif not has_sweating:
            questions.append(
                "What is your temperature, and does the fever come with sweating?"
            )
        else:
            # Both chills and sweating already known — just ask the temperature
            questions.append(
                "What is your temperature reading, and how long has the fever lasted?"
            )

    # ── Respiratory follow-up — only mention symptoms not yet known ──────────
    _RESP_KEYS = {"cough", "chronic cough", "shortness of breath", "chest pain", "wheezing",
                  "chest tightness", "coughing up blood"}
    if symptom_set & _RESP_KEYS:
        missing_resp = []
        if "chest pain" not in symptom_set:
            missing_resp.append("chest pain")
        if "wheezing" not in symptom_set:
            missing_resp.append("wheezing")
        if "coughing up blood" not in symptom_set:
            missing_resp.append("coughing up blood")
        if missing_resp:
            questions.append(
                f"Is there {', '.join(missing_resp)}, or unusually fast breathing?"
            )

    # ── GI follow-up ─────────────────────────────────────────────────────────
    _GI_KEYS = {"diarrhea", "profuse watery diarrhea", "bloody or mucus-filled diarrhea",
                "vomiting", "abdominal pain", "nausea"}
    if symptom_set & _GI_KEYS:
        questions.append(
            "Are you able to keep fluids down, and is there blood in your stool or "
            "signs of dehydration (dry mouth, no urine, sunken eyes)?"
        )

    # ── Fatigue / general weakness follow-up ─────────────────────────────────
    _FATIGUE_KEYS = {"fatigue", "weakness", "body weakness", "dizziness", "headache",
                     "muscle aches"}
    if symptom_set & _FATIGUE_KEYS:
        questions.append(
            "Have you recently had poor sleep, heavy physical work, stress, "
            "missed meals, or unusual exertion?"
        )

    # ── Pregnancy follow-up ───────────────────────────────────────────────────
    if is_pregnant:
        questions.append(
            "How many weeks pregnant are you, and is there bleeding, severe pain, "
            "vision change, swelling, or reduced fetal movement?"
        )

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
# Used to detect which questions have already been asked in prior assistant turns.
# Includes both the original templates and updated variants so history detection
# works across versions.
_ALL_FOLLOWUP_QUESTIONS = [
    "How long have you had these symptoms?",
    "Are they mild, moderate, or severe?",
    # Original "other symptoms" question (kept for history detection)
    "Do you have any other symptoms, such as fever, vomiting, diarrhea, chest pain, rash, dizziness, or trouble breathing?",
    # Fallback when all common symptoms are already reported
    "Have you noticed any additional changes in how you feel?",
    # Fever follow-up variants
    "What is your temperature, and does the fever come with chills or sweating?",
    "What is your temperature, and does the fever come with chills?",
    "What is your temperature, and does the fever come with sweating?",
    "What is your temperature reading, and how long has the fever lasted?",
    # Respiratory follow-up variants
    "Is there chest pain, wheezing, fast breathing, or coughing up blood?",
    "Is there wheezing, fast breathing, or coughing up blood?",
    "Is there chest pain, fast breathing, or coughing up blood?",
    "Is there fast breathing or coughing up blood?",
    # GI follow-up variants
    "Are you able to drink fluids, and is there blood in stool or signs of dehydration?",
    "Are you able to keep fluids down, and is there blood in your stool or signs of dehydration?",
    # Fatigue follow-up
    "Have you recently had poor sleep, heavy work, stress, missed meals, dehydration, or unusual exertion?",
    # Pregnancy follow-up
    "How many weeks pregnant are you, and is there bleeding, severe pain, vision change, swelling, or reduced fetal movement?",
]


def _get_asked_question_set(chat_history: list[dict] | None) -> set[str]:
    """Return the set of follow-up questions already present in assistant messages.

    Adds category sentinels so ``_next_unanswered_question`` can skip the
    whole *family* of related variants once any one of them has been asked —
    e.g. all four fever-temperature variants share the ``__fever_asked__``
    sentinel, so a second fever question is never repeated even when the
    symptom set changes between turns.
    """
    if not chat_history:
        return set()
    assistant_text = "\n".join(
        m.get("content", "") for m in chat_history if m.get("role") == "assistant"
    ).lower()
    asked = {q for q in _ALL_FOLLOWUP_QUESTIONS if q.lower() in assistant_text}

    # ── Category sentinels (phrase-based, not exact-string) ──────────────────
    # "Other symptoms" — dynamic question whose text varies per symptom set
    if (
        "do you have any other symptoms" in assistant_text
        or "have you noticed any additional changes in how you feel" in assistant_text
    ):
        asked.add("__other_symptoms_asked__")

    # Fever/temperature — all four variants share this sentinel
    if "what is your temperature" in assistant_text or "how long has the fever lasted" in assistant_text:
        asked.add("__fever_asked__")

    # Respiratory follow-up — variants share this sentinel
    if any(phrase in assistant_text for phrase in [
        "is there chest pain",
        "is there wheezing",
        "fast breathing or coughing up blood",
        "coughing up blood",
        "or unusually fast breathing",
    ]):
        asked.add("__resp_asked__")

    # GI / fluids follow-up
    if any(phrase in assistant_text for phrase in [
        "are you able to keep fluids",
        "are you able to drink fluids",
        "blood in your stool",
        "blood in stool",
        "signs of dehydration",
    ]):
        asked.add("__gi_asked__")

    # Fatigue / lifestyle follow-up
    if any(phrase in assistant_text for phrase in [
        "poor sleep",
        "heavy physical work",
        "unusual exertion",
        "missed meals",
    ]):
        asked.add("__fatigue_asked__")

    # Pregnancy follow-up
    if "how many weeks pregnant" in assistant_text:
        asked.add("__pregnancy_asked__")

    return asked


# All sentinel names — used to count how many follow-up categories have been covered
_CATEGORY_SENTINELS = frozenset({
    "__other_symptoms_asked__",
    "__fever_asked__",
    "__resp_asked__",
    "__gi_asked__",
    "__fatigue_asked__",
    "__pregnancy_asked__",
})


def _next_unanswered_question(questions: list[str], asked: set[str]) -> str | None:
    other_symptoms_done  = "__other_symptoms_asked__" in asked
    fever_done           = "__fever_asked__"          in asked
    resp_done            = "__resp_asked__"           in asked
    gi_done              = "__gi_asked__"             in asked
    fatigue_done         = "__fatigue_asked__"        in asked
    pregnancy_done       = "__pregnancy_asked__"      in asked

    for q in questions:
        if q in asked:
            continue
        q_lower = q.lower()

        # Skip the whole "other symptoms" category once asked
        if other_symptoms_done and (
            q_lower.startswith("do you have any other symptoms")
            or "additional changes in how you feel" in q_lower
        ):
            continue

        # Skip all fever temperature variants once any one was asked
        if fever_done and "what is your temperature" in q_lower:
            continue

        # Skip all respiratory variants once asked
        if resp_done and (
            "is there chest pain" in q_lower
            or "is there wheezing" in q_lower
            or "coughing up blood" in q_lower
            or "fast breathing" in q_lower
            or "unusually fast breathing" in q_lower
        ):
            continue

        # Skip GI/fluids variants once asked
        if gi_done and (
            q_lower.startswith("are you able to")
            and ("fluids" in q_lower or "blood in" in q_lower or "dehydration" in q_lower)
        ):
            continue

        # Skip fatigue follow-up once asked
        if fatigue_done and (
            "poor sleep" in q_lower
            or "heavy physical work" in q_lower
            or "unusual exertion" in q_lower
        ):
            continue

        # Skip pregnancy follow-up once asked
        if pregnancy_done and "how many weeks pregnant" in q_lower:
            continue

        return q
    return None


# ---------------------------------------------------------------------------
# Reply hints — shown below each follow-up question
# ---------------------------------------------------------------------------

_REPLY_HINTS: list[tuple[str, str]] = [
    ("how long have you had",        "*(e.g. 1 day · 3 days · about a week)*"),
    ("mild, moderate, or severe",    "*(Reply: mild / moderate / severe)*"),
    ("what is your temperature",     "*(e.g. 38 °C · 101 °F · or 'I don't have a thermometer')*"),
    ("do you have any other symptom","*(Name them, or reply **no** to go straight to results)*"),
    ("have you noticed any additional","*(Reply yes / no, or describe)*"),
    ("are you able to keep fluids",  "*(Reply yes/no — and mention dry mouth, no urine, or sunken eyes if present)*"),
    ("are you able to drink fluids", "*(Reply yes or no)*"),
    ("is there chest pain",          "*(Reply yes or no for each symptom mentioned)*"),
    ("is there wheezing",            "*(Reply yes or no)*"),
    ("fast breathing",               "*(Reply yes or no)*"),
    ("poor sleep",                   "*(Reply yes or no)*"),
    ("how many weeks pregnant",      "*(e.g. 24 weeks — and mention bleeding, pain, or reduced movement if present)*"),
]


def _get_reply_hint(question: str) -> str:
    q_lower = question.lower()
    for key, hint in _REPLY_HINTS:
        if key in q_lower:
            return hint
    return ""


# ---------------------------------------------------------------------------
# "No more symptoms" negation detector
# ---------------------------------------------------------------------------

_NO_MORE_SYMPTOMS_PATTERNS = [
    re.compile(r"^\s*no\s*[.!?]*\s*$", re.I),
    re.compile(r"^\s*(nope|nah)\s*[.!?]*\s*$", re.I),
    re.compile(r"\bno\b.{0,20}\b(other|more|additional|else)\b.{0,30}symptom", re.I),
    re.compile(r"\b(only|just)\s+those\b", re.I),
    re.compile(r"\bthat'?s?\s+(all|it)\b", re.I),
    re.compile(r"\bno\s+other\s+symptoms?\b", re.I),
    re.compile(r"\bnothing\s+(else|more|other)\b", re.I),
    re.compile(r"\bnone\b", re.I),
    re.compile(r"\bthose\s+are\s+(all|it)\b", re.I),
]


def _user_said_no_more_symptoms(query: str) -> bool:
    """Return True when the user's reply clearly signals there are no additional symptoms."""
    text = query.strip()
    return any(pat.search(text) for pat in _NO_MORE_SYMPTOMS_PATTERNS)


def _answered_followup_count(chat_history: list[dict] | None, questions: list[str]) -> int:
    asked = _get_asked_question_set(chat_history)
    return sum(1 for q in questions if q in asked)


def _next_followup_response(
    symptoms: list[str],
    questions: list[str],
    asked_count: int,
    pregnancy_context: bool,
    fatigue_context: bool,
    stress_presentation: bool = False,
) -> dict:
    next_question = questions[min(asked_count, len(questions) - 1)]
    symptom_text = ", ".join(symptoms) if symptoms else "your symptoms"
    hint = _get_reply_hint(next_question)

    if asked_count == 0:
        intro = (
            f"I found this in your message: {symptom_text}. "
            "I will ask one question at a time before showing possible matches."
        )
        # Offer a gentle stress/fatigue note on the very first question when the
        # presentation is short and non-specific — so the user isn't alarmed.
        if stress_presentation and len(symptoms) <= 4:
            intro += (
                "\n\n💡 *With just a few non-specific symptoms, stress, fatigue, or dehydration "
                "might be playing a role. I'll still check carefully — just a heads-up.*"
            )
        answer = f"{intro}\n\n{next_question}"
    else:
        answer = f"Noted. {next_question}"

    if hint:
        answer += f"\n\n{hint}"

    return {
        "answer": answer,
        "sources": [],
        "disclaimer": DISCLAIMER,
        "symptoms": symptoms,
        "predictions": [],
        "mode": "symptom_follow_up",
        "pregnancy_context": pregnancy_context,
        "fatigue_context": fatigue_context,
        "stress_presentation": stress_presentation,
        "follow_up_questions": [next_question],
        "data_source": "follow_up",  # collecting more info — no prediction engine used yet
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
    stress_presentation = _is_stress_typical_presentation(reported_symptoms, symptom_context)
    follow_up_questions = _symptom_follow_up_questions(reported_symptoms, pregnancy_context)

    asked_set = _get_asked_question_set(chat_history)

    # ── Max follow-up round cap ──────────────────────────────────────────────
    # Count how many question categories have already been covered.
    # Each sentinel = one category; each hardcoded Q = one question.
    # After 5 covered categories/questions proceed to predictions automatically,
    # so the conversation never gets stuck in an infinite loop.
    categories_done = len(asked_set & _CATEGORY_SENTINELS)
    real_qs_done    = len({q for q in asked_set if not q.startswith("__")})
    total_rounds    = categories_done + real_qs_done

    # If the user explicitly says there are no more symptoms, OR we have
    # reached the maximum number of follow-up rounds, skip to predictions.
    user_negated = (
        followup_already_asked and _user_said_no_more_symptoms(query)
    ) or total_rounds >= 5

    if not user_negated:
        next_q = _next_unanswered_question(follow_up_questions, asked_set)
        if next_q:
            is_first = not (asked_set - _CATEGORY_SENTINELS)
            return _next_followup_response(
                reported_symptoms,
                [next_q],
                0 if is_first else 1,
                pregnancy_context,
                fatigue_context,
                stress_presentation,
            )

    # Chat mode: don't gate on cardinal symptoms — the user may not have mentioned
    # every distinguishing symptom in natural conversation.
    predictions = _enrich_predictions_from_database(
        _get_predictor().predict(reported_symptoms, apply_cardinal_filter=False)
    )
    if fatigue_context:
        for prediction in predictions:
            prediction["fatigue_context"] = True

    # Reflect the actual backend that produced the predictions
    actual_data_source = predictions[0].get("data_source", "model") if predictions else "no_predictions"

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
            "stress_presentation": stress_presentation,
            "follow_up_questions": follow_up_questions,
            "data_source": actual_data_source,
        }

    # ── Seasonal alert ───────────────────────────────────────────────────────
    seasonal_note = _seasonal_context_note(query, reported_symptoms)
    # ── Child health note ────────────────────────────────────────────────────
    child_note = _child_health_context_note(query, reported_symptoms)

    lines = [
        f"I found these symptoms in your message: {', '.join(reported_symptoms)}.",
    ]
    if seasonal_note:
        lines.append(seasonal_note)
    if child_note:
        lines.append(child_note)

    # ── Stress / few-symptom context note (shown BEFORE the predictions list) ──
    if stress_presentation and len(reported_symptoms) <= 4:
        lines.append(
            "💡 *Note: Your symptoms could be linked to stress, fatigue, dehydration, or missed meals — "
            "very common when life is busy. I'll still show possible matches below, but consider resting, "
            "drinking water, and eating a proper meal first. If symptoms persist for more than 2 days or "
            "get worse, please see a health worker.*"
        )

    lines.append("Here are the top possible matches from the MediGuard symptom model:")
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
    if fatigue_context and not stress_presentation:
        # Only show the generic fatigue note when the full stress-presentation note wasn't already shown
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
        "stress_presentation": stress_presentation,
        "follow_up_questions": [],
        "data_source": actual_data_source,
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
        _local_chunks = json.loads(REFERENCE_CHUNKS_FILE.read_text(encoding="utf-8"))
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
                "source": chunk.get("source", "MediGuard medical references"),
                "score": score,
                "retrieval_source": "local_fallback",
            })
    return sorted(matches, key=lambda item: item["score"], reverse=True)[:top_k]


def retrieve(query: str, top_k: int = 5, filter_disease: str | None = None) -> list[dict]:
    index = _get_index()
    if index is None:
        return _local_retrieve(query, top_k=top_k, filter_disease=filter_disease)

    query_vector = embed_text(query, dim=_pinecone_dimension or 384)
    # Restrict to curated reference chunks; exclude disease_profile and training_example
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
            continue  # skip non-reference vectors that slipped through the filter
        chunks.append({
            "text": text,
            "disease": meta.get("disease", ""),
            "source": meta.get("source", "MediGuard medical references"),
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
        f"Based on the medical reference passages I found, {summary} "
        "For first aid, rest, drink safe fluids, monitor symptoms, and seek urgent care for severe, worsening, or persistent symptoms. "
        "MediGuard results can sometimes be faulty, so use this as educational guidance only and consult a qualified healthcare professional for personal symptoms."
    )


def _first_aid_chat_response(
    query: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> dict | None:
    """Return a structured first-aid response when the query describes an accident or injury.

    Priority order:
    1. Detect the specific accident type (burn, fracture, snake bite, etc.)
    2. If not matched but looks like a first-aid request, return general first aid guidance
    3. Otherwise return None so other handlers can process the query
    """
    if not is_first_aid_request(query):
        return None

    entry_key = detect_first_aid_type(query)

    # Fallback: if query says "first aid" or "accident" but type not detected, use general
    if entry_key is None:
        entry_key = "general_firstaid"

    answer = format_first_aid_response(entry_key, query)
    if not answer:
        return None

    entry = FIRST_AID_DATA[entry_key]
    severity = entry.get("severity", "moderate")

    # For critical emergencies, always append a facility nudge
    facility_note = ""
    if severity == "critical":
        if user_lat is not None and user_lng is not None:
            facility_note = (
                "\n\n📍 **Get to hospital now.** Ask me 'nearest hospital' and I will find "
                "facilities closest to your location."
            )
        else:
            facility_note = (
                "\n\n📍 **Get to the nearest hospital immediately.** "
                "You can also ask me 'nearest hospital' and share your location for directions."
            )

    return {
        "answer": answer + facility_note,
        "sources": ["MediGuard First Aid Guidelines"],
        "disclaimer": (
            "This first aid guidance is for immediate emergency use only. "
            "It does not replace professional emergency care. Always seek qualified medical help."
        ),
        "mode": "first_aid",
        "first_aid_type": entry_key,
        "severity": severity,
        "data_source": "firstaid_dataset",
        "follow_up_questions": [],
    }


# ---------------------------------------------------------------------------
# Seasonal disease context — Bamenda, North West Cameroon
# ---------------------------------------------------------------------------

# Month (1–12) → high-risk diseases with local explanations
_BAMENDA_SEASONAL_RISKS: dict[int, list[dict]] = {
    1:  [{"disease": "Meningitis",                "risk": "high",   "reason": "Dry harmattan air — NW Cameroon is in the African meningitis belt"},
         {"disease": "Measles",                   "risk": "medium", "reason": "Dry-season crowding increases measles spread"},
         {"disease": "Common Cold",               "risk": "medium", "reason": "Cold, dry harmattan air dries airways"}],
    2:  [{"disease": "Meningitis",                "risk": "high",   "reason": "Peak meningitis month in the harmattan season"},
         {"disease": "Measles",                   "risk": "high",   "reason": "Measles outbreaks peak February–March in Cameroon"}],
    3:  [{"disease": "Meningitis",                "risk": "medium", "reason": "End of harmattan meningitis season"},
         {"disease": "Typhoid Fever",             "risk": "medium", "reason": "Typhoid rises as rains approach and water sources change"}],
    4:  [{"disease": "Malaria",                   "risk": "high",   "reason": "Long rainy season starts — mosquito breeding surges"},
         {"disease": "Typhoid Fever",             "risk": "medium", "reason": "Contaminated water risk rises with first rains"}],
    5:  [{"disease": "Malaria",                   "risk": "high",   "reason": "Peak malaria month — stagnant pools everywhere"},
         {"disease": "Cholera",                   "risk": "medium", "reason": "Heavy rains can contaminate water sources"},
         {"disease": "Typhoid Fever",             "risk": "high",   "reason": "Waterborne disease risk elevated throughout rainy season"}],
    6:  [{"disease": "Malaria",                   "risk": "high",   "reason": "Malaria season continues through June–July"},
         {"disease": "Cholera",                   "risk": "medium", "reason": "Flood water contamination risk"},
         {"disease": "Typhoid Fever",             "risk": "high",   "reason": "Waterborne risk remains elevated"}],
    7:  [{"disease": "Malaria",                   "risk": "high",   "reason": "Mosquito numbers peak in the rainy season"},
         {"disease": "Skin Fungal Infection",     "risk": "medium", "reason": "Persistent wet weather promotes skin fungal infections"}],
    8:  [{"disease": "Malaria",                   "risk": "high",   "reason": "Malaria season at maximum intensity"},
         {"disease": "Typhoid Fever",             "risk": "high",   "reason": "Continued waterborne risk from rain-contaminated sources"},
         {"disease": "Cholera",                   "risk": "high",   "reason": "Cholera risk peaks approaching the second rains"}],
    9:  [{"disease": "Malaria",                   "risk": "high",   "reason": "Second rainy season — malaria risk high"},
         {"disease": "Cholera",                   "risk": "high",   "reason": "Peak cholera month — heavily contaminated water possible"},
         {"disease": "Typhoid Fever",             "risk": "high",   "reason": "Waterborne disease risk highest of the year"}],
    10: [{"disease": "Malaria",                   "risk": "high",   "reason": "Malaria still high as rains continue"},
         {"disease": "Cholera",                   "risk": "medium", "reason": "Cholera risk easing but still elevated"}],
    11: [{"disease": "Common Cold",               "risk": "medium", "reason": "Harmattan dust starts — respiratory infections rise"},
         {"disease": "Malaria",                   "risk": "medium", "reason": "Malaria declining but still present"}],
    12: [{"disease": "Common Cold",               "risk": "high",   "reason": "Peak harmattan — cold dry air causes respiratory infections"},
         {"disease": "Meningitis",                "risk": "medium", "reason": "Meningitis risk begins rising again in December"}],
}

_MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


def get_seasonal_context(month: int | None = None) -> dict:
    """Return the current seasonal disease risks for Bamenda.

    Returns a dict with ``month_name``, ``risks`` (list of disease dicts),
    and ``banner_text`` suitable for UI display.
    """
    from datetime import datetime
    if month is None:
        month = datetime.now().month
    risks = _BAMENDA_SEASONAL_RISKS.get(month, [])
    month_name = _MONTH_NAMES.get(month, "")
    high = [r for r in risks if r["risk"] == "high"]
    if high:
        names = " & ".join(r["disease"] for r in high[:2])
        banner = f"⚠️ {month_name} in Bamenda: High risk of {names}. Mention any related symptoms early."
    elif risks:
        names = " & ".join(r["disease"] for r in risks[:2])
        banner = f"🌿 {month_name}: Watch for {names} in Bamenda. Stay hydrated and sleep under a net."
    else:
        banner = ""
    return {"month": month, "month_name": month_name, "risks": risks, "banner_text": banner}


def _seasonal_context_note(query: str, symptoms: list[str]) -> str:
    """Inject a seasonal note into a response when the query involves fever, diarrhea,
    or neck stiffness and the current season makes a specific disease more likely."""
    from datetime import datetime
    month = datetime.now().month
    risks = _BAMENDA_SEASONAL_RISKS.get(month, [])
    if not risks:
        return ""
    text = f"{query.lower()} {' '.join(s.lower() for s in symptoms)}"
    notes = []
    for risk in risks:
        if risk["risk"] != "high":
            continue
        disease = risk["disease"]
        if disease == "Malaria" and any(t in text for t in ["fever", "chills", "headache", "sweating"]):
            notes.append(f"⚠️ **Seasonal alert:** It is currently high malaria season in Bamenda. Fever + headache + chills should be tested for malaria urgently.")
        elif disease == "Meningitis" and any(t in text for t in ["neck", "stiff", "headache", "fever", "confusion"]):
            notes.append(f"⚠️ **Seasonal alert:** This is meningitis season in NW Cameroon. A stiff neck with fever needs urgent hospital evaluation — do not wait.")
        elif disease == "Cholera" and any(t in text for t in ["diarrhea", "vomiting", "watery stool", "purge"]):
            notes.append(f"⚠️ **Seasonal alert:** Cholera risk is high this season. Profuse watery diarrhea needs urgent oral rehydration and hospital care.")
        elif disease == "Typhoid Fever" and any(t in text for t in ["fever", "stomach", "abdominal", "belly", "headache"]):
            notes.append(f"⚠️ **Seasonal alert:** Typhoid risk is elevated in the current rainy season. Drink only clean/boiled water.")
    return "\n\n".join(notes)


# ---------------------------------------------------------------------------
# Traditional medicine / herb bridge
# ---------------------------------------------------------------------------

_HERB_KNOWLEDGE: dict[str, dict] = {
    "neem": {
        "local_name": "Neem (dongoyaro)",
        "traditional_use": "Fever, malaria, infections",
        "evidence": "Neem has antimicrobial compounds and may help reduce fever symptoms. However, it **cannot replace antimalarial drugs** (e.g. Coartem) for confirmed malaria.",
        "warning": "Do not delay clinic-based malaria testing while using neem. Malaria can become life-threatening within hours.",
        "related_symptoms": ["Fever"],
    },
    "bitter leaf": {
        "local_name": "Bitter leaf (Vernonia amygdalina / ndole)",
        "traditional_use": "Stomach pain, fever, diabetes management",
        "evidence": "Bitter leaf has shown anti-inflammatory properties in research. It is commonly used for abdominal discomfort and is nutritious.",
        "warning": "It does not treat infections causing stomach pain. If pain is severe, persistent, or comes with fever — see a doctor.",
        "related_symptoms": ["Abdominal pain"],
    },
    "garlic": {
        "local_name": "Garlic (ail)",
        "traditional_use": "Cough, respiratory infections, antibacterial",
        "evidence": "Garlic contains allicin which has mild antimicrobial properties. It may soothe mild coughs and boost immunity slightly.",
        "warning": "Garlic tea cannot treat bacterial pneumonia or tuberculosis. Persistent cough (> 2 weeks) needs clinical evaluation.",
        "related_symptoms": ["Cough"],
    },
    "ginger": {
        "local_name": "Ginger (gingembre)",
        "traditional_use": "Nausea, stomach upset, fever",
        "evidence": "Ginger is well-studied for nausea relief and has mild anti-inflammatory effects. Safe during pregnancy in moderate amounts.",
        "warning": "Persistent vomiting with signs of dehydration (no urine, dry mouth, weakness) needs oral rehydration solution and clinic care.",
        "related_symptoms": ["Nausea", "Vomiting"],
    },
    "lemongrass": {
        "local_name": "Lemongrass / Lemon grass (citronnelle)",
        "traditional_use": "Fever, anxiety, digestive issues",
        "evidence": "Lemongrass tea may provide mild fever relief and has antioxidant properties. Widely used in West and Central Africa.",
        "warning": "Cannot replace malaria testing if fever is present. Use as supportive comfort, not treatment.",
        "related_symptoms": ["Fever"],
    },
    "moringa": {
        "local_name": "Moringa (moringa oleifera / arbre de vie)",
        "traditional_use": "Malnutrition, weakness, anaemia",
        "evidence": "Moringa leaves are very nutritious — high in iron, vitamins A/C, and protein. Helpful for malnutrition and iron-deficiency anaemia.",
        "warning": "Does not treat the cause of severe fatigue if caused by infection or disease. See a clinician if fatigue is persistent.",
        "related_symptoms": ["Fatigue", "Weakness"],
    },
    "pawpaw leaf": {
        "local_name": "Pawpaw/Papaya leaf (feuille de papaye)",
        "traditional_use": "Malaria, fever, platelet boost (dengue)",
        "evidence": "Papaya leaf extract has shown some benefit for platelet counts in dengue fever in small studies. Evidence for malaria treatment is insufficient.",
        "warning": "Do NOT use papaya leaf instead of anti-malarial treatment. Malaria must be tested and treated with proven drugs.",
        "related_symptoms": ["Fever"],
    },
    "guava leaf": {
        "local_name": "Guava leaf tea (feuille de goyave)",
        "traditional_use": "Diarrhea, stomach upset",
        "evidence": "Guava leaf has demonstrated antidiarrheal properties in several studies. May help with mild diarrhea.",
        "warning": "Bloody diarrhea, watery diarrhea with weakness, or diarrhea in children under 5 needs immediate ORS and clinical care.",
        "related_symptoms": ["Diarrhea"],
    },
    "aloe vera": {
        "local_name": "Aloe vera",
        "traditional_use": "Skin rashes, burns, wound healing",
        "evidence": "Aloe vera gel has soothing anti-inflammatory effects on skin. Well-supported for minor burns and mild rashes.",
        "warning": "Do not apply to deep wounds or infected skin. Infected sores or spreading rashes need antibiotic treatment.",
        "related_symptoms": ["Rash"],
    },
    "turmeric": {
        "local_name": "Turmeric (curcuma)",
        "traditional_use": "Joint pain, inflammation, digestion",
        "evidence": "Curcumin (in turmeric) has anti-inflammatory properties. May help mild joint pain and digestive discomfort.",
        "warning": "Cannot treat septic arthritis (hot, very swollen single joint) — that is a medical emergency.",
        "related_symptoms": ["Joint pain"],
    },
    "eucalyptus": {
        "local_name": "Eucalyptus / steam inhalation",
        "traditional_use": "Nasal congestion, cough, respiratory",
        "evidence": "Eucalyptus oil has decongestant properties. Steam inhalation with eucalyptus leaves can ease blocked nose and mild cough.",
        "warning": "Do not give eucalyptus oil orally to children. If breathing difficulty is severe, go to hospital immediately.",
        "related_symptoms": ["Cough", "Nasal congestion"],
    },
    "scent leaf": {
        "local_name": "Scent leaf / African basil (basilic africain / effirin)",
        "traditional_use": "Fever, malaria, infections",
        "evidence": "Some antimicrobial and antipyretic (fever-reducing) properties reported in research.",
        "warning": "As with neem, cannot replace confirmed malaria treatment. Use only as comfort measure while arranging testing.",
        "related_symptoms": ["Fever"],
    },
}

# Keywords that signal a traditional medicine query
_HERB_KEYWORDS: list[str] = [
    "neem", "bitter leaf", "garlic", "ginger", "lemongrass", "lemon grass",
    "moringa", "pawpaw leaf", "papaya leaf", "guava leaf", "aloe vera",
    "turmeric", "eucalyptus", "scent leaf", "african basil", "coconut water",
    "herbal", "herb", "traditional medicine", "bush medicine", "local medicine",
    "plant remedy", "remedy", "natural remedy", "home remedy",
    "feuille de", "tisane", "décoction", "remède naturel",
]


def _traditional_medicine_response(query: str) -> dict | None:
    """Detect herb / traditional medicine mentions and return a bridge response."""
    text = query.lower()
    if not any(kw in text for kw in _HERB_KEYWORDS):
        return None

    matched_herb: dict | None = None
    matched_key: str = ""
    for key, herb in _HERB_KNOWLEDGE.items():
        if key in text:
            matched_herb = herb
            matched_key = key
            break

    if matched_herb:
        lines = [
            f"🌿 **Traditional remedy: {matched_herb['local_name']}**\n",
            f"**Traditional use:** {matched_herb['traditional_use']}",
            f"\n**What the evidence says:** {matched_herb['evidence']}",
            f"\n⚠️ **Important:** {matched_herb['warning']}",
            "\n**MediGuard's advice:** Traditional remedies can provide comfort and may have genuine benefits, "
            "but they should complement — not replace — clinical care when symptoms are severe, persistent, "
            "or worsening. Always test for malaria if you have fever in Bamenda.",
        ]
        follow_ups = [
            f"What symptoms are you using {matched_key} for?",
            "How long have you had these symptoms?",
            "Have you been tested at a clinic yet?",
        ]
    else:
        # Generic herbal / home remedy query
        lines = [
            "🌿 **Traditional medicine and home remedies**\n",
            "Many local plants used in Bamenda have genuine health benefits supported by research. "
            "However, **traditional remedies work best as supportive comfort** — they should not replace "
            "proven treatments for serious illnesses like malaria, meningitis, typhoid, or tuberculosis.\n",
            "**Ask me about a specific herb or plant** (e.g. neem, bitter leaf, ginger, moringa, guava leaf) "
            "and I will tell you what the evidence says, what it is used for, and when you still need to go to the clinic.\n",
            "⚠️ **Always seek clinic care for:** high fever, stiff neck, severe diarrhea, difficulty breathing, "
            "chest pain, confusion, or symptoms in a child under 5.",
        ]
        follow_ups = [
            "Which herb or plant are you asking about?",
            "What symptoms are you trying to treat?",
            "How long have you had these symptoms?",
        ]

    return {
        "answer": "\n".join(lines),
        "sources": ["MediGuard Traditional Medicine Reference", "WHO African Traditional Medicine Guidance"],
        "disclaimer": DISCLAIMER,
        "mode": "traditional_medicine",
        "follow_up_questions": follow_ups,
    }


# ---------------------------------------------------------------------------
# Child health mode — detect queries about children/infants
# ---------------------------------------------------------------------------

_CHILD_TERMS: list[str] = [
    "my child", "my baby", "my pikin", "my son", "my daughter",
    "the baby", "the child", "my toddler", "my infant", "my kid",
    "mon enfant", "mon bébé", "ma fille", "mon fils", "le bébé",
    "pikin dey", "pikin get", "pikin no", "my pikin",
    "years old", "months old", "year old", "month old",
    "newborn", "new born", "neonate",
]

# Vaccination schedule for Cameroon EPI (Expanded Programme on Immunization)
_CAMEROON_EPI: list[dict] = [
    {"age": "At birth",       "vaccines": ["BCG", "OPV0 (Polio)"]},
    {"age": "6 weeks",        "vaccines": ["Pentavalent 1 (DTP-HepB-Hib)", "OPV1", "Pneumococcal PCV13-1", "Rotavirus 1"]},
    {"age": "10 weeks",       "vaccines": ["Pentavalent 2", "OPV2", "Pneumococcal PCV13-2", "Rotavirus 2"]},
    {"age": "14 weeks",       "vaccines": ["Pentavalent 3", "OPV3", "IPV", "Pneumococcal PCV13-3"]},
    {"age": "9 months",       "vaccines": ["Measles-Rubella (MR1)", "Yellow Fever", "Meningococcal A"]},
    {"age": "15–18 months",   "vaccines": ["Measles-Rubella booster (MR2)"]},
]

_CHILD_DANGER_SIGNS: list[str] = [
    "convulsions", "seizures", "fits", "unconscious", "not waking",
    "very fast breathing", "chest in-drawing", "unable to drink",
    "vomiting everything", "blood in stool", "severe dehydration",
    "high fever in baby", "bulging fontanelle", "stiff neck in baby",
    "yellow skin newborn", "yellow eyes newborn",
]


def _is_child_health_query(query: str) -> bool:
    text = query.lower()
    return any(term in text for term in _CHILD_TERMS)


def _child_health_context_note(query: str, symptoms: list[str]) -> str:
    """Return a child-specific note when the query is about a child."""
    if not _is_child_health_query(query):
        return ""
    text = f"{query.lower()} {' '.join(s.lower() for s in symptoms)}"
    danger_found = [sign for sign in _CHILD_DANGER_SIGNS if sign in text]
    if danger_found:
        return (
            "\n\n🚨 **CHILD DANGER SIGN DETECTED:** "
            f"You mentioned: *{', '.join(danger_found[:3])}*. "
            "**This is an emergency — take the child to the nearest hospital immediately.** "
            "Do not wait. Danger signs in children under 5 can become life-threatening within hours."
        )
    # Gentle child-specific note
    return (
        "\n\n👶 **Child health note:** Symptoms in children — especially under 5 — can worsen quickly. "
        "Seek clinic care if the child has high fever (≥ 38.5 °C), cannot drink, has fast breathing, "
        "a stiff neck, fits/seizures, or is unusually drowsy. Do not give adult medication doses to children."
    )


def _vaccination_query_response(query: str) -> dict | None:
    """Handle vaccination / immunisation schedule queries."""
    text = query.lower()
    if not any(kw in text for kw in [
        "vaccine", "vaccination", "immunisation", "immunization",
        "vaccin", "epi", "immuniser", "jab", "shot", "injection schedule",
        "when to vaccinate", "vaccination schedule",
    ]):
        return None
    lines = [
        "💉 **Cameroon Immunisation Schedule (EPI)**\n",
        "The following vaccines are provided **free** at government health centres in Cameroon:\n",
    ]
    for entry in _CAMEROON_EPI:
        vaccines = ", ".join(entry["vaccines"])
        lines.append(f"**{entry['age']}:** {vaccines}")
    lines.extend([
        "\n📍 **Where to vaccinate in Bamenda:**",
        "- Bamenda Regional Hospital — Immunisation Unit",
        "- Any district health centre (free under Cameroon EPI)",
        "- Nkwen Baptist Hospital",
        "\n⚠️ Keep your child's vaccination card safe — bring it to every clinic visit.",
        "\n*If your child has missed vaccinations, visit the nearest health centre — catch-up vaccines are available.*",
    ])
    return {
        "answer": "\n".join(lines),
        "sources": ["Cameroon EPI / MINSANTE", "WHO Immunisation Schedule"],
        "disclaimer": DISCLAIMER,
        "mode": "vaccination_info",
        "follow_up_questions": [
            "How old is your child?",
            "Which vaccines has the child already received?",
            "Does your child have a vaccination card?",
        ],
    }


# ---------------------------------------------------------------------------
# Pidgin / Camfranglais conversational detection
# ---------------------------------------------------------------------------

_PIDGIN_GREETINGS: list[str] = [
    "how you dey", "how na", "how far", "i dey here",
    "oga", "na wah", "wetin dey happen", "wussap",
    "whats up na", "how e dey", "na how", "e don do",
]

_PIDGIN_THANKS: list[str] = [
    "i thank you", "tanks na", "thank you o", "e don do fine",
    "you do well", "you sabi", "you know book",
]


def _pidgin_conversational_response(query: str) -> dict | None:
    """Detect Pidgin greetings/thanks and respond naturally."""
    text = query.lower().strip()
    if any(pg in text for pg in _PIDGIN_GREETINGS):
        return {
            "answer": (
                "How you dey! 👋 Welcome to MediGuard Bamenda.\n\n"
                "I fit help you with:\n"
                "• **Symptom check** — tell me how your body dey feel\n"
                "• **Disease information** — I go explain any sickness\n"
                "• **Nearest hospital** — I fit find hospital wey dey close to you\n"
                "• **Traditional medicine** — I go tell you if any herb fit help\n"
                "• **Child health** — for your pikin dem\n\n"
                "Just tell me wetin dey worry you or your family. No need plenty grammar! 😊"
            ),
            "sources": [],
            "disclaimer": DISCLAIMER,
            "mode": "pidgin_greeting",
            "follow_up_questions": [
                "Wetin dey worry you?",
                "Which part of your body dey pain you?",
                "You get fever or your pikin get fever?",
            ],
        }
    if any(pt in text for pt in _PIDGIN_THANKS):
        return {
            "answer": (
                "You welcome! 🙏 Any time your body dey do you anyhow or your pikin sick, "
                "just come back tell me. MediGuard dey here for Bamenda community. "
                "Make you stay well! 💪"
            ),
            "sources": [],
            "disclaimer": DISCLAIMER,
            "mode": "pidgin_thanks",
        }
    return None


def generate_answer(
    query: str,
    filter_disease: str | None = None,
    chat_history: list[dict] | None = None,
    gender: str | None = None,
    is_pregnant: bool = False,
    pregnancy_weeks: int | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    child_mode: bool = False,
) -> dict:
    # If child mode is active, prepend context so all handlers recognise it
    if child_mode and not query.lower().startswith("my child"):
        query = f"[Child mode] {query}"

    # ── Pidgin / Camfranglais greeting (before standard conversational) ─────────
    pidgin_conv = _pidgin_conversational_response(query)
    if pidgin_conv:
        return pidgin_conv

    conversational = _conversational_response(query)
    if conversational:
        return conversational

    # ── Vaccination / immunisation schedule ──────────────────────────────────
    vaccination = _vaccination_query_response(query)
    if vaccination:
        return vaccination

    # ── Traditional medicine / herb bridge ────────────────────────────────────
    trad_med = _traditional_medicine_response(query)
    if trad_med:
        return trad_med

    # ── First aid / accident handler (high priority — before disease lookup) ──
    first_aid = _first_aid_chat_response(query, user_lat=user_lat, user_lng=user_lng)
    if first_aid:
        return first_aid

    # ── Possible pregnancy suggestion for users who may not know they're pregnant ──
    pregnancy_suggestion = _unaware_pregnancy_response(query, gender=gender)
    if pregnancy_suggestion:
        return pregnancy_suggestion

    trends = _trends_response(query)
    if trends:
        return trends

    facilities = _facilities_response(query, user_lat=user_lat, user_lng=user_lng)
    if facilities:
        return facilities

    platform = _platform_response(query)
    if platform:
        return platform

    if _history_requested_followup(chat_history):
        symptom_check = _symptom_check_response(
            query,
            is_pregnant=is_pregnant,
            pregnancy_weeks=pregnancy_weeks,
            chat_history=chat_history,
        )
        if symptom_check:
            return symptom_check

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
            "answer": "I could not find relevant MediGuard reference information for that question. Please try rephrasing or consult a healthcare professional.",
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
        lang_note = (
            "IMPORTANT: The user is writing in French. Respond entirely in French. "
            "Translate any medical terms to plain French where possible.\n\n"
            if _is_french(query) else ""
        )
        from datetime import datetime as _dt
        _season_ctx = get_seasonal_context(_dt.now().month)
        _season_prompt = ""
        if _season_ctx["risks"]:
            high_risk = [r["disease"] for r in _season_ctx["risks"] if r["risk"] == "high"]
            if high_risk:
                _season_prompt = (
                    f"\n\nSEASONAL CONTEXT: It is currently {_season_ctx['month_name']} in Bamenda. "
                    f"High-risk diseases this season: {', '.join(high_risk)}. "
                    "Mention this context when relevant to the user's symptoms."
                )
        _child_prompt = ""
        if _is_child_health_query(query):
            _child_prompt = (
                "\n\nCHILD HEALTH MODE: The user is asking about a child. "
                "Use age-appropriate dosing guidance, mention child danger signs (high fever, fast breathing, "
                "inability to drink, stiff neck, fits/convulsions), and recommend the Cameroon EPI vaccination "
                "schedule when relevant. Be extra cautious — symptoms in children under 5 escalate quickly."
            )
        messages = [{
            "role": "system",
            "content": (
                f"{lang_note}"
                "You are MediGuard's health assistant for Bamenda, Cameroon. "
                "You understand Cameroon Pidgin English (Camfranglais) — if the user writes in Pidgin, "
                "respond in plain, simple English that is easy to understand. "
                "Answer clearly using only the context below. Never diagnose or prescribe medication. "
                "When the user describes an accident or injury, provide clear step-by-step first aid guidance. "
                "For health questions, include simple first aid, self-care steps, and urgent-care red flags. "
                "Tell users that automated results can sometimes be incomplete or faulty. "
                "Always recommend professional care for personal symptoms. "
                "If the user is pregnant, ask follow-up questions about gestational age, bleeding, fever, "
                "pain, vision changes, swelling, and fetal movement before giving non-urgent guidance."
                f"{_season_prompt}{_child_prompt}\n\n"
                f"User context: gender={gender or 'not provided'}, pregnant={is_pregnant}, "
                f"pregnancy_weeks={pregnancy_weeks or 'not provided'}.\n\n"
                f"Context from MediGuard curated medical references:\n{context}"
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

