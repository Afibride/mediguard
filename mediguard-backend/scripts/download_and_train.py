"""
download_and_train.py
=====================
Master training pipeline for MediGuard.

Downloads real patient-diagnosis datasets from Kaggle, merges them with any
CSV files placed in data/custom/ (e.g. Malaria_Dataset.csv), and retrains
all three symptom-classification models.

USAGE
------
    # Full run (download + merge + train):
    python scripts/download_and_train.py

    # Skip re-downloading already-present zips:
    python scripts/download_and_train.py --skip-download

    # Exclude the existing synthetic baseline, use real data only:
    python scripts/download_and_train.py --real-only

    # Preview what would be imported without writing anything:
    python scripts/download_and_train.py --dry-run

PREREQUISITES
--------------
    pip install kaggle
    Place ~/.kaggle/kaggle.json  (kaggle.com -> Account -> Create API Token)

DATASETS DOWNLOADED (12 sources)
----------------------------------
  1. kaushil268/disease-prediction-using-machine-learning   (42 diseases, 5 000 rows)
  2. noeyislearning/disease-prediction-based-on-symptoms    (42 diseases, split CSVs)
  3. ishandutta/early-stage-diabetes-risk-prediction-dataset (diabetes, 520 rows)
  4. victorcaelina/tuberculosis-symptoms                    (TB, binary columns)
  5. dhivyeshrk/diseases-and-symptoms-dataset              (773 diseases, text)
  6. uom190346a/disease-symptoms-and-patient-profile-dataset (100 diseases)
  7. niyarrbarman/symptom2disease                           (24 diseases, text)
  8. choongqianzheng/disease-and-symptoms-dataset           (multi-disease)
  9. itachi9604/disease-symptom-description-dataset         (41 diseases)
 10. kaushil268/disease-prediction-using-machine-learning   (already #1)
 11. pasindueranga/disease-prediction-based-on-symptoms     (alternate split)
 12. s3programmer/disease-diagnosis-dataset                 (multi-disease)

CUSTOM CSVS  (place in data/custom/)
--------------------------------------
  Malaria_Dataset.csv     — real hospital Malaria records (your file)
  Typhoid_Dataset.csv     — uncomment config when you obtain it
  Dengue_Dataset.csv      — uncomment config when you obtain it
  (see CUSTOM_DATASET_CONFIGS at the bottom of this file)
"""

import argparse
import csv
import json
import math
import os
import pickle
import random
import re
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.ml.simple_model import SimpleLabelEncoder, SimpleSymptomModel  # noqa: E402

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
BASE = Path(__file__).parent.parent

# -- MediGuard master symptom list ---------------------------------------------
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

