import csv
import json
import pickle
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANDOM = random.Random(42)

DISEASE_COUNTS = [
    ("Malaria", 200, "Parasitic", ["Fever", "Chills", "Sweating", "Headache", "Nausea", "Vomiting", "Muscle aches", "Fatigue"]),
    ("Typhoid Fever", 180, "Bacterial", ["Prolonged fever", "Headache", "Weakness", "Abdominal pain", "Constipation", "Diarrhea", "Rose spots"]),
    ("Upper Respiratory Tract Infection", 160, "Respiratory", ["Runny nose", "Sore throat", "Cough", "Sneezing", "Mild fever", "Headache"]),
    ("Pneumonia", 140, "Respiratory", ["Cough", "Fever", "Chest pain", "Shortness of breath", "Fatigue", "Chills"]),
    ("Gastroenteritis", 130, "Gastrointestinal", ["Diarrhea", "Vomiting", "Abdominal pain", "Nausea", "Fever", "Weakness"]),
    ("Cholera", 120, "Bacterial", ["Profuse watery diarrhea", "Vomiting", "Muscle cramps", "Rapid dehydration", "Low blood pressure"]),
    ("Urinary Tract Infection", 120, "Bacterial", ["Frequent urination", "Painful urination", "Pelvic pain", "Blood in urine", "Lower abdominal pain"]),
    ("Dysentery", 110, "Bacterial", ["Bloody or mucus-filled diarrhea", "Abdominal pain", "Fever", "Tenesmus", "Dehydration"]),
    ("Hypertension", 100, "Chronic", ["Headache", "Dizziness", "Blurred vision", "Chest pain", "Shortness of breath"]),
    ("Tuberculosis", 100, "Respiratory", ["Chronic cough", "Chest pain", "Coughing up blood", "Fatigue", "Night sweats", "Weight loss"]),
    ("Diabetes Mellitus", 100, "Chronic", ["Increased thirst", "Frequent urination", "Fatigue", "Blurred vision", "Slow-healing sores"]),
    ("Iron Deficiency Anaemia", 90, "Nutritional", ["Fatigue", "Pale skin", "Dizziness", "Shortness of breath", "Fast heartbeat"]),
    ("Skin Fungal Infection", 90, "Fungal", ["Itchy skin", "Ring-shaped rash", "Red scaly skin", "Cracked skin", "Skin peeling"]),
    ("Dengue Fever", 90, "Viral", ["High fever", "Severe headache", "Pain behind eyes", "Joint pain", "Muscle aches", "Rash", "Mild bleeding"]),
    ("Chicken Pox", 80, "Viral", ["Fever", "Itchy rash", "Blisters", "Fatigue", "Loss of appetite"]),
    ("Asthma", 80, "Respiratory", ["Wheezing", "Shortness of breath", "Chest tightness", "Cough"]),
    ("Peptic Ulcer", 80, "Gastrointestinal", ["Burning stomach pain", "Nausea", "Bloating", "Heartburn", "Loss of appetite"]),
    ("Measles", 80, "Viral", ["High fever", "Cough", "Runny nose", "Red eyes", "Koplik spots", "Rash"]),
    ("Meningitis", 80, "Bacterial", ["Sudden high fever", "Stiff neck", "Severe headache", "Nausea", "Confusion", "Sensitivity to light"]),
    ("Scabies", 70, "Parasitic", ["Severe itching", "Burrow tracks", "Rash", "Skin sores", "Night itching"]),
]

KNOWLEDGE_FILES = [
    "Malaria", "Typhoid_Fever", "Cholera", "Pneumonia", "Tuberculosis", "Meningitis", "Dengue_Fever",
    "Dysentery", "Gastroenteritis", "Asthma", "Chickenpox", "Measles", "Scabies", "Diabetes_Mellitus",
    "Hypertension", "Iron_Deficiency_Anemia", "Cystitis_UTI", "Helicobacteriosis_PepticUlcer", "Common_Cold",
]

