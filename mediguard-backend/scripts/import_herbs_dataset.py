"""
import_herbs_dataset.py
=======================
Converts the Cameroon herbs / traditional remedies CSV into:

  data/herbs_remedies.json   — disease -> herb recommendations lookup
                               (used by the predict endpoint to suggest
                               traditional remedies alongside diagnosis)

NOTE: Herb rows are NOT merged into the symptom-disease training set.
The classifier is trained on Kaggle patient datasets (97% accuracy).
Adding herb rows would introduce broad, overlapping symptom profiles that
degrade accuracy. The remedy lookup is the correct use for herbs data.

Sources:
  data/custom/cameroon_herbs_remedies.csv
  — compiled from published ethnobotanical surveys of NW Cameroon / Bamenda
    (Jiofack et al. 2010; Telefo et al. 2011; Focho et al. 2009;
    IMPM Yaounde monographs; University of Buea ethnobotany studies)

Run from mediguard-backend/ root:
    python scripts/import_herbs_dataset.py
"""

import csv
import json
import math
import pickle
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.ml.simple_model import SimpleLabelEncoder, SimpleSymptomModel  # noqa: E402

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
BASE = Path(__file__).parent.parent

# ── Master symptom list (keep in sync with build_real_dataset.py) ─────────────
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

# Number of synthetic training rows to generate per herb record
ROWS_PER_HERB = 40

# ── Map herb CSV disease names -> MediGuard standard disease names ─────────────
# Keys are anything that appears in the herbs CSV diseases_treated column.
# A None value means "skip" (symptom used as disease name, not a real disease).
HERBS_DISEASE_MAP: dict[str, str | None] = {
    # Standard names — pass through unchanged
    "Malaria":                        "Malaria",
    "Typhoid Fever":                  "Typhoid Fever",
    "Dengue Fever":                   "Dengue Fever",
    "Yellow Fever":                   "Yellow Fever",
    "Cholera":                        "Cholera",
    "Dysentery":                      "Dysentery",
    "Gastroenteritis":                "Gastroenteritis",
    "Hepatitis A":                    "Hepatitis A",
    "Hepatitis B":                    "Hepatitis B",
    "Pneumonia":                      "Pneumonia",
    "Tuberculosis":                   "Tuberculosis",
    "Asthma":                         "Asthma",
    "Whooping Cough":                 "Whooping Cough",
    "Epilepsy":                       "Epilepsy",
    "Meningitis":                     "Meningitis",
    "Chickenpox":                     "Chickenpox",
    "Measles":                        "Measles",
    "Diabetes Mellitus":              "Diabetes Mellitus",
    "Hypertension":                   "Hypertension",
    "Ringworm":                       "Ringworm",
    "Scabies":                        "Scabies",
    "Skin Fungal Infection":          "Skin Fungal Infection",
    "Skin Abscess":                   "Skin Abscess",
    "Herpes Zoster":                  "Herpes Zoster",
    "Conjunctivitis":                 "Conjunctivitis",
    "Cystitis UTI":                   "Cystitis UTI",
    "Pelvic Inflammatory Disease":    "Pelvic Inflammatory Disease",
    "Kidney Stones":                  "Kidney Stones",
    "Iron Deficiency Anemia":         "Iron Deficiency Anemia",
    "Sickle Cell Crisis":             "Sickle Cell Crisis",
    "Gonorrhea":                      "Gonorrhea",
    "Syphilis":                       "Syphilis",
    "Intestinal Worms":               "Intestinal Worms",
    "Malnutrition":                   "Malnutrition",
    "Dental Abscess":                 "Dental Abscess",
    "Arthritis":                      "Arthritis",
    "Eczema":                         "Eczema",
    "Helicobacteriosis PepticUlcer":  "Helicobacteriosis PepticUlcer",
    "Common Cold":                    "Common Cold",
    "HIV AIDS":                       "HIV AIDS",
    # Non-standard -> map to nearest MediGuard disease
    "Wound infections":               "Skin Abscess",
    "Wounds":                         "Skin Abscess",
    "Skin infections":                "Skin Fungal Infection",
    "Skin conditions":                "Eczema",
    "Anemia":                         "Iron Deficiency Anemia",
    "Bronchitis":                     "Pneumonia",
    "Toothache":                      "Dental Abscess",
    "Stomach pain":                   "Gastroenteritis",
    "Diarrhea":                       "Gastroenteritis",
    # Symptoms used as disease names — skip these for training rows
    # (still kept in remedy_lookup under the original name)
    "Cough":                          None,
    "Headache":                       None,
    "Constipation":                   None,
    "Sexually transmitted infections": None,
}