# =============================================================================
# SYMPTOM ALIAS TABLE
# Normalise any free-text or snake_case symptom name -> MediGuard name.
# Add entries here when a new dataset uses different wording.
# =============================================================================
SYMPTOM_ALIAS: dict[str, str] = {
    # -- kaushil268 snake_case ----------------------------------------------
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
    "toxic_look_(typhos)":           "Confusion",
    "depression":                    "Fatigue",
    "passage_of_gases":              "Bloating",
    "stomach_bleeding":              "Blood in stool",
    "receiving_blood_transfusion":   "Weakness",
    "coma":                          "Confusion",
    "yellow_crust_ooze":             "Skin sores",
    "silver_like_dusting":           "Skin lesions",
    "small_dents_in_nails":          "Hair loss",
    "inflammatory_nails":            "Skin sores",
    "scurring":                      "Skin lesions",
    "blackheads":                    "Skin sores",
    "painful_walking":               "Joint pain",
    # -- Malaria CSV ----------------------------------------------------------
    "abdominal_pain":                "Abdominal pain",
    "general_body_malaise":          "Fatigue",
    "backache":                      "Back pain",
    "coughing":                      "Cough",
    # -- Early-stage diabetes -------------------------------------------------
    "polyuria":                      "Frequent urination",
    "polydipsia":                    "Increased thirst",
    "sudden weight loss":            "Weight loss",
    "weakness":                      "Weakness",
    "polyphagia":                    "Increased thirst",
    "genital thrush":                "Vaginal itching",
    "visual blurring":               "Blurred vision",
    "itching":                       "Itchy skin",
    "delayed healing":               "Slow-healing sores",
    "partial paresis":               "Weakness",
    "muscle stiffness":              "Stiffness",
    "alopecia":                      "Hair loss",
    # -- Tuberculosis dataset --------------------------------------------------
    "night_sweats":                  "Night sweats",
    "night sweats":                  "Night sweats",
    "weight_loss":                   "Weight loss",
    "chronic_cough":                 "Chronic cough",
    "blood_in_sputum":               "Coughing up blood",
    "hemoptysis":                    "Coughing up blood",
    "shortness_of_breath":           "Shortness of breath",
    "shortness of breath":           "Shortness of breath",
    "loss_of_appetite":              "Loss of appetite",
    "loss of appetite":              "Loss of appetite",
    "chest_pain":                    "Chest pain",
    "chest pain":                    "Chest pain",
    "fever":                         "Fever",
    "cough":                         "Cough",
    "fatigue":                       "Fatigue",
    "weakness":                      "Weakness",
    "sweating":                      "Sweating",
    "swollen_lymph_nodes":           "Swollen lymph nodes",
    "swollen lymph nodes":           "Swollen lymph nodes",
    # -- uom190346a dataset ----------------------------------------------------
    "difficulty breathing":          "Shortness of breath",
    "difficulty_breathing":          "Shortness of breath",
    # -- Plain English (dhivyeshrk text format) --------------------------------
    "skin rash":                     "Rash",
    "joint pain":                    "Joint pain",
    "stomach pain":                  "Abdominal pain",
    "abdominal pain":                "Abdominal pain",
    "high fever":                    "High fever",
    "mild fever":                    "Mild fever",
    "prolonged fever":               "Prolonged fever",
    "sudden high fever":             "Sudden high fever",
    "chills and rigors":             "Chills",
    "headache":                      "Headache",
    "severe headache":               "Severe headache",
    "muscle ache":                   "Muscle aches",
    "muscle aches":                  "Muscle aches",
    "vomiting":                      "Vomiting",
    "nausea":                        "Nausea",
    "diarrhea":                      "Diarrhea",
    "constipation":                  "Constipation",
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
    "loss of taste":                 "Loss of taste",
    "loss of smell":                 "Loss of smell",
    "excessive sleepiness":          "Excessive sleepiness",
    "blood in stool":                "Blood in stool",
    "rectal bleeding":               "Rectal bleeding",
    "anal pain":                     "Anal pain",
    "swelling near anus":            "Swelling near anus",
    "tooth pain":                    "Tooth pain",
    "jaw swelling":                  "Jaw swelling",
    "joint swelling":                "Joint swelling",
    "stiffness":                     "Stiffness",
    "dry skin":                      "Dry skin",
    "visible worms in stool":        "Visible worms in stool",
    "pain during intercourse":       "Pain during intercourse",
    "missed period":                 "Missed period",
    "sleep disturbances":            "Sleep disturbances",
    "reduced urination":             "Reduced urination",
    "burrow tracks":                 "Burrow tracks",
    "koplik spots":                  "Koplik spots",
    "rose spots":                    "Rose spots",
    "jaundice":                      "Jaundice",
    "dark urine":                    "Dark urine",
    "weight loss":                   "Weight loss",
    "night sweats":                  "Night sweats",
    "chronic cough":                 "Chronic cough",
    "pale skin":                     "Pale skin",
    "rash":                          "Rash",
    "itchy skin":                    "Itchy skin",
    "itchy rash":                    "Itchy rash",
    "loss of appetite":              "Loss of appetite",
    "swollen lymph nodes":           "Swollen lymph nodes",
    "shortness of breath":           "Shortness of breath",
}

