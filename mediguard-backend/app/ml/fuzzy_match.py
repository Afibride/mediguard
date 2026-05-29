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
    # Based on "An Introduction to Cameroonian Pidgin"
    #   (Peace Corps Cameroon, 1983, 2nd Ed. — Bellama, Nkwele, Yudom)
    #
    # Grammar notes:
    #   "de"  = present-progressive tense marker (TEXTBOOK form)
    #   "dey" = modern/spoken variant — BOTH accepted here
    #   "na"  = is/am/are       "no" = negation
    #   "bin" = past tense      "don" = recently completed
    #   "go"  = future          "a"   = I (subject, textbook)
    #
    # Body vocabulary (textbook spellings):
    #   het / hed = head        bele = stomach/belly    fut = foot/leg
    #   skin = body             ia   = ear              nek = neck
    #   bak  = back             xhes / ches = chest     ai  = eye
    #   tit  = teeth/jaw
    #
    # KEY RULE: "hot" in Pidgin means BOTH temperature AND pain/hurt.
    #   "ma het de hot" → my head hurts (= Headache)
    #   "ma skin de hot" → my body is feverish (skin = body → Fever)
    # ─────────────────────────────────────────────────────────────────────────

    # ── Pain pattern: [body part] de/dey hot ─────────────────────────────────
    # het / hed = head
    "het de hot":          "Headache",
    "hed de hot":          "Headache",
    "ma het de hot":       "Headache",
    "ma hed de hot":       "Headache",
    "het dey hot":         "Headache",
    "hed dey hot":         "Headache",
    "ma het dey hot":      "Headache",
    "ma hed dey hot":      "Headache",
    # bele = stomach/belly
    "bele de hot":         "Abdominal pain",
    "ma bele de hot":      "Abdominal pain",
    "bele dey hot":        "Abdominal pain",
    "ma bele dey hot":     "Abdominal pain",
    # bak = back
    "bak de hot":          "Back pain",
    "ma bak de hot":       "Back pain",
    "bak dey hot":         "Back pain",
    "ma bak dey hot":      "Back pain",
    # fut = foot/leg
    "fut de hot":          "Joint pain",
    "ma fut de hot":       "Joint pain",
    "fut dey hot":         "Joint pain",
    "ma fut dey hot":      "Joint pain",
    # nek = neck
    "nek de hot":          "Neck pain",
    "ma nek de hot":       "Neck pain",
    "nek dey hot":         "Neck pain",
    "ma nek dey hot":      "Neck pain",
    # ia = ear
    "ia de hot":           "Ear pain",
    "ma ia de hot":        "Ear pain",
    "ia dey hot":          "Ear pain",
    "ma ia dey hot":       "Ear pain",
    # xhes / ches = chest
    "xhes de hot":         "Chest pain",
    "ma xhes de hot":      "Chest pain",
    "xhes dey hot":        "Chest pain",
    "ma xhes dey hot":     "Chest pain",
    "ches de hot":         "Chest pain",
    "ma ches de hot":      "Chest pain",
    "ches dey hot":        "Chest pain",
    "ma ches dey hot":     "Chest pain",
    # ai = eye
    "ai de hot":           "Eye pain",
    "ma ai de hot":        "Eye pain",
    "ai dey hot":          "Eye pain",
    "ma ai dey hot":       "Eye pain",
    # tit = teeth / jaw
    "tit de hot":          "Jaw stiffness",
    "ma tit de hot":       "Jaw stiffness",
    "tit dey hot":         "Jaw stiffness",
    "ma tit dey hot":      "Jaw stiffness",
    # skin = body → feverish
    "skin de hot":         "Fever",
    "ma skin de hot":      "Fever",
    "skin dey hot":        "Fever",
    "ma skin dey hot":     "Fever",
    "a skin de hot":       "Fever",

    # ── "hye hot" = to be in pain / feel pain ────────────────────────────────
    "hye hot":             "Muscle aches",
    "a de hye hot":        "Muscle aches",
    "a dey hye hot":       "Muscle aches",
    "a de hye hot plenti": "Severe headache",
    "body de hye hot":     "Muscle aches",
    "body dey hye hot":    "Muscle aches",
    "bodi de hye hot":     "Muscle aches",

    # ── Head / neurological (de + dey) ───────────────────────────────────────
    "ma het de pain mi":     "Headache",
    "het de pain mi":        "Headache",
    "het de do mi":          "Headache",
    "ma het de do mi":       "Headache",
    "ma het de beat":        "Severe headache",
    "het de beat mi":        "Severe headache",
    "a de feba":             "Fever",
    "a de fiba":             "Fever",
    "ma het de spin":        "Dizziness",
    "het de spin":           "Dizziness",
    "a de reel":             "Dizziness",
    "a de spin":             "Dizziness",
    "ma ai no de si wel":    "Blurred vision",
    "ai de blor":            "Blurred vision",
    # dey variants (existing + new)
    "my head dey pain me":   "Headache",
    "head dey pain me":      "Headache",
    "my head dey do me":     "Headache",
    "head dey do me":        "Headache",
    "my head dey hot":       "Fever",
    "head dey pain":         "Headache",
    "e dey pain my head":    "Headache",
    "e dey beat for my head":"Severe headache",
    "my head dey spin":      "Dizziness",
    "head dey spin":         "Dizziness",
    "i dey feel dizzy":      "Dizziness",
    "my eye dey blur":       "Blurred vision",
    "my eye no dey see well":"Blurred vision",

    # ── Fever / temperature ───────────────────────────────────────────────────
    "a de hot trong trong":  "High fever",
    "a de hot strong strong":"High fever",
    "feba de kai":           "High fever",
    "feba de bad":           "High fever",
    "a de hot for bodi":     "Fever",
    "a de hot for skin":     "Fever",
    "a de bad for skin":     "Fever",
    # dey variants (existing)
    "my body dey hot":       "Fever",
    "body dey hot":          "Fever",
    "i get fever":           "Fever",
    "i get hot body":        "Fever",
    "e dey hot for body":    "Fever",
    "body hot":              "Fever",

    # ── Chills / kol ─────────────────────────────────────────────────────────
    "a de hye kol":          "Chills",
    "a dey hye kol":         "Chills",
    "a de shake for kol":    "Chills",
    "a de shiver":           "Chills",
    "bodi de shake for kol": "Chills",
    "a de kol":              "Chills",
    "a de kol for bodi":     "Chills",
    # dey variants (existing)
    "i dey shake for cold":  "Chills",
    "i dey shiver":          "Chills",
    "my body dey shake":     "Chills",

    # ── Fatigue / weakness — "taya" = tired (textbook) ───────────────────────
    "a de taya":             "Fatigue",
    "a dey taya":            "Fatigue",
    "a taya plenti":         "Fatigue",
    "a taya bad bad":        "Fatigue",
    "a de taya plenti":      "Fatigue",
    "bodi de taya mi":       "Fatigue",
    "body de taya mi":       "Fatigue",
    "a no get paoa":         "Weakness",
    "a no get pawa":         "Weakness",
    "a no get stren":        "Weakness",
    "a no fit stan":         "Weakness",
    "a de dray":             "Weight loss",   # dray = thin/pale (textbook)
    "a don dray":            "Weight loss",
    "a de fas":              "Weakness",
    "a get bodi pain":       "Muscle aches",
    "a de pein for skin":    "Muscle aches",
    # dey variants (existing)
    "my body dey tire me":   "Fatigue",
    "body dey tire me":      "Fatigue",
    "i dey feel weak":       "Weakness",
    "i no get strength":     "Weakness",
    "body weak":             "Weakness",
    "i dey tire":            "Fatigue",
    "i no fit stand":        "Weakness",
    "my body dey pain me":   "Muscle aches",
    "body dey pain me":      "Muscle aches",

    # ── General sickness — "a no fayn" / "a no wel" ───────────────────────────
    "a no fayn":             "Fatigue",
    "a no fayn at ol":       "Fatigue",
    "a no wel":              "Fatigue",
    "a sik":                 "Fatigue",
    "a de sik":              "Fatigue",
    "a bin sik":             "Fatigue",
    "a don sik":             "Fatigue",
    "a de sik bad":          "Fatigue",
    "i no fayn":             "Fatigue",
    "i no wel":              "Fatigue",
    "bodi no fayn":          "Fatigue",
    "a neba fayn":           "Fatigue",
    "a no fayn bifo":        "Fatigue",
    "a no fayn nawa":        "Fatigue",
    "a de sik nawa":         "Fatigue",
    "a bin sik fo hous":     "Fatigue",

    # ── Stomach / gastrointestinal — "bele" = textbook spelling ──────────────
    "ma bele de do mi":          "Abdominal pain",
    "bele de do mi":             "Abdominal pain",
    "bele de pain mi":           "Abdominal pain",
    "ma bele de pain mi":        "Abdominal pain",
    "bele de ran":               "Diarrhea",
    "ma bele de ran":            "Diarrhea",
    "a de purge":                "Diarrhea",
    "a dey purge":               "Diarrhea",
    "a de purge bad":            "Diarrhea",
    "a de purge trong":          "Diarrhea",
    "a de purge strong":         "Diarrhea",
    "a noba chop":               "Loss of appetite",   # noba = never/haven't
    "a no fit chop":             "Loss of appetite",
    "a no wan chop":             "Loss of appetite",
    "chop no swit mi":           "Loss of appetite",
    "a no de chop":              "Loss of appetite",
    "a de vom":                  "Vomiting",
    "a don vom":                 "Vomiting",
    "wata wata stul":            "Diarrhea",
    "wata stul":                 "Diarrhea",
    "stul de com anyhau":        "Diarrhea",
    "blod for stul":             "Bloody or mucus-filled diarrhea",
    "a de sik fo beli":          "Abdominal pain",
    # bele with dey (also accept older "belle" spelling)
    "bele dey do me":            "Abdominal pain",
    "belle dey do me":           "Abdominal pain",
    "my belle dey do me":        "Abdominal pain",
    "my bele dey do me":         "Abdominal pain",
    "stomach dey do me":         "Abdominal pain",
    "my stomach dey pain me":    "Abdominal pain",
    "belly dey pain me":         "Abdominal pain",
    "i get stomach pain":        "Abdominal pain",
    "i dey vomit":               "Vomiting",
    "i dey vomit since yesterday":"Vomiting",
    "i dey purge":               "Diarrhea",
    "i get purge":               "Diarrhea",
    "running stomach":           "Diarrhea",
    "my stomach dey run":        "Diarrhea",
    "stool dey come anyhow":     "Diarrhea",
    "watery poo-poo":            "Diarrhea",
    "watery poo poo":            "Diarrhea",
    "blood for poo-poo":         "Bloody or mucus-filled diarrhea",
    "blood for stool":           "Bloody or mucus-filled diarrhea",
    "i no wan eat":              "Loss of appetite",
    "i no dey hungry":           "Loss of appetite",
    "food no dey sweet me":      "Loss of appetite",
    "i no fit eat":              "Loss of appetite",
    "my pikin no dey eat":       "Loss of appetite",

    # ── Cough / respiratory — "kof" = textbook, "bref" = breath ─────────────
    "a de kof":                  "Cough",
    "a dey kof":                 "Cough",
    "a de kof trong trong":      "Chronic cough",
    "a de kof strong strong":    "Chronic cough",
    "a don kof ovatem":          "Chronic cough",
    "kof de worry mi":           "Chronic cough",
    "a no fit bref wel":         "Shortness of breath",
    "a no fit bref":             "Shortness of breath",
    "bref de shot mi":           "Shortness of breath",
    "ma xhes de pain mi":        "Chest pain",
    "xhes de pain mi":           "Chest pain",
    "ma ches de pain mi":        "Chest pain",
    "xhes de tight":             "Chest tightness",
    "a de hwiz":                 "Wheezing",
    "a de wheez":                "Wheezing",
    "ma nek de pain mi":         "Sore throat",
    "nek de pain mi":            "Sore throat",
    "noz de ran":                "Runny nose",
    "ma noz de ran":             "Runny nose",
    # dey variants (existing)
    "i dey cough":               "Cough",
    "i get cough":               "Cough",
    "strong cough":              "Chronic cough",
    "cough dey worry me":        "Chronic cough",
    "i no fit breathe well":     "Shortness of breath",
    "breath dey short me":       "Shortness of breath",
    "chest dey pain me":         "Chest pain",
    "my chest dey pain me":      "Chest pain",
    "chest dey tight":           "Chest tightness",
    "i dey wheeze":              "Wheezing",
    "throat dey pain me":        "Sore throat",
    "my throat dey pain me":     "Sore throat",
    "nose dey run":              "Runny nose",
    "my nose dey run":           "Runny nose",

    # ── Eyes / skin (ai = eye, skin = body) ──────────────────────────────────
    "ma ai de yelo":             "Yellow eyes",
    "ai de yelo":                "Yellow eyes",
    "skin de yelo":              "Jaundice",
    "ma skin de yelo":           "Jaundice",
    "skin de scratch mi":        "Itchy skin",
    "ma skin de scratch mi":     "Itchy skin",
    "skin de itch mi":           "Itchy skin",
    "a get rash for skin":       "Rash",
    "ai de red":                 "Red eyes",
    "ma ai de red":              "Red eyes",
    "ai de wata":                "Eye discharge",
    "ma ai de wata":             "Eye discharge",
    "ai de yelo":                "Yellow eyes",
    # dey variants (existing)
    "my eye dey yellow":         "Yellow eyes",
    "eye dey yellow":            "Yellow eyes",
    "yellow eye":                "Yellow eyes",
    "skin dey yellow":           "Jaundice",
    "my skin dey yellow":        "Jaundice",
    "i get rash for skin":       "Rash",
    "rash dey my body":          "Rash",
    "skin dey itch me":          "Itchy skin",
    "my skin dey itch me":       "Itchy skin",
    "body dey itch me":          "Itchy skin",
    "skin dey scratch":          "Itchy skin",
    "eye dey red":               "Red eyes",
    "my eye dey red":            "Red eyes",
    "eye discharge":             "Eye discharge",

    # ── Urinary / reproductive ────────────────────────────────────────────────
    "a de pis plenti":           "Frequent urination",
    "pis de pain mi":            "Painful urination",
    "blod for pis":              "Blood in urine",
    "pis de dak":                "Dark urine",
    # dey variants (existing)
    "i dey urinate too much":    "Frequent urination",
    "pee dey pain me":           "Painful urination",
    "piss dey pain me":          "Painful urination",
    "urine dey pain me":         "Painful urination",
    "blood for urine":           "Blood in urine",
    "dark urine":                "Dark urine",

    # ── Joints / bones / muscles ──────────────────────────────────────────────
    "joynt de pain mi":          "Joint pain",
    "ma joynt de pain mi":       "Joint pain",
    "bon de pain mi":            "Joint pain",
    "wes de pain mi":            "Back pain",
    "ma wes de pain mi":         "Back pain",
    "nek stif":                  "Stiff neck",
    "ma nek stif":               "Stiff neck",
    "ma nek de stif":            "Stiff neck",
    # dey variants (existing)
    "joint dey pain me":         "Joint pain",
    "my joint dey pain me":      "Joint pain",
    "bone dey pain me":          "Joint pain",
    "waist dey pain me":         "Back pain",
    "my waist dey pain me":      "Back pain",
    "neck stiff":                "Stiff neck",
    "my neck stiff":             "Stiff neck",

    # ── Child-specific Pidgin — pikin / smol pikin ────────────────────────────
    # "de" (textbook) forms
    "ma pikin de hot":           "Fever",
    "pikin de hot":              "Fever",
    "ma pikin skin de hot":      "Fever",
    "pikin skin de hot":         "Fever",
    "ma pikin de shake":         "Chills",
    "pikin de shake":            "Chills",
    "ma pikin de taya":          "Fatigue",
    "pikin de taya":             "Fatigue",
    "ma pikin no fit chop":      "Loss of appetite",
    "pikin no fit chop":         "Loss of appetite",
    "pikin no wan chop":         "Loss of appetite",
    "ma pikin de kof":           "Cough",
    "pikin de kof":              "Cough",
    "ma pikin de vomit":         "Vomiting",
    "pikin de vomit":            "Vomiting",
    "pikin de vom":              "Vomiting",
    "ma pikin de purge":         "Diarrhea",
    "pikin de purge":            "Diarrhea",
    "smol pikin de hot":         "Fever",
    "smol pikin de kof":         "Cough",
    "smol pikin de purge":       "Diarrhea",
    "pikin nek stif":            "Stiff neck",
    "ma pikin nek stif":         "Stiff neck",
    "pikin ai de yelo":          "Yellow eyes",
    "pikin fit":                 "Seizures",        # "fit" = convulsion/seizure
    "ma pikin fit":              "Seizures",
    "pikin get fit":             "Seizures",
    "pikin de shake trong":      "Seizures",
    "pikin de shake strong":     "Seizures",
    "ma pikin de shake trong":   "Seizures",
    "pikin no sabi":             "Confusion",       # "no sabi" = doesn't know/confused
    "pikin no de tok":           "Confusion",
    # "dey" forms (existing + new)
    "my pikin dey hot":          "Fever",
    "pikin dey shake":           "Chills",
    "pikin body hot":            "Fever",
    "my pikin dey cry":          "Abdominal pain",
    "pikin no dey sleep":        "Fatigue",
    "my pikin dey vomit":        "Vomiting",
    "pikin dey purge":           "Diarrhea",
    "pikin get rash":            "Rash",
    "pikin neck stiff":          "Stiff neck",
    "pikin eye dey yellow":      "Yellow eyes",
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

    # ── New French aliases ────────────────────────────────────────────────────
    "fièvre":                        "Fever",
    "j'ai de la fièvre":             "Fever",
    "température élevée":            "Fever",
    "mal à la tête":                 "Headache",
    "céphalée":                      "Headache",
    "céphalées":                     "Headache",
    "toux":                          "Cough",
    "je tousse beaucoup":            "Cough",
    "toux persistante":              "Chronic cough",
    "toux chronique":                "Chronic cough",
    "douleur thoracique":            "Chest pain",
    "douleur à la poitrine":         "Chest pain",
    "essoufflement":                 "Shortness of breath",
    "difficultés à respirer":        "Shortness of breath",
    "mal à respirer":                "Shortness of breath",
    "nausées":                       "Nausea",
    "vomissements":                  "Vomiting",
    "diarrhée":                      "Diarrhea",
    "ventre qui fait mal":           "Abdominal pain",
    "douleur abdominale":            "Abdominal pain",
    "crampes abdominales":           "Abdominal pain",
    "fatigue":                       "Fatigue",
    "je suis fatigué":               "Fatigue",
    "épuisement":                    "Fatigue",
    "faiblesse":                     "Weakness",
    "frissons":                      "Chills",
    "transpiration":                 "Sweating",
    "sueurs nocturnes":              "Night sweats",
    "perte de poids":                "Weight loss",
    "perte d'appétit":               "Loss of appetite",
    "ganglions enflés":              "Swollen lymph nodes",
    "ganglions gonflés":             "Swollen lymph nodes",
    "éruption cutanée":              "Rash",
    "démangeaisons cutanées":        "Itchy skin",
    "peau qui gratte":               "Itchy skin",
    "yeux rouges":                   "Red eyes",
    "écoulement des yeux":           "Eye discharge",
    "maux de gorge":                 "Sore throat",
    "gorge qui fait mal":            "Sore throat",
    "nez qui coule":                 "Runny nose",
    "éternuements":                  "Sneezing",
    "constipation":                  "Constipation",
    "douleur articulaire":           "Joint pain",
    "douleurs musculaires":          "Muscle aches",
    "raideur de la nuque":           "Stiff neck",
    "nuque raide":                   "Stiff neck",
    "sang dans les urines":          "Blood in urine",
    "urines foncées":                "Dark urine",
    "urines sombres":                "Dark urine",
    "brûlures urinaires":            "Painful urination",
    "douleur en urinant":            "Painful urination",
    "uriner souvent":                "Frequent urination",
    "uriner fréquemment":            "Frequent urination",
    "saignements rectaux":           "Rectal bleeding",
    "saignement par l'anus":         "Rectal bleeding",
    "sang dans les selles":          "Rectal bleeding",
    "douleur à l'anus":              "Anal pain",
    "démangeaisons à l'anus":        "Anal itching",
    "hémorroïdes":                   "Swelling near anus",
    "hémorroide":                    "Swelling near anus",
    "vers intestinaux":              "Anal itching",
    "parasites intestinaux":         "Anal itching",
    "vertige":                       "Dizziness",
    "étourdissements":               "Dizziness",
    "confusion":                     "Confusion",
    "convulsions":                   "Seizures",
    "crises d'épilepsie":            "Seizures",
    "jaunisse":                      "Jaundice",
    "peau jaune":                    "Jaundice",
    "ictère":                        "Jaundice",
    "mal aux dents":                 "Tooth pain",
    "douleur dentaire":              "Tooth pain",
    "gonflement de la mâchoire":     "Jaw swelling",
    "abcès dentaire":                "Tooth pain",
    "paludisme":                     "Fever",           # French: malaria => map to primary symptom
    "j'ai le paludisme":             "Fever",

    # ── Hemorrhoids / Piles (English) ─────────────────────────────────────────
    "pile":                          "Swelling near anus",
    "piles":                         "Swelling near anus",
    "haemorrhoid":                   "Swelling near anus",
    "haemorrhoids":                  "Swelling near anus",
    "hemorrhoid":                    "Swelling near anus",
    "hemorrhoids":                   "Swelling near anus",
    "rectal bleeding":               "Rectal bleeding",
    "bleeding from anus":            "Rectal bleeding",
    "blood in stool":                "Rectal bleeding",
    "blood when passing stool":      "Rectal bleeding",
    "blood in poo":                  "Rectal bleeding",
    "blood after stooling":          "Rectal bleeding",
    "bleeding during bowel movement": "Rectal bleeding",
    "anal pain":                     "Anal pain",
    "pain in anus":                  "Anal pain",
    "pain near anus":                "Anal pain",
    "pain around anus":              "Anal pain",
    "pain when passing stool":       "Pain during bowel movement",
    "painful bowel movement":        "Pain during bowel movement",
    "painful stooling":              "Pain during bowel movement",
    "anal itching":                  "Anal itching",
    "itching around anus":           "Anal itching",
    "itching near anus":             "Anal itching",
    "anus itching":                  "Anal itching",
    "bottom itching":                "Anal itching",
    "itchy bottom":                  "Anal itching",
    "swelling near anus":            "Swelling near anus",
    "lump near anus":                "Swelling near anus",
    "lump around anus":              "Swelling near anus",
    "swollen anus":                  "Swelling near anus",
    "mucus in stool":                "Mucus discharge from anus",
    "mucus discharge":               "Mucus discharge from anus",
    "slime in poo":                  "Mucus discharge from anus",

    # ── Intestinal worms (English) ────────────────────────────────────────────
    "worms":                         "Anal itching",
    "intestinal worms":              "Anal itching",
    "roundworm":                     "Anal itching",
    "tapeworm":                      "Anal itching",
    "hookworm":                      "Anal itching",
    "pinworm":                       "Anal itching",
    "threadworm":                    "Anal itching",
    "worms in stool":                "Visible worms in stool",
    "worms in poo":                  "Visible worms in stool",
    "worms in toilet":               "Visible worms in stool",
    "seeing worms":                  "Visible worms in stool",

    # ── Rectal / anal symptom natural language ───────────────────────────────
    "pain near my anus":             "Anal pain",
    "pain around anus":              "Anal pain",
    "pain near anus":                "Anal pain",
    "pain in my bottom":             "Anal pain",
    "pain in bottom":                "Anal pain",
    "bottom pain":                   "Anal pain",
    "see blood when i pass stool":   "Rectal bleeding",
    "blood when i pass stool":       "Rectal bleeding",
    "blood when passing stool":      "Rectal bleeding",
    "blood on toilet paper":         "Rectal bleeding",
    "bleed when i poo":              "Rectal bleeding",
    "bleed when defecating":         "Rectal bleeding",
    "blood after toilet":            "Rectal bleeding",
    "blood after passing stool":     "Rectal bleeding",
    "blood in toilet":               "Rectal bleeding",
    "swelling near anus":            "Swelling near anus",
    "swelling near my anus":         "Swelling near anus",
    "lump near anus":                "Swelling near anus",
    "lump in my bottom":             "Swelling near anus",
    "pain when i pass stool":        "Pain during bowel movement",
    "pain during bowel movement":    "Pain during bowel movement",
    "painful to pass stool":         "Pain during bowel movement",
    "itchy near anus":               "Anal itching",
    "itching near anus":             "Anal itching",
    # ── Pidgin: piles / anus / worms ─────────────────────────────────────────
    "i get pain for yansh":          "Anal pain",
    "a get pain for yansh":          "Anal pain",
    "yansh de pain mi":              "Anal pain",
    "yansh dey pain me":             "Anal pain",
    "pain for yansh area":           "Anal pain",
    "yansh dey itch":                "Anal itching",
    "yansh de itch mi":              "Anal itching",
    "blood dey come from yansh":     "Rectal bleeding",
    "blood for yansh":               "Rectal bleeding",
    "blood dey come when a do toilet": "Rectal bleeding",
    "blood when i stool":            "Rectal bleeding",
    "a see blood for toilet":        "Rectal bleeding",
    "i see blood for toilet":        "Rectal bleeding",
    "swelling for yansh":            "Swelling near anus",
    "yansh swell":                   "Swelling near anus",
    "worm dey for bele":             "Anal itching",
    "i get worm":                    "Anal itching",
    "worm dey for poo":              "Visible worms in stool",
    "ma pikin get worm":             "Anal itching",
    "pikin get worm":                "Anal itching",

    # ── Pidgin: dental / teeth ────────────────────────────────────────────────
    "tit de pain mi":                "Tooth pain",
    "tit dey pain me":               "Tooth pain",
    "tooth de pain mi":              "Tooth pain",
    "my tooth dey pain me":          "Tooth pain",
    "jaw dey pain me":               "Jaw swelling",
    "jaw swell":                     "Jaw swelling",

    # ── Visible worms in stool (new symptom) ─────────────────────────────────
    "visible worms in stool":        "Visible worms in stool",
    "visible worms":                 "Visible worms in stool",

    # ── Eczema / skin dryness ────────────────────────────────────────────────
    "dry skin":                      "Dry skin",
    "skin peeling":                  "Skin peeling",
    "cracked skin":                  "Dry skin",
    "flaky skin":                    "Skin peeling",
    "eczema":                        "Itchy skin",
    "dermatitis":                    "Itchy skin",

    # ── Malnutrition ─────────────────────────────────────────────────────────
    "poor wound healing":            "Poor wound healing",
    "wounds not healing":            "Poor wound healing",
    "hair falling out":              "Hair loss",
    "hair loss":                     "Hair loss",
    "hair thinning":                 "Hair loss",

    # ── Arthritis ────────────────────────────────────────────────────────────
    "joint swelling":                "Joint swelling",
    "swollen joints":                "Joint swelling",
    "stiff joints":                  "Stiffness",
    "joint stiffness":               "Stiffness",
    "reduced range of motion":       "Reduced range of motion",
    "can't move joint":              "Reduced range of motion",

    # ── Schistosomiasis / Bilharzia ───────────────────────────────────────────
    "blood in urine":                "Blood in urine",
    "blood in my urine":             "Blood in urine",
    "red urine":                     "Blood in urine",
    "pink urine":                    "Blood in urine",
    "urine with blood":              "Blood in urine",
    "blood when urinating":          "Blood in urine",
    "blood in pee":                  "Blood in urine",
    "hematuria":                     "Blood in urine",
    "haematuria":                    "Blood in urine",
    "blood in stool":                "Blood in stool",
    "blood in my stool":             "Blood in stool",
    "blood in poo":                  "Blood in stool",
    "bloody stool":                  "Blood in stool",
    "swimmers itch":                 "Itchy skin",
    "water itch":                    "Itchy skin",
    # Pidgin: bilharzia / blood in urine
    "blood dey for urine":           "Blood in urine",
    "blood for ma urine":            "Blood in urine",
    "urine red":                     "Blood in urine",
    "a de urinate blood":            "Blood in urine",

    # ── Mpox / Monkeypox ─────────────────────────────────────────────────────
    "pustular rash":                 "Rash",
    "pox lesions":                   "Skin sores",
    "pus-filled rash":               "Rash",
    "monkey pox rash":               "Rash",
    "pox blisters":                  "Blisters",

    # ── Rabies ────────────────────────────────────────────────────────────────
    "hydrophobia":                   "Hydrophobia",
    "fear of water":                 "Hydrophobia",
    "cannot swallow water":          "Hydrophobia",
    "scared of water":               "Hydrophobia",
    "agitation":                     "Agitation",
    "very agitated":                 "Agitation",
    "dog bite":                      "Agitation",
    "bitten by dog":                 "Agitation",
    # Pidgin: rabies / dog bite
    "dog bite me":                   "Agitation",
    "dog don bite me":               "Agitation",
    "i fear water":                  "Hydrophobia",

    # ── African Trypanosomiasis / Sleeping Sickness ───────────────────────────
    "excessive sleepiness":          "Excessive sleepiness",
    "sleeping all the time":         "Excessive sleepiness",
    "always sleeping":               "Excessive sleepiness",
    "cannot stay awake":             "Excessive sleepiness",
    "falling asleep during day":     "Excessive sleepiness",
    "day sleeping":                  "Excessive sleepiness",
    "sleep too much":                "Excessive sleepiness",
    "swollen neck glands":           "Swollen lymph nodes",
    "neck glands swollen":           "Swollen lymph nodes",
    # Pidgin: sleeping sickness
    "a de sleep plenti":             "Excessive sleepiness",
    "a dey sleep plenti":            "Excessive sleepiness",
    "sleep no fit leave me":         "Excessive sleepiness",
    "neck swell":                    "Swollen lymph nodes",

    # ── Cellulitis ────────────────────────────────────────────────────────────
    "skin redness":                  "Skin redness",
    "red skin":                      "Skin redness",
    "skin red and warm":             "Skin redness",
    "skin turning red":              "Skin redness",
    "skin warmth":                   "Skin warmth",
    "warm skin":                     "Skin warmth",
    "hot skin area":                 "Skin warmth",
    "spreading redness":             "Skin redness",
    "redness spreading":             "Skin redness",

    # ── Stroke ────────────────────────────────────────────────────────────────
    "speech difficulty":             "Speech difficulty",
    "difficulty speaking":           "Speech difficulty",
    "cannot speak":                  "Speech difficulty",
    "slurred speech":                "Speech difficulty",
    "trouble speaking":              "Speech difficulty",
    "cannot talk properly":          "Speech difficulty",
    "words not coming out":          "Speech difficulty",
    "facial drooping":               "Facial drooping",
    "face drooping":                 "Facial drooping",
    "face falling":                  "Facial drooping",
    "mouth drooping":                "Facial drooping",
    "one side face numb":            "Facial drooping",
    "sudden weakness":               "Weakness",
    "arm weakness":                  "Weakness",
    "one side weak":                 "Weakness",
    "loss of balance":               "Dizziness",
    "cannot balance":                "Dizziness",
    # Pidgin: stroke
    "mouth fall one side":           "Facial drooping",
    "mouth de fall":                 "Facial drooping",
    "a no fit tok":                  "Speech difficulty",
    "i no fit tok":                  "Speech difficulty",
    "i no fit waka":                 "Weakness",

    # ── Heart Failure ─────────────────────────────────────────────────────────
    "legs swollen":                  "Ankle swelling",
    "swollen legs":                  "Ankle swelling",
    "leg swelling":                  "Ankle swelling",
    "feet swelling":                 "Ankle swelling",
    "cannot breathe lying down":     "Shortness of breath",
    "breathless at night":           "Shortness of breath",
    "wake up breathless":            "Shortness of breath",
    "palpitations":                  "Fast heartbeat",
    "heart racing":                  "Fast heartbeat",
    "heart pounding":                "Fast heartbeat",
    # Pidgin: heart failure
    "fut swell":                     "Ankle swelling",
    "leg swell":                     "Ankle swelling",
    "a no fit breathe":              "Shortness of breath",

    # ── Hypothyroidism / Goitre ──────────────────────────────────────────────
    "cold intolerance":              "Cold intolerance",
    "always feeling cold":           "Cold intolerance",
    "feeling cold all the time":     "Cold intolerance",
    "cannot tolerate cold":          "Cold intolerance",
    "goiter":                        "Swollen lymph nodes",
    "goitre":                        "Swollen lymph nodes",
    "neck swelling":                 "Swollen lymph nodes",
    "swollen neck":                  "Swollen lymph nodes",
    "thyroid swelling":              "Swollen lymph nodes",
    "weight gain":                   "Weight gain",
    "gaining weight":                "Weight gain",
    "unexplained weight gain":       "Weight gain",
    # Pidgin: thyroid / goitre
    "nek swell":                     "Swollen lymph nodes",
    "a de gain weight":              "Weight gain",

    # ── COVID-19 ─────────────────────────────────────────────────────────────
    "loss of taste":                 "Loss of taste",
    "cannot taste food":             "Loss of taste",
    "food has no taste":             "Loss of taste",
    "no taste":                      "Loss of taste",
    "lost my taste":                 "Loss of taste",
    "loss of smell":                 "Loss of smell",
    "cannot smell":                  "Loss of smell",
    "lost my smell":                 "Loss of smell",
    "no smell":                      "Loss of smell",
    "anosmia":                       "Loss of smell",
    "ageusia":                       "Loss of taste",
    # Pidgin: covid
    "a no fit smell":                "Loss of smell",
    "a no fit taste chop":           "Loss of taste",
    "food no get taste":             "Loss of taste",

    # ── Candidiasis / Thrush ─────────────────────────────────────────────────
    "white patches in mouth":        "White patches in mouth",
    "white spots in mouth":          "White patches in mouth",
    "white coating on tongue":       "White patches in mouth",
    "oral thrush":                   "White patches in mouth",
    "mouth thrush":                  "White patches in mouth",
    "white tongue":                  "White patches in mouth",
    "yeast infection":               "Vaginal itching",
    "vaginal thrush":                "Vaginal itching",
    # Pidgin: candidiasis
    "white tin for mouth":           "White patches in mouth",
    "white for tongue":              "White patches in mouth",
}