def _normalize_disease(raw: str) -> str | None:
    """Map a raw disease name from the herbs CSV to a MediGuard standard name.
    Returns None if the name should be skipped for training rows.
    Unknown names are passed through as-is (they will be excluded from training
    rows that don't match the label encoder's known classes).
    """
    return HERBS_DISEASE_MAP.get(raw, raw)   # unknown names pass through


def _parse_list(raw: str) -> list[str]:
    return [s.strip() for s in raw.split(",") if s.strip()]


def _blank_row(disease: str) -> dict:
    row = {s: "0" for s in ALL_SYMPTOMS}
    row["disease"] = disease
    return row


def herbs_to_training_rows(herbs_csv: Path) -> tuple[list[dict], dict]:
    """Convert herbs CSV to:
       - training rows (symptom-disease binary format)
       - remedy lookup dict { disease: [{ herb, local_name, preparation }, ...] }
    """
    training_rows: list[dict] = []
    remedy_lookup: dict[str, list[dict]] = defaultdict(list)

    with herbs_csv.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for record in reader:
            herb      = record["herb_name"].strip()
            local     = record["local_name"].strip()
            diseases  = _parse_list(record["diseases_treated"])
            symptoms  = _parse_list(record["symptoms_addressed"])
            prep      = record["preparation"].strip()
            region    = record.get("source_region", "").strip()

            # Filter symptoms to those in the master list
            valid_syms = [s for s in symptoms if s in SYMPTOM_SET]

            for raw_disease in diseases:
                # Always store in remedy lookup under the original raw name
                remedy_lookup[raw_disease].append({
                    "herb": herb,
                    "local_name": local,
                    "preparation": prep,
                    "symptoms_treated": valid_syms,
                    "region": region,
                })

                # Normalize disease name for training rows
                disease = _normalize_disease(raw_disease)
                if disease is None or not valid_syms:
                    # Skip symptom-names-used-as-diseases or unmapped entries
                    continue

                # Also store under the normalised name so the predict endpoint
                # can look up by MediGuard disease name
                if disease != raw_disease:
                    remedy_lookup[disease].append({
                        "herb": herb,
                        "local_name": local,
                        "preparation": prep,
                        "symptoms_treated": valid_syms,
                        "region": region,
                    })

                # Generate training rows:
                # Each row has the herb's core symptoms (85% probability)
                # + noise floor (3% for unrelated symptoms)
                for _ in range(ROWS_PER_HERB):
                    row = _blank_row(disease)
                    for sym in ALL_SYMPTOMS:
                        if sym in valid_syms:
                            row[sym] = "1" if random.random() < 0.85 else "0"
                        else:
                            row[sym] = "1" if random.random() < 0.03 else "0"
                    training_rows.append(row)

    return training_rows, dict(remedy_lookup)


def load_existing_rows(path: Path) -> list[dict]:
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


def main() -> None:
    herbs_csv = BASE / "data/custom/cameroon_herbs_remedies.csv"
    if not herbs_csv.exists():
        print(f"ERROR: {herbs_csv} not found.")
        return

    print("Building Cameroon herbs remedy lookup ...")
    _, remedy_lookup = herbs_to_training_rows(herbs_csv)

    print(f"  Diseases with remedies: {len(remedy_lookup)}")
    total_herbs = sum(len(v) for v in remedy_lookup.values())
    print(f"  Total herb entries:     {total_herbs}")
    for d in sorted(remedy_lookup):
        names = [h["herb"] for h in remedy_lookup[d]]
        print(f"    {d}: {', '.join(names[:3])}{'...' if len(names) > 3 else ''}")

    # Save remedy lookup JSON (used by the predict endpoint)
    remedies_out = BASE / "data/herbs_remedies.json"
    remedies_out.parent.mkdir(parents=True, exist_ok=True)
    with remedies_out.open("w", encoding="utf-8") as f:
        json.dump(remedy_lookup, f, indent=2, ensure_ascii=False)

    print(f"\nRemedy lookup saved -> {remedies_out}")
    print("Classifier models are NOT retrained here (97% accuracy preserved).")
    print("Run 'python scripts/upload_to_hf.py' to push models + herbs lookup to HuggingFace.")


if __name__ == "__main__":
    main()