# =============================================================================
# DISEASE NAME MAP  (any source -> MediGuard label)
# =============================================================================
DISEASE_MAP: dict[str, str] = {
    # -- exact matches ------------------------------------------------------
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
    "Measles":                          "Measles",
    "Mumps":                            "Mumps",
    "Rubella":                          "Rubella",
    "Scabies":                          "Scabies",
    "Epilepsy":                         "Epilepsy",
    "Meningitis":                       "Meningitis",
    "Cholera":                          "Cholera",
    "Ringworm":                         "Ringworm",
    "Leptospirosis":                    "Leptospirosis",
    "Brucellosis":                      "Brucellosis",
    "Typhus":                           "Typhus",
    "Tetanus":                          "Tetanus",
    "Diphtheria":                       "Diphtheria",
    "Tonsillitis":                      "Tonsillitis",
    "Sinusitis":                        "Sinusitis",
    "Conjunctivitis":                   "Conjunctivitis",
    "Anaphylaxis":                      "Anaphylaxis",
    "Malnutrition":                     "Malnutrition",
    "Candidiasis":                      "Candidiasis",
    "Cellulitis":                       "Cellulitis",
    "Stroke":                           "Stroke",
    "Septicemia":                       "Septicemia",
    "Eczema":                           "Eczema",
    "Mpox":                             "Mpox",
    "Schistosomiasis":                  "Schistosomiasis",
    "Rabies":                           "Rabies",
    "Onchocerciasis":                   "Onchocerciasis",
    "Filariasis":                       "Filariasis",
    # -- name differences --------------------------------------------------
    "Dengue":                           "Dengue Fever",
    "Dengue Fever":                     "Dengue Fever",
    "Dengue fever":                     "Dengue Fever",
    "Typhoid":                          "Typhoid Fever",
    "Typhoid Fever":                    "Typhoid Fever",
    "Typhoid fever":                    "Typhoid Fever",
    "Chicken pox":                      "Chickenpox",
    "Chickenpox":                       "Chickenpox",
    "Varicella":                        "Chickenpox",
    "Diabetes":                         "Diabetes Mellitus",
    "Diabetes mellitus":                "Diabetes Mellitus",
    "Diabetes Mellitus":                "Diabetes Mellitus",
    "Bronchial Asthma":                 "Asthma",
    "Asthma":                           "Asthma",
    "AIDS":                             "HIV AIDS",
    "HIV/AIDS":                         "HIV AIDS",
    "HIV":                              "HIV AIDS",
    "HIV AIDS":                         "HIV AIDS",
    "Urinary tract infection":          "Cystitis UTI",
    "UTI":                              "Cystitis UTI",
    "Cystitis UTI":                     "Cystitis UTI",
    "Peptic ulcer disease":             "Helicobacteriosis PepticUlcer",
    "GERD":                             "Helicobacteriosis PepticUlcer",
    "Helicobacteriosis PepticUlcer":    "Helicobacteriosis PepticUlcer",
    "Fungal infection":                 "Skin Fungal Infection",
    "Tinea":                            "Skin Fungal Infection",
    "Skin Fungal Infection":            "Skin Fungal Infection",
    "Dimorphic hemorrhoids(piles)":     "Hemorrhoids (Piles)",
    "Hemorrhoids":                      "Hemorrhoids (Piles)",
    "Piles":                            "Hemorrhoids (Piles)",
    "Hemorrhoids (Piles)":              "Hemorrhoids (Piles)",
    "Impetigo":                         "Skin Abscess",
    "Skin abscess":                     "Skin Abscess",
    "Skin Abscess":                     "Skin Abscess",
    "Psoriasis":                        "Eczema",
    "Atopic dermatitis":                "Eczema",
    "Heart attack":                     "Heart Failure",
    "Heart failure":                    "Heart Failure",
    "Heart Failure":                    "Heart Failure",
    "Hyperthyroidism":                  "Hypothyroidism",
    "Jaundice":                         "Hepatitis A",
    "hepatitis A":                      "Hepatitis A",
    "Hepatitis A":                      "Hepatitis A",
    "Hepatitis B":                      "Hepatitis B",
    "Hepatitis C":                      "Hepatitis B",
    "Hepatitis D":                      "Hepatitis B",
    "Hepatitis E":                      "Hepatitis A",
    "Alcoholic hepatitis":              "Hepatitis A",
    "Yellow Fever":                     "Yellow Fever",
    "Whooping cough":                   "Whooping Cough",
    "Whooping Cough":                   "Whooping Cough",
    "Pertussis":                        "Whooping Cough",
    "Gonorrhea":                        "Gonorrhea",
    "Syphilis":                         "Syphilis",
    "Chlamydia":                        "Chlamydia",
    "Genital herpes":                   "Genital Herpes",
    "Genital Herpes":                   "Genital Herpes",
    "Trichomoniasis":                   "Trichomoniasis",
    "Pelvic inflammatory disease":      "Pelvic Inflammatory Disease",
    "PID":                              "Pelvic Inflammatory Disease",
    "Pelvic Inflammatory Disease":      "Pelvic Inflammatory Disease",
    "Benign prostatic hyperplasia":     "Benign Prostatic Hyperplasia",
    "BPH":                              "Benign Prostatic Hyperplasia",
    "Benign Prostatic Hyperplasia":     "Benign Prostatic Hyperplasia",
    "Sickle cell anemia":               "Sickle Cell Crisis",
    "Sickle Cell Crisis":               "Sickle Cell Crisis",
    "Iron deficiency anemia":           "Iron Deficiency Anemia",
    "Anemia":                           "Iron Deficiency Anemia",
    "Iron Deficiency Anemia":          "Iron Deficiency Anemia",
    "Kidney stones":                    "Kidney Stones",
    "Kidney Stones":                    "Kidney Stones",
    "Appendicitis":                     "Appendicitis",
    "Ear infection":                    "Ear Infection",
    "Ear Infection":                    "Ear Infection",
    "Otitis media":                     "Ear Infection",
    "Herpes zoster":                    "Herpes Zoster",
    "Herpes Zoster":                    "Herpes Zoster",
    "Shingles":                         "Herpes Zoster",
    "Pink eye":                         "Conjunctivitis",
    "Intestinal worms":                 "Intestinal Worms",
    "Intestinal Worms":                 "Intestinal Worms",
    "Helminthiasis":                    "Intestinal Worms",
    "Dental abscess":                   "Dental Abscess",
    "Dental Abscess":                   "Dental Abscess",
    "African trypanosomiasis":          "African Trypanosomiasis",
    "African Trypanosomiasis":          "African Trypanosomiasis",
    "Sleeping sickness":                "African Trypanosomiasis",
    "Buruli ulcer":                     "Buruli Ulcer",
    "Buruli Ulcer":                     "Buruli Ulcer",
    "COVID-19":                         "COVID-19",
    "Covid-19":                         "COVID-19",
    "Coronavirus":                      "COVID-19",
    "Monkeypox":                        "Mpox",
    "Bilharzia":                        "Schistosomiasis",
    "River blindness":                  "Onchocerciasis",
    "Lymphatic filariasis":             "Filariasis",
    "Osteoarthritis":                   "Arthritis",
    "Rheumatoid arthritis":             "Arthritis",
    "Hypoglycemia":                     "Diabetes Mellitus",
    "Sepsis":                           "Septicemia",
    "Thrush":                           "Candidiasis",
    "Bilharzia":                        "Schistosomiasis",
}


