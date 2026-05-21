"""
generate_50_disease_dataset.py
==============================
Generates a synthetic symptom-disease CSV dataset for 50 diseases.

Each disease has:
  - core symptoms     → 90% presence probability
  - secondary symptoms → 60% presence probability
  - occasional symptoms → 25% presence probability
  - all other symptoms → 5% noise presence probability

Run from mediguard-backend/ root:
    python scripts/generate_50_disease_dataset.py

Outputs:
    data/raw/mediguard_dataset_full.csv
    data/processed/mediguard_train.csv
    data/processed/mediguard_test.csv
    data_pipeline/symptoms_list.json   (updated)
    models/random_forest.pkl  (trained SimpleSymptomModel)
    models/decision_tree.pkl
    models/naive_bayes.pkl
    models/label_encoder.pkl
"""

import csv
import json
import math
import pickle
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Allow importing from the app package so pickled models resolve correctly
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.ml.simple_model import SimpleSymptomModel, SimpleLabelEncoder  # noqa: E402

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Symptom list (127 total)
# ---------------------------------------------------------------------------
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
    # STI-specific
    "Genital sores", "Genital discharge",
]
SYMPTOM_INDEX = {s: i for i, s in enumerate(ALL_SYMPTOMS)}

# ---------------------------------------------------------------------------
# Disease profiles
# Structure: { "Disease Name": (core, secondary, occasional, records) }
# core = 90% presence, secondary = 60%, occasional = 25%, noise = 5%
# ---------------------------------------------------------------------------
DISEASE_PROFILES: dict[str, tuple[list, list, list, int]] = {
    "Malaria": (
        ["Fever", "Chills", "Sweating", "Headache", "Muscle aches"],
        ["Nausea", "Vomiting", "Fatigue"],
        ["Dizziness", "Weakness", "Joint pain"],
        200,
    ),
    "Typhoid Fever": (
        ["Prolonged fever", "Headache", "Weakness", "Abdominal pain"],
        ["Constipation", "Diarrhea", "Fatigue", "Nausea"],
        ["Rose spots", "Vomiting", "Low appetite"],
        180,
    ),
    "Cholera": (
        ["Profuse watery diarrhea", "Vomiting", "Rapid dehydration"],
        ["Muscle cramps", "Low blood pressure", "Dehydration"],
        ["Sunken eyes", "Dry mouth", "Weakness"],
        120,
    ),
    "Pneumonia": (
        ["Cough", "Fever", "Chest pain", "Shortness of breath"],
        ["Fatigue", "Chills", "Headache"],
        ["Nausea", "Muscle aches", "Rapid dehydration"],
        140,
    ),
    "Tuberculosis": (
        ["Chronic cough", "Night sweats", "Weight loss", "Fatigue"],
        ["Chest pain", "Coughing up blood", "Fever"],
        ["Weakness", "Swollen lymph nodes", "Loss of appetite"],
        100,
    ),
    "Meningitis": (
        ["Sudden high fever", "Stiff neck", "Severe headache"],
        ["Nausea", "Confusion", "Sensitivity to light"],
        ["Vomiting", "Seizures", "Sensitivity to sound"],
        80,
    ),
    "Dengue Fever": (
        ["High fever", "Severe headache", "Pain behind eyes", "Joint pain"],
        ["Muscle aches", "Rash", "Fatigue"],
        ["Mild bleeding", "Nose bleeding", "Vomiting"],
        90,
    ),
    "Dysentery": (
        ["Bloody or mucus-filled diarrhea", "Abdominal pain", "Fever"],
        ["Tenesmus", "Dehydration", "Nausea"],
        ["Vomiting", "Weakness", "Loss of appetite"],
        110,
    ),
    "Gastroenteritis": (
        ["Diarrhea", "Vomiting", "Abdominal pain", "Nausea"],
        ["Fever", "Weakness", "Dehydration"],
        ["Headache", "Muscle aches", "Low appetite"],
        130,
    ),
    "Asthma": (
        ["Wheezing", "Shortness of breath", "Chest tightness"],
        ["Cough", "Fatigue"],
        ["Anxiety", "Headache"],
        80,
    ),
    "Chickenpox": (
        ["Fever", "Itchy rash", "Blisters", "Fatigue"],
        ["Loss of appetite", "Headache"],
        ["Sore throat", "Weakness"],
        80,
    ),
    "Measles": (
        ["High fever", "Cough", "Runny nose", "Rash"],
        ["Red eyes", "Koplik spots", "Fatigue"],
        ["Loss of appetite", "Sneezing", "Weakness"],
        80,
    ),
    "Scabies": (
        ["Severe itching", "Night itching", "Burrow tracks"],
        ["Rash", "Skin sores"],
        ["Itchy skin", "Skin lesions"],
        70,
    ),
    "Diabetes Mellitus": (
        ["Increased thirst", "Frequent urination", "Fatigue"],
        ["Blurred vision", "Slow-healing sores", "Weight loss"],
        ["Dizziness", "Weakness", "Numbness"],
        100,
    ),
    "Hypertension": (
        ["Headache", "Dizziness", "Blurred vision"],
        ["Chest pain", "Shortness of breath", "Fast heartbeat"],
        ["Nausea", "Weakness", "Confusion"],
        100,
    ),
    "Iron Deficiency Anemia": (
        ["Fatigue", "Pale skin", "Dizziness"],
        ["Shortness of breath", "Fast heartbeat", "Weakness"],
        ["Headache", "Cold intolerance", "Numbness"],
        90,
    ),
    "Cystitis UTI": (
        ["Frequent urination", "Painful urination", "Lower abdominal pain"],
        ["Pelvic pain", "Blood in urine"],
        ["Fever", "Weakness", "Back pain"],
        120,
    ),
    "Helicobacteriosis PepticUlcer": (
        ["Burning stomach pain", "Nausea", "Heartburn"],
        ["Bloating", "Loss of appetite", "Vomiting"],
        ["Weight loss", "Abdominal pain", "Weakness"],
        80,
    ),
    "Common Cold": (
        ["Runny nose", "Sore throat", "Sneezing", "Mild fever"],
        ["Cough", "Headache", "Nasal congestion"],
        ["Fatigue", "Weakness", "Loss of appetite"],
        160,
    ),
    "Skin Fungal Infection": (
        ["Itchy skin", "Ring-shaped rash", "Red scaly skin"],
        ["Skin peeling", "Skin lesions"],
        ["Cracked skin", "Rash", "Hair loss"],
        90,
    ),
    # ── 30 new diseases ───────────────────────────────────────────────────────
    "Hepatitis A": (
        ["Jaundice", "Fatigue", "Dark urine", "Loss of appetite"],
        ["Nausea", "Vomiting", "Abdominal pain", "Fever"],
        ["Yellow eyes", "Muscle aches", "Weakness"],
        90,
    ),
    "Hepatitis B": (
        ["Jaundice", "Yellow eyes", "Dark urine", "Fatigue"],
        ["Abdominal pain", "Joint pain", "Nausea", "Loss of appetite"],
        ["Fever", "Vomiting", "Skin lesions"],
        90,
    ),
    "Yellow Fever": (
        ["High fever", "Jaundice", "Muscle aches", "Severe headache"],
        ["Nausea", "Vomiting", "Back pain", "Yellow eyes"],
        ["Dark urine", "Nose bleeding", "Weakness"],
        80,
    ),
    "Whooping Cough": (
        ["Cough", "Runny nose", "Sneezing"],
        ["Fever", "Vomiting", "Fatigue"],
        ["Weakness", "Loss of appetite", "Headache"],
        90,
    ),
    "Mumps": (
        ["Swollen lymph nodes", "Jaw stiffness", "Fever"],
        ["Headache", "Muscle aches", "Fatigue"],
        ["Loss of appetite", "Weakness", "Neck pain"],
        80,
    ),
    "Rubella": (
        ["Mild fever", "Rash", "Swollen lymph nodes"],
        ["Red eyes", "Runny nose", "Headache"],
        ["Joint pain", "Fatigue", "Sneezing"],
        80,
    ),
    "Sinusitis": (
        ["Headache", "Nasal congestion", "Facial pain"],
        ["Runny nose", "Cough", "Sore throat"],
        ["Fever", "Fatigue", "Loss of appetite"],
        90,
    ),
    "Tonsillitis": (
        ["Sore throat", "Difficulty swallowing", "Swollen lymph nodes", "High fever"],
        ["Headache", "Fatigue", "Loss of appetite"],
        ["Body aches", "Weakness", "Ear pain"],
        80,
    ),
    "Ear Infection": (
        ["Ear pain", "Fever", "Hearing loss"],
        ["Headache", "Dizziness", "Fatigue"],
        ["Pus or discharge", "Nausea", "Neck pain"],
        80,
    ),
    "Conjunctivitis": (
        ["Red eyes", "Eye discharge", "Itchy skin"],
        ["Eye pain", "Sensitivity to light", "Headache"],
        ["Runny nose", "Sneezing", "Nasal congestion"],
        80,
    ),
    "Herpes Zoster": (
        ["Blisters", "Rash", "Itchy rash", "Skin sores"],
        ["Fever", "Fatigue", "Sensitivity to light"],
        ["Headache", "Muscle aches", "Weakness"],
        80,
    ),
    "Appendicitis": (
        ["Abdominal pain", "Fever", "Nausea"],
        ["Vomiting", "Loss of appetite", "Weakness"],
        ["Constipation", "Diarrhea", "Back pain"],
        90,
    ),
    "Kidney Stones": (
        ["Back pain", "Blood in urine", "Painful urination"],
        ["Nausea", "Vomiting", "Frequent urination"],
        ["Fever", "Lower abdominal pain", "Dehydration"],
        90,
    ),
    "Sickle Cell Crisis": (
        ["Joint pain", "Fatigue", "Pale skin"],
        ["Chest pain", "Shortness of breath", "Jaundice"],
        ["Swollen feet", "Yellow eyes", "Weakness"],
        80,
    ),
    "Tetanus": (
        ["Jaw stiffness", "Stiff neck", "Muscle cramps"],
        ["Fever", "Headache", "Difficulty swallowing"],
        ["Sweating", "Seizures", "Weakness"],
        80,
    ),
    "Diphtheria": (
        ["Sore throat", "Hoarse voice", "Difficulty swallowing"],
        ["Fever", "Swollen lymph nodes", "Fatigue"],
        ["Runny nose", "Loss of appetite", "Headache"],
        80,
    ),
    "Ringworm": (
        ["Ring-shaped rash", "Itchy skin", "Red scaly skin"],
        ["Skin peeling", "Skin lesions"],
        ["Hair loss", "Cracked skin", "Rash"],
        80,
    ),
    "Leptospirosis": (
        ["High fever", "Muscle aches", "Headache", "Red eyes"],
        ["Jaundice", "Vomiting", "Rash"],
        ["Dark urine", "Cough", "Weakness"],
        80,
    ),
    "Typhus": (
        ["Sudden high fever", "Severe headache", "Rash"],
        ["Muscle aches", "Fatigue", "Confusion"],
        ["Chills", "Weakness", "Cough"],
        80,
    ),
    "Brucellosis": (
        ["Fever", "Sweating", "Joint pain", "Muscle aches"],
        ["Fatigue", "Loss of appetite", "Back pain"],
        ["Night sweats", "Weight loss", "Headache"],
        80,
    ),
    "Septicemia": (
        ["High fever", "Confusion", "Fast heartbeat"],
        ["Shortness of breath", "Low blood pressure", "Chills"],
        ["Rash", "Sweating", "Weakness"],
        80,
    ),
    "Pelvic Inflammatory Disease": (
        ["Pelvic pain", "Vaginal discharge", "Lower abdominal pain"],
        ["Fever", "Painful urination"],
        ["Missed period", "Pain during intercourse", "Nausea"],
        80,
    ),
    "Benign Prostatic Hyperplasia": (
        ["Frequent urination", "Reduced urination", "Sleep disturbances"],
        ["Lower abdominal pain", "Weakness"],
        ["Back pain", "Blood in urine", "Fatigue"],
        80,
    ),
    "Migraine": (
        ["Severe headache", "Sensitivity to light", "Sensitivity to sound", "Nausea"],
        ["Vomiting", "Blurred vision", "Dizziness"],
        ["Weakness", "Fatigue", "Numbness"],
        90,
    ),
    "Epilepsy": (
        ["Seizures", "Confusion", "Confusion at night"],
        ["Muscle cramps", "Fatigue", "Weakness"],
        ["Poor coordination", "Dizziness", "Body aches"],
        80,
    ),
    "Onchocerciasis": (
        ["Severe itching", "Skin lesions", "Blurred vision"],
        ["Rash", "Skin peeling", "Swollen lymph nodes"],
        ["Weight loss", "Itchy skin", "Eye pain"],
        70,
    ),
    "Filariasis": (
        ["Swollen feet", "Ankle swelling", "Skin lesions"],
        ["Fever", "Skin sores", "Weakness"],
        ["Itchy skin", "Pain during intercourse", "Fatigue"],
        70,
    ),
    "HIV AIDS": (
        ["Fatigue", "Weight loss", "Night sweats", "Swollen lymph nodes"],
        ["Diarrhea", "Fever", "Rash", "Loss of appetite"],
        ["Cough", "Sore throat", "White patches in mouth"],
        90,
    ),
    "Skin Abscess": (
        ["Skin sores", "Pus or discharge", "Rash"],
        ["Fever", "Fatigue"],
        ["Swollen lymph nodes", "Headache", "Weakness"],
        80,
    ),
    "Anaphylaxis": (
        ["Rash", "Shortness of breath", "Fast heartbeat", "Dizziness"],
        ["Low blood pressure", "Nausea", "Swollen feet"],
        ["Vomiting", "Abdominal pain", "Confusion"],
        70,
    ),
    # ── STIs ──────────────────────────────────────────────────────────────────
    "Gonorrhea": (
        ["Genital discharge", "Painful urination"],
        ["Pelvic pain", "Vaginal discharge", "Vaginal itching"],
        ["Sore throat", "Swollen lymph nodes", "Fever"],
        70,
    ),
    "Syphilis": (
        ["Genital sores", "Rash"],
        ["Swollen lymph nodes", "Fever", "Fatigue"],
        ["Headache", "Muscle aches", "Skin sores"],
        70,
    ),
    "Chlamydia": (
        ["Genital discharge", "Painful urination", "Pelvic pain"],
        ["Vaginal discharge", "Vaginal itching"],
        ["Pain during intercourse", "Lower abdominal pain", "Fatigue"],
        70,
    ),
    "Genital Herpes": (
        ["Genital sores", "Blisters", "Painful urination"],
        ["Fever", "Fatigue", "Muscle aches"],
        ["Vaginal itching", "Skin sores", "Swollen lymph nodes"],
        70,
    ),
    "Trichomoniasis": (
        ["Vaginal itching", "Genital discharge"],
        ["Painful urination", "Vaginal discharge", "Pelvic pain"],
        ["Rash", "Lower abdominal pain", "Fatigue"],
        70,
    ),
}