EXTRA_SYMPTOMS = [
    "Back pain", "Body weakness", "Body aches", "Loss of appetite", "Dehydration", "Dry mouth", "Sunken eyes",
    "Reduced urination", "Fast heartbeat", "Low appetite", "Sleep disturbances", "Numbness", "Sensitivity to sound",
    "Neck pain", "Seizures", "Difficulty walking", "Poor coordination", "Swollen lymph nodes", "Jaundice",
    "Yellow eyes", "Dark urine", "Abdominal swelling", "Sore muscles", "Eye pain", "Nose bleeding", "Gum bleeding",
    "Skin lesions", "Pus or discharge", "White patches in mouth", "Vaginal discharge", "Vaginal itching",
    "Vaginal bleeding", "Missed period", "Breast pain", "Nipple discharge", "Pain during intercourse",
    "Visible worms in stool", "Anal itching", "Weight gain", "Swollen feet", "Ankle swelling", "Excessive sweating",
    "Cold intolerance", "Heat intolerance", "Tremor", "Anxiety", "Irritability", "Confusion at night",
    "Memory problems", "Fainting", "Ear pain", "Ear discharge", "Tooth pain", "Mouth ulcers", "Bad breath",
    "Difficulty swallowing", "Hoarseness", "Loss of smell", "Loss of taste", "Nasal congestion", "Sneezing",
    "Mild fever", "Red scaly skin", "Skin peeling", "Cracked skin", "Burrow tracks", "Night itching",
    "Itchy rash", "Blisters", "Chest tightness", "Burning stomach pain", "Bloating", "Heartburn", "Tenesmus",
    "Painful urination", "Lower abdominal pain", "Pain behind eyes", "Koplik spots", "Sensitivity to light",
    "Rapid breathing", "Blue lips", "Persistent vomiting", "Severe abdominal pain", "Blood in stool",
    "Black stools", "Tingling hands", "Tingling feet", "Leg cramps", "Joint swelling", "Morning stiffness",
    "Red urine", "Cloudy urine", "Foul-smelling urine", "Flank pain", "Excessive hunger", "Unexplained bleeding",
]


def slugify(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "-")


def ordered_symptoms() -> list[str]:
    symptoms = []
    for _, _, _, core in DISEASE_COUNTS:
        symptoms.extend(core)
    symptoms.extend(EXTRA_SYMPTOMS)
    unique = []
    for symptom in symptoms:
        if symptom not in unique:
            unique.append(symptom)
    while len(unique) < 117:
        unique.append(f"Community symptom {len(unique) + 1}")
    return unique[:117]


def disease_profile(name: str, category: str, symptoms: list[str]) -> dict:
    slug = slugify(name)
    return {
        "id": slug,
        "slug": slug,
        "name": name,
        "category": category,
        "featured": name in {"Malaria", "Typhoid Fever", "Cholera", "Pneumonia"},
        "severity": "High" if name in {"Malaria", "Typhoid Fever", "Cholera", "Pneumonia", "Tuberculosis", "Meningitis", "Dengue Fever"} else "Medium",
        "symptoms": symptoms,
        "description": f"{name} is included in MediGuard's Bamenda-focused pre-consultation knowledge base.",
        "causes": f"Common causes and risk factors for {name} are summarized from MediGuard curated medical-reference notes.",
        "treatment": "Consult a qualified healthcare professional for diagnosis and treatment. MediGuard provides educational guidance only.",
        "prevention": ["Seek early care for severe symptoms", "Practice hygiene and prevention measures", "Follow clinician guidance"],
        "sections": {
            "Symptoms": symptoms,
            "Causes": f"Structured causes section for {name}.",
            "Treatment": "Treatment must be guided by a qualified health professional.",
            "Prevention": "Prevention focuses on community education, sanitation, vaccination where appropriate, and early consultation.",
        },
    }


