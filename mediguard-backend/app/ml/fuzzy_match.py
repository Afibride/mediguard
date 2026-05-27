"""
Fuzzy symptom matching.

Maps free-text symptom descriptions — including misspellings, informal phrases,
connectives ("I have a fever and headache"), and common typos — to canonical
symptom names used by the ML model.

Also covers:
  - Cameroon Pidgin English (Camfranglais) phrases
  - Local herb / traditional-medicine queries (mapped to related symptoms)
  - Common Francophone African phrasing
"""

import difflib
import re

# ---------------------------------------------------------------------------
# Alias dictionary: lowercase phrase → canonical symptom name
# Covers common misspellings, synonyms, and informal descriptions.
# ---------------------------------------------------------------------------
SYMPTOM_ALIASES: dict[str, str] = {
    # ── Fever / Temperature ──────────────────────────────────────────────────
    "fever": "Fever",
    "feaver": "Fever",
    "fevr": "Fever",
    "fiver": "Fever",
    "high temperature": "Fever",
    "temperature": "Fever",
    "hot body": "Fever",
    "body heat": "Fever",
    "raised temperature": "Fever",
    "mild fever": "Mild fever",
    "slight fever": "Mild fever",
    "low grade fever": "Mild fever",
    "low-grade fever": "Mild fever",
    "high fever": "High fever",
    "very high temperature": "High fever",
    "severe fever": "High fever",
    "prolonged fever": "Prolonged fever",
    "persistent fever": "Prolonged fever",
    "long lasting fever": "Prolonged fever",
    "sudden fever": "Sudden high fever",
    "sudden high fever": "Sudden high fever",
    # ── Headache ─────────────────────────────────────────────────────────────
    "headache": "Headache",
    "head ache": "Headache",
    "headach": "Headache",
    "headche": "Headache",
    "hed ache": "Headache",
    "pain in head": "Headache",
    "pain in my head": "Headache",
    "head pain": "Headache",
    "migrane": "Severe headache",
    "migraine": "Severe headache",
    "severe headache": "Severe headache",
    "very bad headache": "Severe headache",
    "pounding headache": "Severe headache",
    "throbbing headache": "Severe headache",
    "one sided headache": "Severe headache",
    # ── Nausea / Vomiting ────────────────────────────────────────────────────
    "nausea": "Nausea",
    "nauseated": "Nausea",
    "feel sick": "Nausea",
    "feeling sick": "Nausea",
    "queasy": "Nausea",
    "sick to stomach": "Nausea",
    "stomach sick": "Nausea",
    "vomiting": "Vomiting",
    "vomit": "Vomiting",
    "throwing up": "Vomiting",
    "puking": "Vomiting",
    "puke": "Vomiting",
    "throwing out": "Vomiting",
    "vomitting": "Vomiting",
    "vommiting": "Vomiting",
    # ── Fatigue / Weakness ───────────────────────────────────────────────────
    "fatigue": "Fatigue",
    "tired": "Fatigue",
    "tiredness": "Fatigue",
    "exhausted": "Fatigue",
    "exhaustion": "Fatigue",
    "very tired": "Fatigue",
    "extreme tiredness": "Fatigue",
    "weakness": "Weakness",
    "weak": "Weakness",
    "feeling weak": "Weakness",
    "body weakness": "Body weakness",
    "general weakness": "Weakness",
    "no energy": "Fatigue",
    # ── Cough ────────────────────────────────────────────────────────────────
    "cough": "Cough",
    "coughing": "Cough",
    "dry cough": "Cough",
    "wet cough": "Cough",
    "persistent cough": "Chronic cough",
    "chronic cough": "Chronic cough",
    "long cough": "Chronic cough",
    "coughing blood": "Coughing up blood",
    "spitting blood": "Coughing up blood",
    "blood in sputum": "Coughing up blood",
    "whooping cough": "Cough",
    "barking cough": "Cough",
    # ── Respiratory ─────────────────────────────────────────────────────────
    "shortness of breath": "Shortness of breath",
    "short of breath": "Shortness of breath",
    "difficulty breathing": "Shortness of breath",
    "can't breathe": "Shortness of breath",
    "cannot breathe": "Shortness of breath",
    "breathlessness": "Shortness of breath",
    "hard to breathe": "Shortness of breath",
    "breathing difficulty": "Shortness of breath",
    "wheezing": "Wheezing",
    "whistling breath": "Wheezing",
    "chest tightness": "Chest tightness",
    "tight chest": "Chest tightness",
    "chest pain": "Chest pain",
    "chest ache": "Chest pain",
    "pain in chest": "Chest pain",
    "chest discomfort": "Chest pain",
    "runny nose": "Runny nose",
    "running nose": "Runny nose",
    "watery nose": "Runny nose",
    "nose running": "Runny nose",
    "nose discharge": "Runny nose",
    "dripping nose": "Runny nose",
    "nasal congestion": "Nasal congestion",
    "blocked nose": "Nasal congestion",
    "stuffy nose": "Nasal congestion",
    "congested nose": "Nasal congestion",
    "sore throat": "Sore throat",
    "throat pain": "Sore throat",
    "throat ache": "Sore throat",
    "painful throat": "Sore throat",
    "scratchy throat": "Sore throat",
    "sneezing": "Sneezing",
    "sneeze": "Sneezing",
    "hoarse voice": "Hoarse voice",
    "hoarseness": "Hoarse voice",
    "voice change": "Hoarse voice",
    "croaky voice": "Hoarse voice",
    "raspy voice": "Hoarse voice",
    "difficulty swallowing": "Difficulty swallowing",
    "hard to swallow": "Difficulty swallowing",
    "can't swallow": "Difficulty swallowing",
    "painful swallowing": "Difficulty swallowing",
    # ── Gastrointestinal ─────────────────────────────────────────────────────
    "abdominal pain": "Abdominal pain",
    "stomach pain": "Abdominal pain",
    "belly pain": "Abdominal pain",
    "tummy pain": "Abdominal pain",
    "stomach ache": "Abdominal pain",
    "stomachache": "Abdominal pain",
    "belly ache": "Abdominal pain",
    "lower abdominal pain": "Lower abdominal pain",
    "pelvic pain": "Pelvic pain",
    "pelvic ache": "Pelvic pain",
    "diarrhea": "Diarrhea",
    "diarrhoea": "Diarrhea",
    "running stomach": "Diarrhea",
    "loose stool": "Diarrhea",
    "loose bowels": "Diarrhea",
    "watery stool": "Diarrhea",
    "running tummy": "Diarrhea",
    "frequent stool": "Diarrhea",
    "constipation": "Constipation",
    "no stool": "Constipation",
    "can't pass stool": "Constipation",
    "hard stool": "Constipation",
    "bloating": "Bloating",
    "bloated": "Bloating",
    "stomach bloated": "Bloating",
    "gas": "Bloating",
    "heartburn": "Heartburn",
    "acid reflux": "Heartburn",
    "burning chest": "Heartburn",
    "burping": "Bloating",
    "burning stomach": "Burning stomach pain",
    "burning stomach pain": "Burning stomach pain",
    "loss of appetite": "Loss of appetite",
    "no appetite": "Loss of appetite",
    "not hungry": "Loss of appetite",
    "can't eat": "Loss of appetite",
    "not eating": "Loss of appetite",
    "dehydration": "Dehydration",
    "very thirsty": "Increased thirst",
    "increased thirst": "Increased thirst",
    "excessive thirst": "Increased thirst",
    "always thirsty": "Increased thirst",
    # ── Urinary ──────────────────────────────────────────────────────────────
    "frequent urination": "Frequent urination",
    "urinating often": "Frequent urination",
    "urinating frequently": "Frequent urination",
    "peeing often": "Frequent urination",
    "always urinating": "Frequent urination",
    "painful urination": "Painful urination",
    "pain when urinating": "Painful urination",
    "burning urination": "Painful urination",
    "burning when pee": "Painful urination",
    "pain on urination": "Painful urination",
    "blood in urine": "Blood in urine",
    "bloody urine": "Blood in urine",
    "red urine": "Blood in urine",
    "pink urine": "Blood in urine",
    "dark urine": "Dark urine",
    "brown urine": "Dark urine",
    "cola urine": "Dark urine",
    "reduced urination": "Reduced urination",
    "not urinating": "Reduced urination",
    "difficulty urinating": "Reduced urination",
    # ── Pain ─────────────────────────────────────────────────────────────────
    "joint pain": "Joint pain",
    "joint ache": "Joint pain",
    "painful joints": "Joint pain",
    "arthritis": "Joint pain",
    "bone pain": "Joint pain",
    "muscle pain": "Muscle aches",
    "muscle ache": "Muscle aches",
    "body pain": "Muscle aches",
    "body ache": "Muscle aches",
    "aching body": "Muscle aches",
    "aches": "Muscle aches",
    "back pain": "Back pain",
    "backache": "Back pain",
    "lower back pain": "Back pain",
    "back ache": "Back pain",
    "neck pain": "Neck pain",
    "stiff neck": "Stiff neck",
    "neck stiffness": "Stiff neck",
    "jaw pain": "Jaw stiffness",
    "jaw stiffness": "Jaw stiffness",
    "locked jaw": "Jaw stiffness",
    "lockjaw": "Jaw stiffness",
    "jaw swelling": "Jaw stiffness",
    "trismus": "Jaw stiffness",
    "ear pain": "Ear pain",
    "earache": "Ear pain",
    "ear ache": "Ear pain",
    "pain in ear": "Ear pain",
    "facial pain": "Facial pain",
    "face pain": "Facial pain",
    "sinus pain": "Facial pain",
    "eye pain": "Eye pain",
    "painful eyes": "Eye pain",
    "pain in eye": "Eye pain",
    # ── Neurological ─────────────────────────────────────────────────────────
    "dizziness": "Dizziness",
    "dizzy": "Dizziness",
    "feeling dizzy": "Dizziness",
    "lightheaded": "Dizziness",
    "light headed": "Dizziness",
    "spinning": "Dizziness",
    "blurred vision": "Blurred vision",
    "blur": "Blurred vision",
    "vision blur": "Blurred vision",
    "can't see clearly": "Blurred vision",
    "hazy vision": "Blurred vision",
    "confusion": "Confusion",
    "confused": "Confusion",
    "disoriented": "Confusion",
    "not thinking clearly": "Confusion",
    "mental confusion": "Confusion",
    "sensitivity to light": "Sensitivity to light",
    "light hurts eyes": "Sensitivity to light",
    "photophobia": "Sensitivity to light",
    "can't stand light": "Sensitivity to light",
    "sensitivity to sound": "Sensitivity to sound",
    "sound hurts": "Sensitivity to sound",
    "noise sensitivity": "Sensitivity to sound",
    "numbness": "Numbness",
    "numb": "Numbness",
    "tingling": "Numbness",
    "tremor": "Tremor",
    "shaking hands": "Tremor",
    "hand trembling": "Tremor",
    "shaking": "Tremor",
    "seizures": "Seizures",
    "fits": "Seizures",
    "convulsions": "Seizures",
    "seizure": "Seizures",
    "epileptic fit": "Seizures",
    "poor coordination": "Poor coordination",
    "difficulty walking": "Difficulty walking",
    "hard to walk": "Difficulty walking",
    "sleep disturbances": "Sleep disturbances",
    "can't sleep": "Sleep disturbances",
    "insomnia": "Sleep disturbances",
    "waking at night": "Sleep disturbances",
    # ── Skin ─────────────────────────────────────────────────────────────────
    "rash": "Rash",
    "skin rash": "Rash",
    "spots on skin": "Rash",
    "itchy rash": "Itchy rash",
    "itching": "Itchy skin",
    "itchy": "Itchy skin",
    "itchy skin": "Itchy skin",
    "itch": "Itchy skin",
    "scratching": "Itchy skin",
    "severe itching": "Severe itching",
    "very itchy": "Severe itching",
    "ring rash": "Ring-shaped rash",
    "ring shaped rash": "Ring-shaped rash",
    "circular rash": "Ring-shaped rash",
    "red scaly skin": "Red scaly skin",
    "scaly skin": "Red scaly skin",
    "flaky skin": "Skin peeling",
    "skin peeling": "Skin peeling",
    "peeling skin": "Skin peeling",
    "blisters": "Blisters",
    "skin blisters": "Blisters",
    "water blisters": "Blisters",
    "pimples": "Skin sores",
    "boil": "Skin sores",
    "skin sores": "Skin sores",
    "skin lesions": "Skin lesions",
    "skin marks": "Skin lesions",
    "pus": "Pus or discharge",
    "pus discharge": "Pus or discharge",
    "discharge": "Pus or discharge",
    "burrow tracks": "Burrow tracks",
    "night itching": "Night itching",
    "itching at night": "Night itching",
    "hair loss": "Hair loss",
    "losing hair": "Hair loss",
    "bald patches": "Hair loss",
    "pale skin": "Pale skin",
    "paleness": "Pale skin",
    "yellowish skin": "Jaundice",
    "yellow skin": "Jaundice",
    "jaundice": "Jaundice",
    "yellowing skin": "Jaundice",
    "yellow eyes": "Yellow eyes",
    "yellowing eyes": "Yellow eyes",
    "white patches in mouth": "White patches in mouth",
    "mouth sores": "White patches in mouth",
    "oral thrush": "White patches in mouth",
    # ── Eyes ─────────────────────────────────────────────────────────────────
    "red eyes": "Red eyes",
    "pink eye": "Red eyes",
    "conjunctivitis": "Red eyes",
    "bloodshot eyes": "Red eyes",
    "eye discharge": "Eye discharge",
    "discharge from eye": "Eye discharge",
    "crusty eyes": "Eye discharge",
    "watery eyes": "Eye discharge",
    "hearing loss": "Hearing loss",
    "can't hear": "Hearing loss",
    "deaf": "Hearing loss",
    "ear discharge": "Pus or discharge",
    # ── Cardiovascular ───────────────────────────────────────────────────────
    "fast heartbeat": "Fast heartbeat",
    "heart racing": "Fast heartbeat",
    "heart pounding": "Fast heartbeat",
    "palpitations": "Fast heartbeat",
    "rapid pulse": "Fast heartbeat",
    "low blood pressure": "Low blood pressure",
    "hypotension": "Low blood pressure",
    "collapsed": "Low blood pressure",
    "fainted": "Dizziness",
    "swollen feet": "Swollen feet",
    "swollen legs": "Swollen feet",
    "oedema": "Swollen feet",
    "edema": "Swollen feet",
    "ankle swelling": "Ankle swelling",
    "swollen ankles": "Ankle swelling",
    # ── Systemic / Other ─────────────────────────────────────────────────────
    "night sweats": "Night sweats",
    "sweating at night": "Night sweats",
    "sweat at night": "Night sweats",
    "weight loss": "Weight loss",
    "losing weight": "Weight loss",
    "unexplained weight loss": "Weight loss",
    "swollen glands": "Swollen lymph nodes",
    "swollen lymph nodes": "Swollen lymph nodes",
    "neck lumps": "Swollen lymph nodes",
    "swollen neck": "Swollen lymph nodes",
    "lymph nodes": "Swollen lymph nodes",
    "fast heart rate": "Fast heartbeat",
    "chills": "Chills",
    "shivering": "Chills",
    "shiver": "Chills",
    "cold shaking": "Chills",
    "sweating": "Sweating",
    "excessive sweating": "Excessive sweating",
    "profuse sweating": "Excessive sweating",
    "slow healing wounds": "Slow-healing sores",
    "wounds not healing": "Slow-healing sores",
    "wound not healing": "Slow-healing sores",
    "bleeding": "Mild bleeding",
    "nosebleed": "Nose bleeding",
    "nose bleed": "Nose bleeding",
    "gum bleed": "Gum bleeding",
    "bleeding gums": "Gum bleeding",
    # ── Reproductive / Gynaecological ────────────────────────────────────────
    "vaginal discharge": "Vaginal discharge",
    "discharge from vagina": "Vaginal discharge",
    "unusual discharge": "Vaginal discharge",
    "vaginal itching": "Vaginal itching",
    "itching in vagina": "Vaginal itching",
    "vaginal bleeding": "Vaginal bleeding",
    "abnormal bleeding": "Vaginal bleeding",
    "missed period": "Missed period",
    "no period": "Missed period",
    "late period": "Missed period",
    "pain during intercourse": "Pain during intercourse",
    "painful sex": "Pain during intercourse",
    # ── Parasitic specific ───────────────────────────────────────────────────
    "worms in stool": "Visible worms in stool",
    "anal itch": "Anal itching",
    "itchy anus": "Anal itching",
    "anal itching": "Anal itching",
    "river blindness": "Blurred vision",
    "swollen limbs": "Swollen feet",

    # ── Cameroon Pidgin English (Camfranglais) ────────────────────────────────
    # Head / neurological
    "my head dey pain me": "Headache",
    "head dey pain me": "Headache",
    "my head dey do me": "Headache",
    "head dey do me": "Headache",
    "my head dey hot": "Fever",
    "head dey pain": "Headache",
    "e dey pain my head": "Headache",
    "e dey beat for my head": "Severe headache",
    "my head dey spin": "Dizziness",
    "head dey spin": "Dizziness",
    "i dey feel dizzy": "Dizziness",
    "my eye dey blur": "Blurred vision",
    "my eye no dey see well": "Blurred vision",
    # Fever / temperature
    "my body dey hot": "Fever",
    "body dey hot": "Fever",
    "i get fever": "Fever",
    "i get hot body": "Fever",
    "e dey hot for body": "Fever",
    "body hot": "Fever",
    "i dey shake for cold": "Chills",
    "i dey shiver": "Chills",
    "my body dey shake": "Chills",
    # Fatigue / weakness
    "my body dey tire me": "Fatigue",
    "body dey tire me": "Fatigue",
    "i dey feel weak": "Weakness",
    "i no get strength": "Weakness",
    "body weak": "Weakness",
    "i dey tire": "Fatigue",
    "i no fit stand": "Weakness",
    "my body dey pain me": "Muscle aches",
    "body dey pain me": "Muscle aches",
    # Stomach / gastrointestinal
    "belle dey do me": "Abdominal pain",
    "my belle dey do me": "Abdominal pain",
    "stomach dey do me": "Abdominal pain",
    "my stomach dey pain me": "Abdominal pain",
    "belly dey pain me": "Abdominal pain",
    "i get stomach pain": "Abdominal pain",
    "i dey vomit": "Vomiting",
    "i dey vomit since yesterday": "Vomiting",
    "i dey purge": "Diarrhea",
    "i get purge": "Diarrhea",
    "running stomach": "Diarrhea",
    "my stomach dey run": "Diarrhea",
    "stool dey come anyhow": "Diarrhea",
    "watery poo-poo": "Diarrhea",
    "watery poo poo": "Diarrhea",
    "blood for poo-poo": "Bloody or mucus-filled diarrhea",
    "blood for stool": "Bloody or mucus-filled diarrhea",
    "i no wan eat": "Loss of appetite",
    "i no dey hungry": "Loss of appetite",
    "food no dey sweet me": "Loss of appetite",
    "i no fit eat": "Loss of appetite",
    "my pikin no dey eat": "Loss of appetite",
    # Cough / respiratory
    "i dey cough": "Cough",
    "i get cough": "Cough",
    "strong cough": "Chronic cough",
    "cough dey worry me": "Chronic cough",
    "i no fit breathe well": "Shortness of breath",
    "breath dey short me": "Shortness of breath",
    "chest dey pain me": "Chest pain",
    "my chest dey pain me": "Chest pain",
    "chest dey tight": "Chest tightness",
    "i dey wheeze": "Wheezing",
    "throat dey pain me": "Sore throat",
    "my throat dey pain me": "Sore throat",
    "nose dey run": "Runny nose",
    "my nose dey run": "Runny nose",
    # Eyes / skin
    "my eye dey yellow": "Yellow eyes",
    "eye dey yellow": "Yellow eyes",
    "yellow eye": "Yellow eyes",
    "skin dey yellow": "Jaundice",
    "my skin dey yellow": "Jaundice",
    "i get rash for skin": "Rash",
    "rash dey my body": "Rash",
    "skin dey itch me": "Itchy skin",
    "my skin dey itch me": "Itchy skin",
    "body dey itch me": "Itchy skin",
    "skin dey scratch": "Itchy skin",
    "eye dey red": "Red eyes",
    "my eye dey red": "Red eyes",
    "eye discharge": "Eye discharge",
    # Urinary / reproductive
    "i dey urinate too much": "Frequent urination",
    "pee dey pain me": "Painful urination",
    "piss dey pain me": "Painful urination",
    "urine dey pain me": "Painful urination",
    "blood for urine": "Blood in urine",
    "dark urine": "Dark urine",
    # Joints / bones
    "joint dey pain me": "Joint pain",
    "my joint dey pain me": "Joint pain",
    "bone dey pain me": "Joint pain",
    "waist dey pain me": "Back pain",
    "my waist dey pain me": "Back pain",
    "neck stiff": "Stiff neck",
    "my neck stiff": "Stiff neck",
    # Child-specific Pidgin
    "my pikin dey hot": "Fever",
    "pikin dey shake": "Chills",
    "pikin body hot": "Fever",
    "my pikin dey cry": "Abdominal pain",
    "pikin no dey sleep": "Fatigue",
    "my pikin dey vomit": "Vomiting",
    "pikin dey purge": "Diarrhea",
    "pikin get rash": "Rash",
    "pikin neck stiff": "Stiff neck",
    "pikin eye dey yellow": "Yellow eyes",
    # ── Traditional medicine / local herb symptom links ───────────────────────
    # These map herb mentions to the symptom the user is TREATING,
    # so the normalizer can extract the underlying symptom for prediction.
    "neem leaf": "Fever",
    "neem leaves": "Fever",
    "neem tea": "Fever",
    "bitter leaf": "Abdominal pain",
    "bitter leaf soup": "Abdominal pain",
    "garlic tea": "Cough",
    "garlic water": "Cough",
    "ginger tea": "Nausea",
    "ginger water": "Nausea",
    "lemon grass": "Fever",
    "lemongrass tea": "Fever",
    "african basil": "Fever",
    "scent leaf": "Fever",
    "moringa": "Fatigue",
    "moringa leaf": "Fatigue",
    "moringa water": "Fatigue",
    "turmeric": "Joint pain",
    "turmeric water": "Joint pain",
    "eucalyptus": "Cough",
    "eucalyptus leaf": "Cough",
    "aloe vera": "Rash",
    "aloe leaf": "Rash",
    "pawpaw leaf": "Fever",
    "papaya leaf": "Fever",
    "guava leaf": "Diarrhea",
    "guava leaf tea": "Diarrhea",
    "bush pepper": "Abdominal pain",
    "black pepper tea": "Cough",
    "coconut water": "Dehydration",
    "eru": "Abdominal pain",
    "njama njama": "Abdominal pain",
    "tonton": "Abdominal pain",
    # ── Francophone African informal phrases ──────────────────────────────────
    "j'ai mal à la tête": "Headache",
    "mal de tête": "Headache",
    "j'ai de la fièvre": "Fever",
    "j'ai chaud": "Fever",
    "j'ai froid": "Chills",
    "j'ai mal au ventre": "Abdominal pain",
    "mal au ventre": "Abdominal pain",
    "j'ai la diarrhée": "Diarrhea",
    "j'ai vomi": "Vomiting",
    "je tousse": "Cough",
    "j'ai mal à la gorge": "Sore throat",
    "yeux jaunes": "Yellow eyes",
    "peau jaune": "Jaundice",
    "j'ai des boutons": "Rash",
    "boutons sur la peau": "Rash",
    "démangeaisons": "Itchy skin",
    "pieds enflés": "Swollen feet",
    "j'urine souvent": "Frequent urination",
    "ça brûle quand j'urine": "Painful urination",
    "j'ai perdu l'appétit": "Loss of appetite",
    "je me sens faible": "Weakness",
    "j'ai les articulations qui font mal": "Joint pain",
}