DISEASE_NAMES = list(DISEASE_PROFILES.keys())


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_record(disease: str, core: list, secondary: list, occasional: list) -> dict:
    row: dict[str, int | str] = {s: 0 for s in ALL_SYMPTOMS}
    for s in ALL_SYMPTOMS:
        if s in core:
            row[s] = 1 if random.random() < 0.90 else 0
        elif s in secondary:
            row[s] = 1 if random.random() < 0.60 else 0
        elif s in occasional:
            row[s] = 1 if random.random() < 0.25 else 0
        else:
            row[s] = 1 if random.random() < 0.05 else 0
    row["disease"] = disease
    return row


def generate_dataset() -> list[dict]:
    dataset: list[dict] = []
    for disease, (core, secondary, occasional, n) in DISEASE_PROFILES.items():
        for _ in range(n):
            dataset.append(generate_record(disease, core, secondary, occasional))
    random.shuffle(dataset)
    return dataset


def stratified_split(dataset: list[dict], test_ratio: float = 0.2):
    by_disease: dict[str, list] = defaultdict(list)
    for row in dataset:
        by_disease[row["disease"]].append(row)

    train, test = [], []
    for rows in by_disease.values():
        random.shuffle(rows)
        n_test = max(1, math.ceil(len(rows) * test_ratio))
        test.extend(rows[:n_test])
        train.extend(rows[n_test:])

    random.shuffle(train)
    random.shuffle(test)
    return train, test


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ALL_SYMPTOMS + ["disease"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Wrote {len(rows)} rows -> {path}")


# ---------------------------------------------------------------------------
# Model training (uses shared SimpleSymptomModel from app.ml.simple_model)
# ---------------------------------------------------------------------------

def train_model(symptoms: list[str], rows: list[dict], variant: str) -> SimpleSymptomModel:
    class_counts = Counter(row["disease"] for row in rows)
    classes = sorted(class_counts)
    total = len(rows)
    symptom_counts: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        disease = row["disease"]
        for s in symptoms:
            if int(row[s]):
                symptom_counts[disease][s] += 1

    log_priors = {d: math.log(c / total) for d, c in class_counts.items()}
    log_likelihoods = {}
    for disease in classes:
        log_likelihoods[disease] = {}
        for s in symptoms:
            present = symptom_counts[disease][s]
            log_likelihoods[disease][s] = (present + 1) / (class_counts[disease] + 2)

    return SimpleSymptomModel(symptoms, classes, log_priors, log_likelihoods, variant)


def evaluate(model: SimpleSymptomModel, rows: list[dict]) -> float:
    correct = 0
    for row in rows:
        selected = [s for s in model.symptoms if int(row[s])]
        pred = model.predict_ranked(selected, top_k=1)[0]["disease"]
        correct += pred == row["disease"]
    return correct / len(rows)


def dump_pickle(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        pickle.dump(obj, f)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    base = Path(__file__).parent.parent  # mediguard-backend/

    print("Generating 50-disease dataset …")
    dataset = generate_dataset()
    print(f"  Total records: {len(dataset)}")
    print(f"  Diseases: {len(DISEASE_PROFILES)}")

    train_rows, test_rows = stratified_split(dataset, test_ratio=0.2)
    print(f"  Train: {len(train_rows)}  Test: {len(test_rows)}")

    write_csv(base / "data/raw/mediguard_dataset_full.csv", dataset)
    write_csv(base / "data/processed/mediguard_train.csv", train_rows)
    write_csv(base / "data/processed/mediguard_test.csv", test_rows)

    # Update symptoms_list.json
    symptoms_path = base / "data_pipeline/symptoms_list.json"
    symptoms_path.write_text(json.dumps(ALL_SYMPTOMS, indent=2), encoding="utf-8")
    print(f"  Updated {symptoms_path} ({len(ALL_SYMPTOMS)} symptoms)")

    # Also write to models/symptoms_list.json
    models_symptoms = base / "models/symptoms_list.json"
    models_symptoms.parent.mkdir(exist_ok=True)
    models_symptoms.write_text(json.dumps(ALL_SYMPTOMS, indent=2), encoding="utf-8")

    print("\nTraining models …")
    for name, variant in [
        ("random_forest", "random_forest_fallback"),
        ("decision_tree", "decision_tree_fallback"),
        ("naive_bayes", "naive_bayes_fallback"),
    ]:
        model = train_model(ALL_SYMPTOMS, train_rows, variant)
        acc = evaluate(model, test_rows)
        dump_pickle(base / f"models/{name}.pkl", model)
        print(f"  {name}: test_accuracy={acc:.4f}")

    classes = sorted({row["disease"] for row in train_rows})
    dump_pickle(base / "models/label_encoder.pkl", SimpleLabelEncoder(classes))
    print(f"\nDone. {len(DISEASE_PROFILES)} diseases, {len(ALL_SYMPTOMS)} symptoms.")


if __name__ == "__main__":
    main()