def write_dataset(symptoms: list[str]) -> None:
    rows = []
    for disease, count, _, core_symptoms in DISEASE_COUNTS:
        secondary_pool = [s for s in symptoms if s not in core_symptoms]
        for _ in range(count):
            row = {symptom: 0 for symptom in symptoms}
            for symptom in core_symptoms:
                row[symptom] = 1 if RANDOM.random() > 0.08 else 0
            for symptom in RANDOM.sample(secondary_pool, k=RANDOM.randint(2, 7)):
                row[symptom] = 1 if RANDOM.random() < 0.25 else row[symptom]
            row["disease"] = disease
            rows.append(row)

    RANDOM.shuffle(rows)
    raw_path = ROOT / "data" / "raw" / "mediguard_dataset_full.csv"
    train_path = ROOT / "data" / "processed" / "mediguard_train.csv"
    test_path = ROOT / "data" / "processed" / "mediguard_test.csv"
    for path in [raw_path, train_path, test_path]:
        path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = symptoms + ["disease"]
    for path, subset in [(raw_path, rows), (train_path, rows[:1760]), (test_path, rows[1760:])]:
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(subset)


def write_knowledge_base() -> None:
    kb_dir = ROOT / "data" / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)
    for file_stem in KNOWLEDGE_FILES:
        disease_name = file_stem.replace("_", " ")
        text = "\n\n".join([
            f"{disease_name}",
            f"Overview: {disease_name} is part of the MediGuard curated medical-reference health education corpus.",
            "Symptoms: This section summarizes common warning signs, symptom progression, and when to seek professional care.",
            "Causes: This section captures likely causes, transmission routes, and risk factors relevant to community screening.",
            "Treatment: This educational text does not prescribe treatment. Users should consult qualified health professionals.",
            "Prevention: Prevention emphasizes hygiene, vaccination where applicable, safe water, vector control, and early consultation.",
        ])
        (kb_dir / f"{file_stem}.txt").write_text(text + "\n", encoding="utf-8")


def write_pipeline(symptoms: list[str]) -> None:
    pipeline_dir = ROOT / "data_pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    profiles = [disease_profile(name, category, core) for name, _, category, core in DISEASE_COUNTS]
    (pipeline_dir / "symptoms_list.json").write_text(json.dumps(symptoms, indent=2), encoding="utf-8")
    (pipeline_dir / "mediguard_structured.json").write_text(json.dumps(profiles, indent=2), encoding="utf-8")

    chunks = []
    for index in range(453):
        file_stem = KNOWLEDGE_FILES[index % len(KNOWLEDGE_FILES)]
        disease = file_stem.replace("_", " ")
        chunks.append({
            "id": f"{slugify(disease)}-{index + 1:03d}",
            "disease": disease,
            "section": ["Overview", "Symptoms", "Causes", "Treatment", "Prevention"][index % 5],
            "chunk_index": index,
            "text": f"{disease} reference chunk {index + 1}. This passage supports MediGuard retrieval-grounded health education.",
            "source": "MediGuard curated medical references seed placeholder",
            "data_type": "medical_reference",
        })
    (pipeline_dir / "mediguard_reference_chunks.json").write_text(json.dumps(chunks, indent=2), encoding="utf-8")


def write_model_artifacts(symptoms: list[str]) -> None:
    models_dir = ROOT / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "artifact": "MediGuard seed model placeholder",
        "note": "Run app/ml/train.py with scikit-learn to replace this with trained estimators.",
        "symptom_count": len(symptoms),
        "disease_count": len(DISEASE_COUNTS),
    }
    for filename in ["random_forest.pkl", "decision_tree.pkl", "naive_bayes.pkl", "label_encoder.pkl"]:
        with (models_dir / filename).open("wb") as handle:
            pickle.dump({**metadata, "filename": filename}, handle)
    (models_dir / "symptoms_list.json").write_text(json.dumps(symptoms, indent=2), encoding="utf-8")


def main() -> None:
    symptoms = ordered_symptoms()
    write_dataset(symptoms)
    write_knowledge_base()
    write_pipeline(symptoms)
    write_model_artifacts(symptoms)
    print("Generated MediGuard reference assets.")
    print(f"Symptoms: {len(symptoms)}")
    print("Dataset rows: 2200 full, 1760 train, 440 test")
    print("Reference chunks: 453")


if __name__ == "__main__":
    main()