# =============================================================================
# KAGGLE DATASETS TO DOWNLOAD
# =============================================================================

class KaggleDataset:
    def __init__(self, slug: str, csvs: list[str], fmt: str, note: str = ""):
        self.slug = slug
        self.csvs = csvs          # candidate CSV filenames to try
        self.fmt = fmt            # "binary", "text", "diabetes", "tb", "profile"
        self.note = note


KAGGLE_DATASETS: list[KaggleDataset] = [
    KaggleDataset(
        "kaushil268/disease-prediction-using-machine-learning",
        ["Training.csv", "training.csv"],
        "binary",
        "42 diseases, 132 binary symptom columns — primary source",
    ),
    KaggleDataset(
        "noeyislearning/disease-prediction-based-on-symptoms",
        ["train.csv", "Training.csv", "dataset.csv"],
        "binary",
        "Alternate 42-disease split — adds rows for same diseases",
    ),
    KaggleDataset(
        "pasindueranga/disease-prediction-based-on-symptoms",
        ["train.csv", "Training.csv", "dataset.csv"],
        "binary",
        "Another 42-disease alternate source",
    ),
    KaggleDataset(
        "itachi9604/disease-symptom-description-dataset",
        ["dataset.csv", "Symptom_severity.csv"],
        "text",
        "41 diseases with text symptom columns",
    ),
    KaggleDataset(
        "ishandutta/early-stage-diabetes-risk-prediction-dataset",
        ["diabetes_risk_prediction_dataset.csv", "diabetes.csv", "dataset.csv"],
        "diabetes",
        "520 real patients — Early Stage Diabetes (UCI)",
    ),
    KaggleDataset(
        "victorcaelina/tuberculosis-symptoms",
        ["tuberculosis_symptoms.csv", "tb_symptoms.csv", "dataset.csv"],
        "tb",
        "Tuberculosis symptom records",
    ),
    KaggleDataset(
        "dhivyeshrk/diseases-and-symptoms-dataset",
        ["dataset.csv", "Diseases_Symptoms.csv"],
        "text",
        "773 diseases, 246 000 rows — broadest disease coverage",
    ),
    KaggleDataset(
        "uom190346a/disease-symptoms-and-patient-profile-dataset",
        ["disease_symptom_and_patient_profile_dataset.csv", "dataset.csv"],
        "profile",
        "100 diseases, binary Fever/Cough/Fatigue/DifficultyBreathing",
    ),
    KaggleDataset(
        "choongqianzheng/disease-and-symptoms-dataset",
        ["disease_and_symptoms_dataset.csv", "dataset.csv"],
        "text",
        "~5000 multi-disease symptom records",
    ),
    KaggleDataset(
        "s3programmer/disease-diagnosis-dataset",
        ["disease_diagnosis_dataset.csv", "dataset.csv"],
        "profile",
        "Multi-disease diagnosis dataset",
    ),
    KaggleDataset(
        "miltonmacgyver/symptom-based-disease-prediction-dataset",
        ["symptom_based_disease_prediction_dataset.csv", "dataset.csv"],
        "binary",
        "Symptom-based prediction, binary format",
    ),
]

