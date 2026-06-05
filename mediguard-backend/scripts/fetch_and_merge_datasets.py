"""
fetch_and_merge_datasets.py
============================
Downloads real patient-diagnosis datasets from Kaggle and merges them
into MediGuard's binary symptom format, then retrains all models.

DATASETS USED
─────────────
1. kaushil268/disease-prediction-using-machine-learning
   • 42 diseases, 132 binary symptom columns, ~5 000 patient rows
   • Direct binary format — highest compatibility with MediGuard

2. dhivyeshrk/diseases-and-symptoms-dataset
   • 773 diseases, 377 symptoms, 246 000+ rows
   • Text-format symptoms — mapped to MediGuard schema

3. noeyislearning/disease-prediction-based-on-symptoms
   • 42 diseases, pre-split train/test CSV
   • Alternate version of dataset 1 (extra coverage)

SETUP
─────
1. Install the Kaggle CLI:
       pip install kaggle

2. Create a Kaggle API token:
       kaggle.com → Account → API → "Create New API Token"
       This downloads kaggle.json.

3. Place it at one of:
       Windows : C:\\Users\\<you>\\.kaggle\\kaggle.json
       Linux/Mac: ~/.kaggle/kaggle.json

4. Run from mediguard-backend/ root:
       python scripts/fetch_and_merge_datasets.py

   Optional flags:
       --skip-download   Use already-downloaded zips in data/external/
       --no-synthetic    Exclude the existing synthetic data; use real only
       --real-only       Alias for --no-synthetic

OUTPUTS
───────
   data/external/           raw downloaded zips
   data/raw/mediguard_dataset_full.csv
   data/processed/mediguard_train.csv
   data/processed/mediguard_test.csv
   models/random_forest.pkl
   models/decision_tree.pkl
   models/naive_bayes.pkl
   models/label_encoder.pkl
"""

import argparse
import csv
import io
import json
import math
import os
import pickle
import random
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.ml.simple_model import SimpleLabelEncoder, SimpleSymptomModel  # noqa: E402

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

BASE = Path(__file__).parent.parent

# ── MediGuard master symptom list (keep in sync with build_real_dataset.py) ──
ALL_SYMPTOMS = [
    "Fever", "Chills", "Sweating", "Headache", "Nausea", "Vomiting",
    "Muscle aches", "Fatigue", "Prolonged fever", "Weakness", "Abdominal pain",
    "Constipation", "Diarrhea", "Rose spots", "Runny nose", "Sore throat",
    "Cough", "Sneezing", "Mild fever", "Chest pain", "Shortness of breath",
    "Profuse watery diarrhea", "Muscle cramps", "Rapid dehydration",
    "Low blood pressure", "Frequent urination", "Painful urination",
    "Pelvic pain", "Blood in urine", "Lower abdominal pain",
    "Bloody or mucus-filled diarrhea", "Tenesmus", "Dehydration", "Dizziness",
    "Blurred vision", "Chronic cough", "Coughing up blood", "Night sweats",
    "Weight loss", "Increased thirst", "Slow-healing sores", "Pale skin",
    "Fast heartbeat", "Itchy skin", "Ring-shaped rash", "Red scaly skin",
    "Cracked skin", "Skin peeling", "High fever", "Severe headache",
    "Pain behind eyes", "Joint pain", "Rash", "Mild bleeding", "Itchy rash",
    "Blisters", "Loss of appetite", "Wheezing", "Chest tightness",
    "Burning stomach pain", "Bloating", "Heartburn", "Red eyes", "Koplik spots",
    "Sudden high fever", "Stiff neck", "Confusion", "Sensitivity to light",
    "Severe itching", "Burrow tracks", "Skin sores", "Night itching",
    "Back pain", "Body weakness", "Body aches", "Dry mouth", "Sunken eyes",
    "Reduced urination", "Low appetite", "Sleep disturbances", "Numbness",
    "Sensitivity to sound", "Neck pain", "Seizures", "Difficulty walking",
    "Poor coordination", "Swollen lymph nodes", "Jaundice", "Yellow eyes",
    "Dark urine", "Abdominal swelling", "Sore muscles", "Eye pain",
    "Nose bleeding", "Gum bleeding", "Skin lesions", "Pus or discharge",
    "White patches in mouth", "Vaginal discharge", "Vaginal itching",
    "Vaginal bleeding", "Missed period", "Breast pain", "Nipple discharge",
    "Pain during intercourse", "Visible worms in stool", "Anal itching",
    "Weight gain", "Swollen feet", "Ankle swelling", "Excessive sweating",
    "Cold intolerance", "Heat intolerance", "Tremor", "Anxiety", "Irritability",
    "Confusion at night", "Jaw stiffness", "Ear pain", "Hearing loss",
    "Hoarse voice", "Difficulty swallowing", "Nasal congestion", "Eye discharge",
    "Facial pain", "Hair loss",
    "Genital sores", "Genital discharge",
    "Rectal bleeding", "Anal pain", "Swelling near anus",
    "Pain during bowel movement", "Mucus discharge from anus",
    "Tooth pain", "Jaw swelling",
    "Joint swelling", "Stiffness", "Reduced range of motion",
    "Dry skin", "Poor wound healing",
    "Blood in stool", "Excessive sleepiness", "Hydrophobia", "Agitation",
    "Skin redness", "Skin warmth", "Speech difficulty", "Facial drooping",
    "Loss of balance", "Loss of taste", "Loss of smell",
]
SYMPTOM_SET = set(ALL_SYMPTOMS)