def _split_on_connectives(text: str) -> list[str]:
    """Split text on common connectives and punctuation.

    Handles English, Pidgin English (Camfranglais), and French connectives.
    Pidgin patterns: 'i get fever and headache', 'belle dey do me and i dey vomit'
    """
    return [
        part.strip()
        for part in re.split(
            r"\band\b|\bwith\b|\balso\b|\bplus\b|\bor\b"
            r"|\bi get\b|\bi dey\b|\bi don\b"  # Pidgin starters — split multi-symptom
            r"|\bet\b|\bavec\b|\baussi\b|\bainsi que\b"  # French connectives
            r"|,|;|\.",
            text.lower()
        )
        if part.strip()
    ]


def _preprocess_pidgin(text: str) -> str:
    """Normalise common Pidgin / Camfranglais constructs before alias matching.

    Removes filler verbs and subject pronouns so 'my head dey pain me'
    can still match the alias 'head dey pain me', etc.
    """
    text = text.lower().strip()
    # Strip leading subject phrases: 'my pikin dey ...' → 'pikin dey ...'
    text = re.sub(r"^(my|the|our|her|his)\s+", "", text)
    # Normalise 'e dey' → remove filler
    text = re.sub(r"\be\s+dey\s+", "", text)
    # 'i have ...' → remove 'i have' so the noun phrase can match
    text = re.sub(r"^(i have|i get|i don get|i dey)\s+", "", text)
    return text.strip()