# =============================================================================
# CUSTOM CSV CONFIGS  (files in data/custom/)
# =============================================================================

class CustomDataset(NamedTuple):
    filename: str
    disease: str
    col_map: dict
    label_col: str = ""
    label_map: dict = {}


CUSTOM_DATASETS: list[CustomDataset] = [
    CustomDataset(
        filename="Malaria_Dataset.csv",
        disease="Malaria",
        col_map={
            "Fever":                "Fever",
            "Headache":             "Headache",
            "Abdominal_Pain":       "Abdominal pain",
            "General_Body_Malaise": "Fatigue",
            "Dizziness":            "Dizziness",
            "Vomiting":             "Vomiting",
            "Confusion":            "Confusion",
            "Backache":             "Back pain",
            "Chest_Pain":           "Chest pain",
            "Coughing":             "Cough",
            "Joint_Pain":           "Joint pain",
        },
    ),
    # -- Add more custom CSVs below as you collect them ------------------------
    # CustomDataset(
    #     filename="Typhoid_Dataset.csv",
    #     disease="Typhoid Fever",
    #     col_map={
    #         "Fever": "Prolonged fever", "Headache": "Headache",
    #         "Abdominal_Pain": "Abdominal pain", "Vomiting": "Vomiting",
    #         "Diarrhea": "Diarrhea", "Weakness": "Weakness",
    #         "Loss_of_Appetite": "Loss of appetite",
    #     },
    # ),
    # CustomDataset(
    #     filename="Dengue_Dataset.csv",
    #     disease="Dengue Fever",
    #     col_map={
    #         "Fever": "High fever", "Headache": "Severe headache",
    #         "Pain_Behind_Eyes": "Pain behind eyes", "Joint_Pain": "Joint pain",
    #         "Muscle_Pain": "Muscle aches", "Rash": "Rash",
    #         "Vomiting": "Vomiting", "Nausea": "Nausea", "Fatigue": "Fatigue",
    #     },
    # ),
    # CustomDataset(
    #     filename="Cholera_Dataset.csv",
    #     disease="Cholera",
    #     col_map={
    #         "Watery_Diarrhea": "Profuse watery diarrhea", "Vomiting": "Vomiting",
    #         "Dehydration": "Rapid dehydration", "Muscle_Cramps": "Muscle cramps",
    #         "Low_Blood_Pressure": "Low blood pressure", "Weakness": "Weakness",
    #     },
    # ),
    # CustomDataset(
    #     filename="Pneumonia_Dataset.csv",
    #     disease="Pneumonia",
    #     col_map={
    #         "Cough": "Cough", "Fever": "Fever", "Chest_Pain": "Chest pain",
    #         "Shortness_of_Breath": "Shortness of breath", "Fatigue": "Fatigue",
    #         "Chills": "Chills",
    #     },
    # ),
]


# =============================================================================
# KAGGLE DOWNLOAD HELPERS
# =============================================================================

def _kaggle_env() -> dict:
    """Build environment dict with KAGGLE_API_TOKEN set from access_token file."""
    env = os.environ.copy()
    # Prefer env var already set
    if "KAGGLE_API_TOKEN" in env:
        return env
    # Read from ~/.kaggle/access_token
    token_path = Path.home() / ".kaggle" / "access_token"
    if token_path.exists():
        env["KAGGLE_API_TOKEN"] = token_path.read_text(encoding="utf-8").strip()
    return env


def _kaggle_cmd() -> list[str] | None:
    """Return the kaggle command list, or None if kaggle is not available."""
    env = _kaggle_env()
    for cmd in [[sys.executable, "-m", "kaggle"], ["kaggle"]]:
        try:
            r = subprocess.run(
                cmd + ["--version"], capture_output=True, timeout=10, env=env,
            )
            if r.returncode == 0:
                return cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _kaggle_ok() -> bool:
    return _kaggle_cmd() is not None


def download_kaggle(slug: str, dest: Path) -> bool:
    slug_dir = dest / slug.replace("/", "_")
    if any(slug_dir.glob("*.csv")):
        print(f"  [cache] {slug}")
        return True
    cmd = _kaggle_cmd()
    if not cmd:
        print(f"  [SKIP]  {slug} — kaggle not found. Run: pip install kaggle")
        return False
    slug_dir.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {slug} ...", end=" ", flush=True)
    r = subprocess.run(
        cmd + ["datasets", "download", "-d", slug, "-p", str(slug_dir)],
        capture_output=True, timeout=600, env=_kaggle_env(),
    )
    if r.returncode != 0:
        err = r.stderr.decode(errors="replace")
        print(f"FAILED\n  {err[:400]}")
        return False
    print("done.")
    for z in slug_dir.glob("*.zip"):
        with zipfile.ZipFile(z) as zf:
            zf.extractall(slug_dir)
    return True