# ─────────────────────────────────────────────────────────────────────────────
# Symptom name mapping: Kaggle snake_case  →  MediGuard symptom name
# Unmapped Kaggle symptoms are silently dropped (not in our schema).
# ─────────────────────────────────────────────────────────────────────────────
KAGGLE_SYMPTOM_MAP: dict[str, str] = {
    "itching":                       "Itchy skin",
    "skin_rash":                     "Rash",
    "nodal_skin_eruptions":          "Skin lesions",
    "continuous_sneezing":           "Sneezing",
    "shivering":                     "Chills",
    "chills":                        "Chills",
    "joint_pain":                    "Joint pain",
    "stomach_pain":                  "Abdominal pain",
    "belly_pain":                    "Abdominal pain",
    "acidity":                       "Heartburn",
    "ulcers_on_tongue":              "White patches in mouth",
    "patches_in_throat":             "White patches in mouth",
    "muscle_wasting":                "Weakness",
    "vomiting":                      "Vomiting",
    "burning_micturition":           "Painful urination",
    "spotting_ urination":           "Blood in urine",
    "spotting_urination":            "Blood in urine",
    "fatigue":                       "Fatigue",
    "weight_gain":                   "Weight gain",
    "anxiety":                       "Anxiety",
    "cold_hands_and_feets":          "Cold intolerance",
    "weight_loss":                   "Weight loss",
    "restlessness":                  "Anxiety",
    "lethargy":                      "Weakness",
    "irregular_sugar_level":         "Increased thirst",
    "cough":                         "Cough",
    "high_fever":                    "High fever",
    "sunken_eyes":                   "Sunken eyes",
    "breathlessness":                "Shortness of breath",
    "sweating":                      "Sweating",
    "dehydration":                   "Dehydration",
    "indigestion":                   "Bloating",
    "headache":                      "Headache",
    "yellowish_skin":                "Jaundice",
    "dark_urine":                    "Dark urine",
    "nausea":                        "Nausea",
    "loss_of_appetite":              "Loss of appetite",
    "pain_behind_the_eyes":          "Pain behind eyes",
    "back_pain":                     "Back pain",
    "constipation":                  "Constipation",
    "abdominal_pain":                "Abdominal pain",
    "diarrhoea":                     "Diarrhea",
    "mild_fever":                    "Mild fever",
    "yellow_urine":                  "Dark urine",
    "yellowing_of_eyes":             "Yellow eyes",
    "acute_liver_failure":           "Jaundice",
    "fluid_overload":                "Abdominal swelling",
    "swelling_of_stomach":           "Abdominal swelling",
    "distention_of_abdomen":         "Abdominal swelling",
    "swelled_lymph_nodes":           "Swollen lymph nodes",
    "malaise":                       "Fatigue",
    "blurred_and_distorted_vision":  "Blurred vision",
    "visual_disturbances":           "Blurred vision",
    "phlegm":                        "Cough",
    "mucoid_sputum":                 "Cough",
    "rusty_sputum":                  "Coughing up blood",
    "blood_in_sputum":               "Coughing up blood",
    "throat_irritation":             "Sore throat",
    "redness_of_eyes":               "Red eyes",
    "watering_from_eyes":            "Eye discharge",
    "sinus_pressure":                "Facial pain",
    "runny_nose":                    "Runny nose",
    "congestion":                    "Nasal congestion",
    "chest_pain":                    "Chest pain",
    "weakness_in_limbs":             "Weakness",
    "fast_heart_rate":               "Fast heartbeat",
    "palpitations":                  "Fast heartbeat",
    "pain_during_bowel_movements":   "Pain during bowel movement",
    "pain_in_anal_region":           "Anal pain",
    "bloody_stool":                  "Blood in stool",
    "irritation_in_anus":            "Anal itching",
    "neck_pain":                     "Neck pain",
    "dizziness":                     "Dizziness",
    "cramps":                        "Muscle cramps",
    "bruising":                      "Mild bleeding",
    "swollen_legs":                  "Swollen feet",
    "swollen_extremeties":           "Ankle swelling",
    "brittle_nails":                 "Hair loss",
    "slurred_speech":                "Speech difficulty",
    "knee_pain":                     "Joint pain",
    "hip_joint_pain":                "Joint pain",
    "muscle_weakness":               "Muscle aches",
    "muscle_pain":                   "Muscle aches",
    "stiff_neck":                    "Stiff neck",
    "swelling_joints":               "Joint swelling",
    "movement_stiffness":            "Stiffness",
    "loss_of_balance":               "Loss of balance",
    "loss_of_smell":                 "Loss of smell",
    "bladder_discomfort":            "Painful urination",
    "foul_smell_of_urine":           "Painful urination",
    "continuous_feel_of_urine":      "Frequent urination",
    "polyuria":                      "Frequent urination",
    "increased_appetite":            "Increased thirst",
    "internal_itching":              "Itchy skin",
    "irritability":                  "Irritability",
    "altered_sensorium":             "Confusion",
    "red_spots_over_body":           "Rash",
    "abnormal_menstruation":         "Vaginal bleeding",
    "dischromic_patches":            "Skin lesions",
    "skin_peeling":                  "Skin peeling",
    "blister":                       "Blisters",
    "red_sore_around_nose":          "Skin sores",
    "pus_filled_pimples":            "Pus or discharge",
    "prominent_veins_on_calf":       "Swollen feet",
    "pain_during_bowel_movement":    "Pain during bowel movement",
    "toxic_look_(typhos)":           "Confusion",
    "depression":                    "Fatigue",
    # Dataset 2 (dhivyeshrk) uses plain English names — normalise them below
    "fever":                         "Fever",
    "high fever":                    "High fever",
    "mild fever":                    "Mild fever",
    "prolonged fever":               "Prolonged fever",
    "sudden high fever":             "Sudden high fever",
    "chills and rigors":             "Chills",
    "headache":                      "Headache",
    "severe headache":               "Severe headache",
    "muscle ache":                   "Muscle aches",
    "muscle aches":                  "Muscle aches",
    "joint pain":                    "Joint pain",
    "fatigue":                       "Fatigue",
    "nausea":                        "Nausea",
    "vomiting":                      "Vomiting",
    "diarrhea":                      "Diarrhea",
    "diarrhoea":                     "Diarrhea",
    "abdominal pain":                "Abdominal pain",
    "stomach pain":                  "Abdominal pain",
    "cough":                         "Cough",
    "chronic cough":                 "Chronic cough",
    "shortness of breath":           "Shortness of breath",
    "breathlessness":                "Shortness of breath",
    "chest pain":                    "Chest pain",
    "rash":                          "Rash",
    "skin rash":                     "Rash",
    "itching":                       "Itchy skin",
    "itchy skin":                    "Itchy skin",
    "weight loss":                   "Weight loss",
    "night sweats":                  "Night sweats",
    "swollen lymph nodes":           "Swollen lymph nodes",
    "jaundice":                      "Jaundice",
    "dark urine":                    "Dark urine",
    "loss of appetite":              "Loss of appetite",
    "weakness":                      "Weakness",
    "fatigue and weakness":          "Fatigue",
    "runny nose":                    "Runny nose",
    "sore throat":                   "Sore throat",
    "sneezing":                      "Sneezing",
    "red eyes":                      "Red eyes",
    "eye discharge":                 "Eye discharge",
    "blisters":                      "Blisters",
    "stiff neck":                    "Stiff neck",
    "sensitivity to light":          "Sensitivity to light",
    "confusion":                     "Confusion",
    "seizures":                      "Seizures",
    "frequent urination":            "Frequent urination",
    "painful urination":             "Painful urination",
    "blood in urine":                "Blood in urine",
    "pelvic pain":                   "Pelvic pain",
    "lower abdominal pain":          "Lower abdominal pain",
    "back pain":                     "Back pain",
    "increased thirst":              "Increased thirst",
    "blurred vision":                "Blurred vision",
    "slow healing sores":            "Slow-healing sores",
    "pale skin":                     "Pale skin",
    "fast heartbeat":                "Fast heartbeat",
    "rapid heart rate":              "Fast heartbeat",
    "wheezing":                      "Wheezing",
    "chest tightness":               "Chest tightness",
    "burning stomach pain":          "Burning stomach pain",
    "bloating":                      "Bloating",
    "heartburn":                     "Heartburn",
    "ear pain":                      "Ear pain",
    "hearing loss":                  "Hearing loss",
    "nasal congestion":              "Nasal congestion",
    "facial pain":                   "Facial pain",
    "hair loss":                     "Hair loss",
    "genital sores":                 "Genital sores",
    "genital discharge":             "Genital discharge",
    "vaginal discharge":             "Vaginal discharge",
    "vaginal itching":               "Vaginal itching",
    "anal itching":                  "Anal itching",
    "swollen feet":                  "Swollen feet",
    "ankle swelling":                "Ankle swelling",
    "anxiety":                       "Anxiety",
    "tremor":                        "Tremor",
    "difficulty swallowing":         "Difficulty swallowing",
    "hoarse voice":                  "Hoarse voice",
    "jaw stiffness":                 "Jaw stiffness",
    "dehydration":                   "Dehydration",
    "sunken eyes":                   "Sunken eyes",
    "dry mouth":                     "Dry mouth",
    "muscle cramps":                 "Muscle cramps",
    "low blood pressure":            "Low blood pressure",
    "skin lesions":                  "Skin lesions",
    "skin sores":                    "Skin sores",
    "pus or discharge":              "Pus or discharge",
    "white patches in mouth":        "White patches in mouth",
    "weight gain":                   "Weight gain",
    "cold intolerance":              "Cold intolerance",
    "yellow eyes":                   "Yellow eyes",
    "abdominal swelling":            "Abdominal swelling",
    "nose bleeding":                 "Nose bleeding",
    "gum bleeding":                  "Gum bleeding",
    "severe itching":                "Severe itching",
    "night itching":                 "Night itching",
    "ring-shaped rash":              "Ring-shaped rash",
    "red scaly skin":                "Red scaly skin",
    "skin peeling":                  "Skin peeling",
    "cracked skin":                  "Cracked skin",
    "coughing up blood":             "Coughing up blood",
    "profuse watery diarrhea":       "Profuse watery diarrhea",
    "body aches":                    "Body aches",
    "body weakness":                 "Body weakness",
    "numbness":                      "Numbness",
    "neck pain":                     "Neck pain",
    "poor coordination":             "Poor coordination",
    "difficulty walking":            "Difficulty walking",
    "speech difficulty":             "Speech difficulty",
    "facial drooping":               "Facial drooping",
    "loss of balance":               "Loss of balance",
    "loss of taste":                 "Loss of taste",
    "loss of smell":                 "Loss of smell",
    "excessive sleepiness":          "Excessive sleepiness",
    "hydrophobia":                   "Hydrophobia",
    "agitation":                     "Agitation",
    "skin redness":                  "Skin redness",
    "skin warmth":                   "Skin warmth",
    "blood in stool":                "Blood in stool",
    "rectal bleeding":               "Rectal bleeding",
    "anal pain":                     "Anal pain",
    "swelling near anus":            "Swelling near anus",
    "constipation":                  "Constipation",
    "tooth pain":                    "Tooth pain",
    "jaw swelling":                  "Jaw swelling",
    "joint swelling":                "Joint swelling",
    "stiffness":                     "Stiffness",
    "reduced range of motion":       "Reduced range of motion",
    "dry skin":                      "Dry skin",
    "poor wound healing":            "Poor wound healing",
    "visible worms in stool":        "Visible worms in stool",
    "pain during intercourse":       "Pain during intercourse",
    "missed period":                 "Missed period",
    "sleep disturbances":            "Sleep disturbances",
    "reduced urination":             "Reduced urination",
    "burrow tracks":                 "Burrow tracks",
    "koplik spots":                  "Koplik spots",
    "rose spots":                    "Rose spots",
}