def normalize_symptom_text(text: str, known_symptoms: list[str]) -> list[str]:
    """
    Parse free-text symptom input and return canonical symptom names.

    Handles:
    - Direct alias lookup (misspellings, informal phrases)
    - Multi-symptom text ("fever and headache, body ache")
    - Fuzzy difflib fallback for novel misspellings

    Args:
        text: Raw user-typed symptom description.
        known_symptoms: List of canonical symptom names from symptoms_list.json.

    Returns:
        Deduplicated list of matched canonical symptom names.
    """
    text = text.lower().strip()
    known_lower = {s.lower(): s for s in known_symptoms}
    found: set[str] = set()

    # 1. Try whole-text alias first (original + pidgin-preprocessed)
    for candidate_text in {text, _preprocess_pidgin(text)}:
        if candidate_text in SYMPTOM_ALIASES:
            canonical = SYMPTOM_ALIASES[candidate_text]
            if canonical in known_symptoms:
                found.add(canonical)
    if found:
        return list(found)

    # 2. Split on connectives, process each part
    parts = _split_on_connectives(text)
    for part in parts:
        if not part:
            continue

        # Also try the pidgin-preprocessed version of each part
        part_variants = {part, _preprocess_pidgin(part)}

        # 2a. Direct alias match
        for pv in part_variants:
            if pv in SYMPTOM_ALIASES:
                canonical = SYMPTOM_ALIASES[pv]
                if canonical in known_symptoms:
                    found.add(canonical)

        if any(pv in SYMPTOM_ALIASES for pv in part_variants):
            continue

        # 2b. Partial alias scan (phrase in part or part in phrase)
        matched_alias = False
        for phrase, canonical in SYMPTOM_ALIASES.items():
            for pv in part_variants:
                if phrase in pv or pv in phrase:
                    if canonical in known_symptoms:
                        found.add(canonical)
                        matched_alias = True

        if matched_alias:
            continue

        # 2c. Fuzzy match against known symptom names
        close = difflib.get_close_matches(part, known_lower.keys(), n=2, cutoff=0.72)
        for match in close:
            found.add(known_lower[match])

    return list(found)