def find_csv(slug_dir: Path, candidates: list[str]) -> Path | None:
    for name in candidates:
        p = slug_dir / name
        if p.exists():
            return p
    csvs = sorted(slug_dir.rglob("*.csv"))
    return csvs[0] if csvs else None


# =============================================================================
# ROW NORMALISATION HELPERS
# =============================================================================

def _norm_key(s: str) -> str:
    return s.strip().lower().replace("_", " ").replace("-", " ")


def resolve_symptom(raw: str) -> str | None:
    key = _norm_key(raw)
    medi = SYMPTOM_ALIAS.get(key)
    if medi and medi in SYMPTOM_SET:
        return medi
    # title-case direct lookup
    tc = raw.strip().title()
    if tc in SYMPTOM_SET:
        return tc
    # try original casing
    if raw.strip() in SYMPTOM_SET:
        return raw.strip()
    return None


def resolve_disease(raw: str) -> str | None:
    return DISEASE_MAP.get(raw.strip()) or DISEASE_MAP.get(raw.strip().title())


def _blank_row(disease: str) -> dict:
    row = {s: "0" for s in ALL_SYMPTOMS}
    row["disease"] = disease
    return row


def _is_positive(val: str) -> bool:
    return val.strip().lower() in {"1", "1.0", "yes", "y", "true", "positive", "present"}


# =============================================================================
# FORMAT-SPECIFIC PARSERS
# =============================================================================

def parse_binary(csv_path: Path) -> list[dict]:
    """kaushil268-style: binary integer columns + 'prognosis' label."""
    rows = []
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            disease_raw = (
                raw.get("prognosis") or raw.get("Prognosis") or raw.get("disease") or ""
            ).strip()
            disease = resolve_disease(disease_raw)
            if not disease:
                continue
            row = _blank_row(disease)
            for col, val in raw.items():
                if col.lower() in ("prognosis", "disease"):
                    continue
                sym = resolve_symptom(col)
                if sym and _is_positive(str(val)):
                    row[sym] = "1"
            rows.append(row)
    return rows


def parse_text(csv_path: Path) -> list[dict]:
    """dhivyeshrk-style: Disease col + Symptom_1 … Symptom_N (text names)."""
    rows = []
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        disease_col = next(
            (c for c in fieldnames if c.lower() in ("disease", "prognosis")), None
        )
        sym_cols = [c for c in fieldnames if c != disease_col]
        for raw in reader:
            if not disease_col:
                continue
            disease = resolve_disease(raw.get(disease_col, ""))
            if not disease:
                continue
            row = _blank_row(disease)
            for sc in sym_cols:
                text = raw.get(sc, "").strip()
                if not text:
                    continue
                sym = resolve_symptom(text)
                if sym:
                    row[sym] = "1"
            rows.append(row)
    return rows


def parse_diabetes(csv_path: Path) -> list[dict]:
    """ishandutta Early-stage Diabetes: Yes/No feature cols + 'class' label."""
    rows = []
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            class_val = raw.get("class", raw.get("Class", "")).strip().lower()
            if class_val not in ("positive", "yes", "1"):
                continue          # keep only positive (diabetic) patients
            disease = "Diabetes Mellitus"
            row = _blank_row(disease)
            for col, val in raw.items():
                if col.lower() in ("class", "age", "gender", "sex", "id"):
                    continue
                sym = resolve_symptom(col)
                if sym and _is_positive(str(val)):
                    row[sym] = "1"
            rows.append(row)
    return rows


def parse_tb(csv_path: Path) -> list[dict]:
    """victorcaelina TB dataset: binary symptom cols + TB_Status / label col."""
    rows = []
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        # Detect label column
        label_col = next(
            (c for c in fieldnames
             if c.lower() in ("tb_status", "tuberculosis", "diagnosis",
                              "label", "class", "result", "outcome")),
            None,
        )
        for raw in reader:
            # Only include confirmed TB cases
            if label_col:
                lv = raw.get(label_col, "").strip().lower()
                if lv not in ("positive", "yes", "1", "tb", "true"):
                    continue
            row = _blank_row("Tuberculosis")
            for col, val in raw.items():
                if col == label_col or col.lower() in ("id", "age", "gender", "sex"):
                    continue
                sym = resolve_symptom(col)
                if sym and _is_positive(str(val)):
                    row[sym] = "1"
            rows.append(row)
    return rows