# ─────────────────────────────────────────────────────────────────────────────
# Disease name mapping: Kaggle name  →  MediGuard name
# Only diseases in this map are imported; others are silently skipped.
# ─────────────────────────────────────────────────────────────────────────────
KAGGLE_DISEASE_MAP: dict[str, str] = {
    # ── Direct matches ────────────────────────────────────────────────────────
    "Malaria":                          "Malaria",
    "Tuberculosis":                     "Tuberculosis",
    "Pneumonia":                        "Pneumonia",
    "Common Cold":                      "Common Cold",
    "Gastroenteritis":                  "Gastroenteritis",
    "Hypertension":                     "Hypertension",
    "Hypertension ":                    "Hypertension",
    "Migraine":                         "Migraine",
    "Arthritis":                        "Arthritis",
    "Acne":                             "Acne",
    "Hypothyroidism":                   "Hypothyroidism",
    "Hepatitis A":                      "Hepatitis A",
    "hepatitis A":                      "Hepatitis A",
    "Hepatitis B":                      "Hepatitis B",
    "Hepatitis C":                      "Hepatitis B",   # map to closest
    "Hepatitis D":                      "Hepatitis B",
    "Hepatitis E":                      "Hepatitis A",
    "Alcoholic hepatitis":              "Hepatitis A",
    "Measles":                          "Measles",
    "Mumps":                            "Mumps",
    "Rubella":                          "Rubella",
    "Scabies":                          "Scabies",
    "Epilepsy":                         "Epilepsy",
    "Meningitis":                       "Meningitis",
    "Cholera":                          "Cholera",
    "Dengue":                           "Dengue Fever",
    "Dengue Fever":                     "Dengue Fever",
    # ── Name differences ─────────────────────────────────────────────────────
    "Typhoid":                          "Typhoid Fever",
    "Typhoid Fever":                    "Typhoid Fever",
    "Chicken pox":                      "Chickenpox",
    "Chickenpox":                       "Chickenpox",
    "Varicella":                        "Chickenpox",
    "Diabetes":                         "Diabetes Mellitus",
    "Diabetes mellitus":                "Diabetes Mellitus",
    "Bronchial Asthma":                 "Asthma",
    "Asthma":                           "Asthma",
    "AIDS":                             "HIV AIDS",
    "HIV/AIDS":                         "HIV AIDS",
    "HIV":                              "HIV AIDS",
    "Urinary tract infection":          "Cystitis UTI",
    "UTI":                              "Cystitis UTI",
    "Peptic ulcer disease":             "Helicobacteriosis PepticUlcer",
    "GERD":                             "Helicobacteriosis PepticUlcer",
    "Fungal infection":                 "Skin Fungal Infection",
    "Tinea":                            "Skin Fungal Infection",
    "Ringworm":                         "Ringworm",
    "Dimorphic hemorrhoids(piles)":     "Hemorrhoids (Piles)",
    "Hemorrhoids":                      "Hemorrhoids (Piles)",
    "Piles":                            "Hemorrhoids (Piles)",
    "Impetigo":                         "Skin Abscess",
    "Skin abscess":                     "Skin Abscess",
    "Psoriasis":                        "Eczema",
    "Eczema":                           "Eczema",
    "Atopic dermatitis":                "Eczema",
    "Heart attack":                     "Heart Failure",
    "Heart failure":                    "Heart Failure",
    "Hyperthyroidism":                  "Hypothyroidism",  # closest available
    "Jaundice":                         "Hepatitis A",     # non-specific → map to Hep A
    "Yellow Fever":                     "Yellow Fever",
    "Leptospirosis":                    "Leptospirosis",
    "Brucellosis":                      "Brucellosis",
    "Typhus":                           "Typhus",
    "Septicemia":                       "Septicemia",
    "Sepsis":                           "Septicemia",
    "Dysentery":                        "Dysentery",
    "Sickle cell anemia":               "Sickle Cell Crisis",
    "Sickle Cell Crisis":               "Sickle Cell Crisis",
    "Iron deficiency anemia":           "Iron Deficiency Anemia",
    "Anemia":                           "Iron Deficiency Anemia",
    "Kidney stones":                    "Kidney Stones",
    "Appendicitis":                     "Appendicitis",
    "Tonsillitis":                      "Tonsillitis",
    "Sinusitis":                        "Sinusitis",
    "Ear infection":                    "Ear Infection",
    "Otitis media":                     "Ear Infection",
    "Conjunctivitis":                   "Conjunctivitis",
    "Pink eye":                         "Conjunctivitis",
    "Herpes zoster":                    "Herpes Zoster",
    "Shingles":                         "Herpes Zoster",
    "Tetanus":                          "Tetanus",
    "Diphtheria":                       "Diphtheria",
    "Whooping cough":                   "Whooping Cough",
    "Pertussis":                        "Whooping Cough",
    "Gonorrhea":                        "Gonorrhea",
    "Syphilis":                         "Syphilis",
    "Chlamydia":                        "Chlamydia",
    "Genital herpes":                   "Genital Herpes",
    "Trichomoniasis":                   "Trichomoniasis",
    "Pelvic inflammatory disease":      "Pelvic Inflammatory Disease",
    "PID":                              "Pelvic Inflammatory Disease",
    "Benign prostatic hyperplasia":     "Benign Prostatic Hyperplasia",
    "BPH":                              "Benign Prostatic Hyperplasia",
    "Onchocerciasis":                   "Onchocerciasis",
    "River blindness":                  "Onchocerciasis",
    "Filariasis":                       "Filariasis",
    "Lymphatic filariasis":             "Filariasis",
    "Anaphylaxis":                      "Anaphylaxis",
    "Malnutrition":                     "Malnutrition",
    "Arthritis (rheumatoid)":           "Arthritis",
    "Osteoarthritis":                   "Arthritis",
    "Rheumatoid arthritis":             "Arthritis",
    "Dental abscess":                   "Dental Abscess",
    "Candidiasis":                      "Candidiasis",
    "Thrush":                           "Candidiasis",
    "Cellulitis":                       "Cellulitis",
    "Stroke":                           "Stroke",
    "COVID-19":                         "COVID-19",
    "Covid-19":                         "COVID-19",
    "Coronavirus":                      "COVID-19",
    "Mpox":                             "Mpox",
    "Monkeypox":                        "Mpox",
    "Schistosomiasis":                  "Schistosomiasis",
    "Bilharzia":                        "Schistosomiasis",
    "Rabies":                           "Rabies",
    "African trypanosomiasis":          "African Trypanosomiasis",
    "Sleeping sickness":                "African Trypanosomiasis",
    "Buruli ulcer":                     "Buruli Ulcer",
    "Intestinal worms":                 "Intestinal Worms",
    "Helminthiasis":                    "Intestinal Worms",
    "Hypoglycemia":                     "Diabetes Mellitus",  # related condition
}