def fuzzy_match_symptom(raw: str, known_symptoms: list[str], cutoff: float = 0.72) -> str | None:
    """
    Match a single raw symptom string to the closest canonical symptom name.

    Returns the best match or None if no close match found.
    """
    raw_lower = raw.lower().strip()
    known_lower = {s.lower(): s for s in known_symptoms}

    # Direct alias
    if raw_lower in SYMPTOM_ALIASES:
        canonical = SYMPTOM_ALIASES[raw_lower]
        if canonical in known_symptoms:
            return canonical

    # Exact match (case-insensitive)
    if raw_lower in known_lower:
        return known_lower[raw_lower]

    # Fuzzy match
    close = difflib.get_close_matches(raw_lower, known_lower.keys(), n=1, cutoff=cutoff)
    if close:
        return known_lower[close[0]]

    return None


def normalize_symptom_list(raw_symptoms: list[str], known_symptoms: list[str]) -> list[str]:
    """
    Normalize a list of symptom strings (may contain misspellings or informal names).

    Each item is matched individually via alias + fuzzy matching, and items that
    are already valid canonical names are kept as-is.
    """
    known_set = set(known_symptoms)
    result: list[str] = []
    seen: set[str] = set()

    for raw in raw_symptoms:
        # Already canonical
        if raw in known_set and raw not in seen:
            result.append(raw)
            seen.add(raw)
            continue

        matched = fuzzy_match_symptom(raw, known_symptoms)
        if matched and matched not in seen:
            result.append(matched)
            seen.add(matched)

    return result