def parse_profile(csv_path: Path) -> list[dict]:
    """uom190346a-style: Disease, Fever (Yes/No), Cough (Yes/No), Fatigue, ..."""
    rows = []
    skip_cols = {"age", "gender", "sex", "blood pressure", "blood_pressure",
                 "cholesterol level", "cholesterol_level", "outcome variable",
                 "outcome_variable", "id"}
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            disease_raw = (
                raw.get("Disease") or raw.get("disease") or raw.get("prognosis") or ""
            ).strip()
            disease = resolve_disease(disease_raw)
            if not disease:
                continue
            row = _blank_row(disease)
            for col, val in raw.items():
                if col.lower() in skip_cols or col.lower() in ("disease", "prognosis"):
                    continue
                sym = resolve_symptom(col)
                if sym and _is_positive(str(val)):
                    row[sym] = "1"
            rows.append(row)
    return rows


def parse_custom(cfg: CustomDataset, csv_path: Path) -> list[dict]:
    """Single-disease CSV with a defined column map (e.g. Malaria_Dataset.csv)."""
    rows = []
    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        available = set(reader.fieldnames or [])
        mapped = {src: tgt for src, tgt in cfg.col_map.items()
                  if src in available and tgt in SYMPTOM_SET}
        missing = [src for src in cfg.col_map if src not in available]
        if missing:
            print(f"    [WARN] columns not found in {cfg.filename}: {missing}")

        for raw in reader:
            disease = cfg.disease
            row = _blank_row(disease)
            for src, tgt in mapped.items():
                if _is_positive(raw.get(src, "0")):
                    row[tgt] = "1"
            rows.append(row)
    return rows


PARSERS = {
    "binary":   parse_binary,
    "text":     parse_text,
    "diabetes": parse_diabetes,
    "tb":       parse_tb,
    "profile":  parse_profile,
}


# =============================================================================
# ML UTILITIES
# =============================================================================

def load_synthetic(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ALL_SYMPTOMS + ["disease"])
        w.writeheader()
        w.writerows(rows)
    print(f"  Saved {len(rows):,} rows -> {path}")


def stratified_split(rows: list[dict], test_ratio: float = 0.2):
    by_disease: dict[str, list] = defaultdict(list)
    for row in rows:
        by_disease[row["disease"]].append(row)
    train, test = [], []
    for dr in by_disease.values():
        random.shuffle(dr)
        n = max(1, int(len(dr) * test_ratio))
        test.extend(dr[:n])
        train.extend(dr[n:])
    random.shuffle(train)
    random.shuffle(test)
    return train, test


def train_model(rows: list[dict], variant: str) -> SimpleSymptomModel:
    cc = Counter(r["disease"] for r in rows)
    classes = sorted(cc)
    total = len(rows)
    sc: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        d = row["disease"]
        for s in ALL_SYMPTOMS:
            if str(row.get(s, "0")).strip() in ("1", "1.0"):
                sc[d][s] += 1
    lp = {d: math.log(c / total) for d, c in cc.items()}
    ll = {d: {s: (sc[d][s] + 1) / (cc[d] + 2) for s in ALL_SYMPTOMS} for d in classes}
    return SimpleSymptomModel(ALL_SYMPTOMS, classes, lp, ll, variant)