# ─────────────────────────────────────────────────────────────────────────────
# Kaggle download helper
# ─────────────────────────────────────────────────────────────────────────────

def _kaggle_available() -> bool:
    try:
        result = subprocess.run(
            ["kaggle", "--version"], capture_output=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def download_dataset(dataset_slug: str, dest: Path) -> bool:
    """Download a Kaggle dataset zip to dest/. Returns True on success."""
    dest.mkdir(parents=True, exist_ok=True)
    slug_dir = dest / dataset_slug.replace("/", "_")
    zip_path = slug_dir / "dataset.zip"

    if zip_path.exists():
        print(f"  [cache] {dataset_slug} already downloaded.")
        return True

    if not _kaggle_available():
        print(
            f"\n  [SKIP] kaggle CLI not found. To download '{dataset_slug}':\n"
            f"    1. pip install kaggle\n"
            f"    2. Place your API token at ~/.kaggle/kaggle.json\n"
            f"    3. Run:  kaggle datasets download -d {dataset_slug} "
            f"-p {slug_dir} --unzip\n"
        )
        return False

    slug_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {dataset_slug} …", end=" ", flush=True)
    result = subprocess.run(
        ["kaggle", "datasets", "download", "-d", dataset_slug,
         "-p", str(slug_dir)],
        capture_output=True,
        timeout=300,
    )
    if result.returncode != 0:
        print("FAILED")
        print(f"  stderr: {result.stderr.decode()[:500]}")
        return False
    print("done.")
    return True


def extract_dataset(dataset_slug: str, dest: Path) -> Path:
    """Extract zip and return the directory containing CSV files."""
    slug_dir = dest / dataset_slug.replace("/", "_")
    for f in slug_dir.iterdir():
        if f.suffix == ".zip":
            with zipfile.ZipFile(f) as zf:
                zf.extractall(slug_dir)
            break
    return slug_dir


# ─────────────────────────────────────────────────────────────────────────────
# Parser: binary-format CSV (kaushil268 / noeyislearning style)
#   Columns: <symptom_1>, <symptom_2>, …, prognosis
#   Values:  0 / 1 binary integers
# ─────────────────────────────────────────────────────────────────────────────

def parse_binary_csv(csv_path: Path) -> list[dict]:
    """Convert a binary-symptom Kaggle CSV to MediGuard row dicts."""
    rows = []
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            disease_col = raw.get("prognosis") or raw.get("Prognosis") or raw.get("disease")
            if not disease_col:
                continue
            disease_col = disease_col.strip()
            medi_disease = KAGGLE_DISEASE_MAP.get(disease_col)
            if not medi_disease:
                continue

            # Build MediGuard binary row (start all-zeros)
            row: dict[str, str] = {s: "0" for s in ALL_SYMPTOMS}
            row["disease"] = medi_disease

            for col, val in raw.items():
                if col in ("prognosis", "Prognosis", "disease"):
                    continue
                kaggle_col = col.strip().lower().replace(" ", "_")
                medi_sym = KAGGLE_SYMPTOM_MAP.get(kaggle_col)
                if medi_sym and medi_sym in SYMPTOM_SET:
                    # OR-logic: if any mapped column is 1, set symptom to 1
                    if str(val).strip() in ("1", "1.0"):
                        row[medi_sym] = "1"

            rows.append(row)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Parser: text-format CSV (dhivyeshrk / itachi9604 style)
#   Columns: Disease, Symptom_1, Symptom_2, … (text symptom names)
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_symptom(raw: str) -> str | None:
    """Normalise a free-text symptom name to a MediGuard symptom."""
    key = raw.strip().lower().replace("_", " ").replace("-", " ")
    direct = KAGGLE_SYMPTOM_MAP.get(key)
    if direct and direct in SYMPTOM_SET:
        return direct
    # Try Title Case lookup in symptom set
    tc = raw.strip().title()
    if tc in SYMPTOM_SET:
        return tc
    return None


def parse_text_csv(csv_path: Path) -> list[dict]:
    """Convert a text-symptom Kaggle CSV to MediGuard row dicts.

    Expected columns: Disease (or prognosis), Symptom_1, Symptom_2, …
    """
    rows = []
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        disease_col_name = next(
            (c for c in fieldnames if c.lower() in ("disease", "prognosis")), None
        )
        symptom_cols = [
            c for c in fieldnames
            if c != disease_col_name and "symptom" in c.lower()
        ]
        if not symptom_cols:
            # Assume all non-disease columns are symptoms
            symptom_cols = [c for c in fieldnames if c != disease_col_name]

        for raw in reader:
            if not disease_col_name:
                continue
            disease_raw = raw.get(disease_col_name, "").strip()
            medi_disease = KAGGLE_DISEASE_MAP.get(disease_raw)
            if not medi_disease:
                continue

            row: dict[str, str] = {s: "0" for s in ALL_SYMPTOMS}
            row["disease"] = medi_disease

            for sc in symptom_cols:
                sym_text = raw.get(sc, "").strip()
                if not sym_text:
                    continue
                medi_sym = _normalise_symptom(sym_text)
                if medi_sym:
                    row[medi_sym] = "1"

            rows.append(row)
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# Load the existing build_real_dataset synthetic data (optional)
# ─────────────────────────────────────────────────────────────────────────────

def load_synthetic_rows(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with csv_path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ─────────────────────────────────────────────────────────────────────────────
# Merge, split, train
# ─────────────────────────────────────────────────────────────────────────────

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ALL_SYMPTOMS + ["disease"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows → {path}")


def stratified_split(rows: list[dict], test_ratio: float = 0.2):
    by_disease: dict[str, list] = defaultdict(list)
    for row in rows:
        by_disease[row["disease"]].append(row)

    train, test = [], []
    for disease_rows in by_disease.values():
        random.shuffle(disease_rows)
        n_test = max(1, int(len(disease_rows) * test_ratio))
        test.extend(disease_rows[:n_test])
        train.extend(disease_rows[n_test:])

    random.shuffle(train)
    random.shuffle(test)
    return train, test


def train_model(rows: list[dict], variant: str) -> SimpleSymptomModel:
    class_counts = Counter(r["disease"] for r in rows)
    classes = sorted(class_counts)
    total = len(rows)
    symptom_counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        d = row["disease"]
        for s in ALL_SYMPTOMS:
            if str(row.get(s, "0")).strip() in ("1", "1.0"):
                symptom_counts[d][s] += 1

    log_priors = {d: math.log(c / total) for d, c in class_counts.items()}
    log_likelihoods: dict[str, dict] = {}
    for d in classes:
        log_likelihoods[d] = {
            s: (symptom_counts[d][s] + 1) / (class_counts[d] + 2)
            for s in ALL_SYMPTOMS
        }
    return SimpleSymptomModel(ALL_SYMPTOMS, classes, log_priors, log_likelihoods, variant)


def evaluate(model: SimpleSymptomModel, rows: list[dict]) -> float:
    correct = 0
    for row in rows:
        selected = [s for s in ALL_SYMPTOMS if str(row.get(s, "0")).strip() in ("1", "1.0")]
        pred = model.predict_ranked(selected, top_k=1)[0]["disease"]
        correct += pred == row["disease"]
    return correct / len(rows) if rows else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

DATASETS = [
    # (slug, expected CSV filenames to try, format)
    (
        "kaushil268/disease-prediction-using-machine-learning",
        ["Training.csv", "training.csv", "dataset.csv"],
        "binary",
    ),
    (
        "noeyislearning/disease-prediction-based-on-symptoms",
        ["train.csv", "Training.csv", "dataset.csv"],
        "binary",
    ),
    (
        "dhivyeshrk/diseases-and-symptoms-dataset",
        ["dataset.csv", "diseases_and_symptoms.csv", "Diseases_Symptoms.csv"],
        "text",
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and merge real disease datasets")
    parser.add_argument("--skip-download", action="store_true",
                        help="Skip download; use already-extracted files in data/external/")
    parser.add_argument("--no-synthetic", "--real-only", action="store_true",
                        help="Exclude existing synthetic data; train on real data only")
    args = parser.parse_args()

    ext_dir = BASE / "data/external"
    all_rows: list[dict] = []

    # ── 1. Load existing synthetic data ──────────────────────────────────────
    if not args.no_synthetic:
        synth_path = BASE / "data/raw/mediguard_dataset_full.csv"
        synth_rows = load_synthetic_rows(synth_path)
        if synth_rows:
            print(f"Loaded {len(synth_rows)} existing synthetic rows from {synth_path}")
            all_rows.extend(synth_rows)
        else:
            print("No existing synthetic data found — run build_real_dataset.py first "
                  "to generate baseline synthetic rows.")

    # ── 2. Download + parse each Kaggle dataset ───────────────────────────────
    for slug, csv_candidates, fmt in DATASETS:
        print(f"\n── Dataset: {slug} ({fmt}) ──")

        if not args.skip_download:
            ok = download_dataset(slug, ext_dir)
            if not ok:
                print(f"  Skipping {slug} (download failed or kaggle CLI absent).")
                continue
            slug_dir = extract_dataset(slug, ext_dir)
        else:
            slug_dir = ext_dir / slug.replace("/", "_")
            if not slug_dir.exists():
                print(f"  Directory not found: {slug_dir} — skipping.")
                continue

        # Find the CSV file
        csv_path = None
        for candidate in csv_candidates:
            p = slug_dir / candidate
            if p.exists():
                csv_path = p
                break
        if csv_path is None:
            # Try any CSV in the directory
            csvs = list(slug_dir.glob("*.csv"))
            if csvs:
                csv_path = csvs[0]
        if csv_path is None:
            print(f"  No CSV found in {slug_dir} — skipping.")
            continue

        print(f"  Parsing {csv_path.name} …", end=" ", flush=True)
        if fmt == "binary":
            new_rows = parse_binary_csv(csv_path)
        else:
            new_rows = parse_text_csv(csv_path)

        disease_counts = Counter(r["disease"] for r in new_rows)
        print(f"{len(new_rows)} rows, {len(disease_counts)} diseases matched")
        for d, c in sorted(disease_counts.items()):
            print(f"    {d}: {c}")

        all_rows.extend(new_rows)

    if not all_rows:
        print("\nNo data available. "
              "Install kaggle CLI and set up credentials, then re-run.")
        sys.exit(1)

    # ── 3. Save full dataset ───────────────────────────────────────────────────
    print(f"\nTotal rows: {len(all_rows)}")
    print(f"Diseases:   {len({r['disease'] for r in all_rows})}")

    random.shuffle(all_rows)
    write_csv(BASE / "data/raw/mediguard_dataset_full.csv", all_rows)

    # ── 4. Stratified train/test split ────────────────────────────────────────
    train_rows, test_rows = stratified_split(all_rows, test_ratio=0.2)
    print(f"Train: {len(train_rows)}  Test: {len(test_rows)}")
    write_csv(BASE / "data/processed/mediguard_train.csv", train_rows)
    write_csv(BASE / "data/processed/mediguard_test.csv", test_rows)

    # ── 5. Update symptoms list ────────────────────────────────────────────────
    for sym_path in [
        BASE / "data_pipeline/symptoms_list.json",
        BASE / "models/symptoms_list.json",
    ]:
        sym_path.parent.mkdir(parents=True, exist_ok=True)
        sym_path.write_text(json.dumps(ALL_SYMPTOMS, indent=2), encoding="utf-8")

    # ── 6. Train and evaluate models ──────────────────────────────────────────
    print("\nTraining models …")
    models_dir = BASE / "models"
    models_dir.mkdir(exist_ok=True)

    for name, variant in [
        ("random_forest", "random_forest_fallback"),
        ("decision_tree", "decision_tree_fallback"),
        ("naive_bayes",   "naive_bayes_fallback"),
    ]:
        model = train_model(train_rows, variant)
        acc = evaluate(model, test_rows)
        pkl_path = models_dir / f"{name}.pkl"
        with pkl_path.open("wb") as f:
            pickle.dump(model, f)
        print(f"  {name}: accuracy = {acc:.4f}  ({acc * 100:.1f}%)")

    classes = sorted({r["disease"] for r in train_rows})
    with (models_dir / "label_encoder.pkl").open("wb") as f:
        pickle.dump(SimpleLabelEncoder(classes), f)

    print(f"\nDone. {len(classes)} diseases, {len(ALL_SYMPTOMS)} symptoms.")
    print("Models saved to models/")


if __name__ == "__main__":
    main()