def _split_on_connectives(text: str) -> list[str]:
    """Split text on common connectives and punctuation.

    Handles English, Pidgin English (Camfranglais), and French connectives.
    Pidgin patterns:
      'i get fever and headache'
      'bele de do mi an a de kof'          (an = and, textbook)
      'a de hot wit headache'              (wit = with)
      'a dey vomit and i dey purge'
    """
    return [
        part.strip()
        for part in re.split(
            r"\band\b|\bwith\b|\balso\b|\bplus\b|\bor\b"
            r"|\bi get\b|\bi dey\b|\bi don\b|\bi de\b"   # Pidgin: I-starters
            r"|\ba de\b|\ba dey\b|\ba don\b|\ba bin\b"   # textbook "a" subject
            r"|\bwit\b|\ban\b"                            # Pidgin "with" / "and"
            r"|\bet\b|\bavec\b|\baussi\b|\bainsi que\b"  # French connectives
            r"|,|;|\.",
            text.lower()
        )
        if part.strip()
    ]


def _preprocess_pidgin(text: str) -> str:
    """Normalise Pidgin / Camfranglais constructs before alias matching.

    Based on "An Introduction to Cameroonian Pidgin" (Peace Corps Cameroon, 1983).
    Removes filler subject pronouns and tense markers so bare phrases can match
    alias entries regardless of which tense form the user typed.

    Examples:
      'a de taya plenti'         → 'taya plenti'
      'ma het de hot'            → 'het de hot'
      'my pikin dey purge'       → 'pikin dey purge'
      'i have a fever'           → 'a fever'  (then → 'fever')
    """
    text = text.lower().strip()

    # ── Textbook possessives: "ma" (my), "ya" (your) ─────────────────────────
    # Strip leading "ma" / "ya" so 'ma het de hot' → 'het de hot'
    text = re.sub(r"^(ma|ya)\s+", "", text)

    # ── English possessives ───────────────────────────────────────────────────
    # 'my pikin dey ...' → 'pikin dey ...'
    text = re.sub(r"^(my|the|our|her|his)\s+", "", text)

    # ── Filler subject + tense — textbook "a de/dey/don/bin" ─────────────────
    # 'a de kof' → 'kof', 'a dey purge' → 'purge'
    text = re.sub(r"^(a|i)\s+(de|dey|don|bin|go)\s+", "", text)

    # ── "e dey" filler (3rd-person impersonal) ────────────────────────────────
    text = re.sub(r"\be\s+(dey|de)\s+", "", text)

    # ── English "i have / i get / i dey" starters ────────────────────────────
    text = re.sub(r"^(i have|i get|i don get|i dey|i de)\s+", "", text)

    # ── Trailing object pronoun "mi" / "me" — 'pain mi' stays, but if after
    #    stripping subject the phrase is just a verb + mi, keep verb only ──────
    # e.g. 'pain mi' → keep (so aliases like 'het de pain mi' still match);
    # we only remove trailing "me" on bare verbs like 'tire me', 'do me'
    text = re.sub(r"\s+(me|mi)$", "", text)

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