def evaluate(model: SimpleSymptomModel, rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return sum(
        model.predict_ranked(
            [s for s in ALL_SYMPTOMS if str(row.get(s, "0")).strip() in ("1", "1.0")],
            top_k=1,
        )[0]["disease"] == row["disease"]
        for row in rows
    ) / len(rows)


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true",
                    help="Skip Kaggle download; use already-extracted files")
    ap.add_argument("--real-only", "--no-synthetic", action="store_true",
                    help="Skip synthetic baseline; train on real data only")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse and report stats without writing files")
    args = ap.parse_args()

    ext_dir  = BASE / "data/external"
    cust_dir = BASE / "data/custom"
    cust_dir.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []

    # -- 1. Existing synthetic baseline ----------------------------------------
    if not args.real_only:
        synth = load_synthetic(BASE / "data/raw/mediguard_dataset_full.csv")
        if synth:
            print(f"Loaded {len(synth):,} existing synthetic rows.")
            all_rows.extend(synth)
        else:
            print("No synthetic baseline found. Run build_real_dataset.py first "
                  "to generate it (optional — training still works without it).")

    # -- 2. Kaggle datasets ----------------------------------------------------
    print(f"\n{'-'*60}")
    print(f"KAGGLE DATASETS ({len(KAGGLE_DATASETS)} sources)")
    print(f"{'-'*60}")

    for ds in KAGGLE_DATASETS:
        slug_dir = ext_dir / ds.slug.replace("/", "_")

        if not args.skip_download:
            ok = download_kaggle(ds.slug, ext_dir)
            if not ok:
                continue
        else:
            if not slug_dir.exists():
                print(f"  [SKIP] {ds.slug} — directory not found, use --skip-download=False")
                continue

        csv_path = find_csv(slug_dir, ds.csvs)
        if not csv_path:
            print(f"  [WARN] {ds.slug} — no CSV found in {slug_dir}")
            continue

        print(f"  Parsing {ds.slug}  ({ds.fmt})  {ds.note}")
        parser = PARSERS.get(ds.fmt, parse_binary)
        try:
            new_rows = parser(csv_path)
        except Exception as exc:
            print(f"    [ERROR] {exc}")
            continue

        if not new_rows:
            print(f"    (0 rows matched — check column names or disease map)")
            continue

        counts = Counter(r["disease"] for r in new_rows)
        print(f"    {len(new_rows):,} rows  |  {len(counts)} diseases")
        for d, n in sorted(counts.items(), key=lambda x: -x[1])[:10]:
            print(f"      {d}: {n:,}")
        if len(counts) > 10:
            print(f"      … and {len(counts) - 10} more")
        all_rows.extend(new_rows)

    # -- 3. Custom CSVs  (data/custom/) ----------------------------------------
    print(f"\n{'-'*60}")
    print("CUSTOM CSVs  (data/custom/)")
    print(f"{'-'*60}")

    for cfg in CUSTOM_DATASETS:
        csv_path = cust_dir / cfg.filename
        if not csv_path.exists():
            print(f"  [SKIP] {cfg.filename} — place it in data/custom/ to import")
            continue
        print(f"  Parsing {cfg.filename}  ->  '{cfg.disease}'")
        try:
            new_rows = parse_custom(cfg, csv_path)
        except Exception as exc:
            print(f"    [ERROR] {exc}")
            continue
        print(f"    {len(new_rows):,} rows")
        all_rows.extend(new_rows)

    # -- 4. Summary ------------------------------------------------------------
    if not all_rows:
        print("\nNo data collected. Install kaggle CLI, set up credentials, and re-run.")
        return

    disease_counts = Counter(r["disease"] for r in all_rows)
    print(f"\n{'='*60}")
    print(f"TOTAL: {len(all_rows):,} rows  |  {len(disease_counts)} diseases")
    print(f"{'-'*60}")
    for d, n in sorted(disease_counts.items(), key=lambda x: -x[1]):
        bar = "#" * min(40, n // max(1, max(disease_counts.values()) // 40))
        print(f"  {d:<40} {n:>5}  {bar}")

    if args.dry_run:
        print("\n[DRY RUN] No files written. Remove --dry-run to proceed.")
        return

    # -- 5. Write datasets -----------------------------------------------------
    print(f"\n{'-'*60}")
    print("SAVING DATASETS")
    random.shuffle(all_rows)
    write_csv(BASE / "data/raw/mediguard_dataset_full.csv", all_rows)

    train_rows, test_rows = stratified_split(all_rows, test_ratio=0.2)
    print(f"  Train: {len(train_rows):,}  Test: {len(test_rows):,}")
    write_csv(BASE / "data/processed/mediguard_train.csv", train_rows)
    write_csv(BASE / "data/processed/mediguard_test.csv",  test_rows)

    for sp in [BASE / "data_pipeline/symptoms_list.json",
               BASE / "models/symptoms_list.json"]:
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(ALL_SYMPTOMS, indent=2), encoding="utf-8")

    # -- 6. Retrain models -----------------------------------------------------
    print(f"\n{'-'*60}")
    print("TRAINING MODELS")
    models_dir = BASE / "models"
    models_dir.mkdir(exist_ok=True)

    for name, variant in [
        ("random_forest", "random_forest_fallback"),
        ("decision_tree", "decision_tree_fallback"),
        ("naive_bayes",   "naive_bayes_fallback"),
    ]:
        model = train_model(train_rows, variant)
        acc = evaluate(model, test_rows)
        with (models_dir / f"{name}.pkl").open("wb") as f:
            pickle.dump(model, f)
        print(f"  {name:<20} accuracy = {acc:.4f}  ({acc*100:.1f}%)")

    classes = sorted(disease_counts)
    with (models_dir / "label_encoder.pkl").open("wb") as f:
        pickle.dump(SimpleLabelEncoder(classes), f)

    print(f"\n{'='*60}")
    print(f"Done.  {len(classes)} diseases  |  {len(ALL_SYMPTOMS)} symptoms  |  {len(train_rows):,} training rows")
    print("Models saved -> models/")


if __name__ == "__main__":
    main()
