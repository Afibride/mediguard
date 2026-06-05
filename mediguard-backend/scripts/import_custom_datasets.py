"""
import_custom_datasets.py
=========================
Imports real patient-diagnosis CSVs (one disease per file) into MediGuard's
binary symptom format, merges with existing training data, and retrains models.

HOW TO USE
──────────
1. Drop your CSV files into  data/custom/
2. Register each file in DATASET_CONFIGS below (column map + disease label).
3. Run from mediguard-backend/ root:
       python scripts/import_custom_datasets.py

   Flags:
       --no-synthetic   Train on real data only (skip existing synthetic base)
       --dry-run        Parse and show stats; do not overwrite data or models
       --list           Print registered dataset configs and exit

OUTPUTS
───────
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
import json
import math
import pickle
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.ml.simple_model import SimpleLabelEncoder, SimpleSymptomModel  # noqa: E402

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
BASE = Path(__file__).parent.parent

# ── MediGuard master symptom list ─────────────────────────────────────────────
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
# Dataset configuration
# ─────────────────────────────────────────────────────────────────────────────

class DatasetConfig(NamedTuple):
    filename: str           # CSV filename inside data/custom/
    disease: str            # MediGuard disease label for every row
    col_map: dict           # { csv_column_name: MediGuard_symptom }
    label_col: str = ""     # If set, read disease from this column instead
    label_map: dict = {}    # { csv_label: MediGuard_disease } when label_col used


# ── Column map: Malaria clinical dataset (Kaggle — real hospital records) ─────
_MALARIA_COL_MAP = {
    "Fever":               "Fever",
    "Headache":            "Headache",
    "Abdominal_Pain":      "Abdominal pain",
    "General_Body_Malaise":"Fatigue",
    "Dizziness":           "Dizziness",
    "Vomiting":            "Vomiting",
    "Confusion":           "Confusion",
    "Backache":            "Back pain",
    "Chest_Pain":          "Chest pain",
    "Coughing":            "Cough",
    "Joint_Pain":          "Joint pain",
}

# ── Column map: generic Typhoid CSV (if you find one with similar structure) ──
_TYPHOID_COL_MAP = {
    "Fever":               "Prolonged fever",
    "Headache":            "Headache",
    "Abdominal_Pain":      "Abdominal pain",
    "Weakness":            "Weakness",
    "Vomiting":            "Vomiting",
    "Nausea":              "Nausea",
    "Diarrhea":            "Diarrhea",
    "Constipation":        "Constipation",
    "Loss_of_Appetite":    "Loss of appetite",
}

# ── Column map: Dengue fever CSV ──────────────────────────────────────────────
_DENGUE_COL_MAP = {
    "Fever":               "High fever",
    "Headache":            "Severe headache",
    "Pain_Behind_Eyes":    "Pain behind eyes",
    "Joint_Pain":          "Joint pain",
    "Muscle_Pain":         "Muscle aches",
    "Rash":                "Rash",
    "Vomiting":            "Vomiting",
    "Nausea":              "Nausea",
    "Fatigue":             "Fatigue",
    "Bleeding":            "Mild bleeding",
    "Nosebleed":           "Nose bleeding",
}

# ── Column map: Tuberculosis CSV ──────────────────────────────────────────────
_TB_COL_MAP = {
    "Cough":               "Chronic cough",
    "Night_Sweats":        "Night sweats",
    "Weight_Loss":         "Weight loss",
    "Fatigue":             "Fatigue",
    "Chest_Pain":          "Chest pain",
    "Blood_in_Sputum":     "Coughing up blood",
    "Fever":               "Fever",
    "Weakness":            "Weakness",
    "Loss_of_Appetite":    "Loss of appetite",
}

# ── Column map: Cholera CSV ───────────────────────────────────────────────────
_CHOLERA_COL_MAP = {
    "Watery_Diarrhea":     "Profuse watery diarrhea",
    "Vomiting":            "Vomiting",
    "Dehydration":         "Rapid dehydration",
    "Muscle_Cramps":       "Muscle cramps",
    "Low_Blood_Pressure":  "Low blood pressure",
    "Sunken_Eyes":         "Sunken eyes",
    "Dry_Mouth":           "Dry mouth",
    "Weakness":            "Weakness",
}

# ── Column map: Pneumonia CSV ──────────────────────────────────────────────────
_PNEUMONIA_COL_MAP = {
    "Cough":               "Cough",
    "Fever":               "Fever",
    "Chest_Pain":          "Chest pain",
    "Shortness_of_Breath": "Shortness of breath",
    "Fatigue":             "Fatigue",
    "Chills":              "Chills",
    "Headache":            "Headache",
    "Nausea":              "Nausea",
}

# ── Column map: Hepatitis (A or B) CSV ────────────────────────────────────────
_HEPATITIS_COL_MAP = {
    "Jaundice":            "Jaundice",
    "Yellow_Eyes":         "Yellow eyes",
    "Dark_Urine":          "Dark urine",
    "Fatigue":             "Fatigue",
    "Nausea":              "Nausea",
    "Loss_of_Appetite":    "Loss of appetite",
    "Abdominal_Pain":      "Abdominal pain",
    "Fever":               "Fever",
    "Vomiting":            "Vomiting",
    "Itching":             "Itchy skin",
}

# ── Column map: Diabetes CSV ───────────────────────────────────────────────────
_DIABETES_COL_MAP = {
    "Polyuria":            "Frequent urination",
    "Polydipsia":          "Increased thirst",
    "Weight_Loss":         "Weight loss",
    "Weakness":            "Weakness",
    "Fatigue":             "Fatigue",
    "Blurred_Vision":      "Blurred vision",
    "Slow_Healing_Sores":  "Slow-healing sores",
    "Numbness":            "Numbness",
    "Frequent_Urination":  "Frequent urination",
    "Increased_Thirst":    "Increased thirst",
}

# ── Column map: COVID-19 CSV ───────────────────────────────────────────────────
_COVID_COL_MAP = {
    "Fever":               "Fever",
    "Cough":               "Cough",
    "Fatigue":             "Fatigue",
    "Loss_of_Taste":       "Loss of taste",
    "Loss_of_Smell":       "Loss of smell",
    "Muscle_Aches":        "Muscle aches",
    "Headache":            "Headache",
    "Shortness_of_Breath": "Shortness of breath",
    "Sore_Throat":         "Sore throat",
    "Diarrhea":            "Diarrhea",
    "Runny_Nose":          "Runny nose",
}

# ── Column map: HIV/AIDS symptomatic CSV ──────────────────────────────────────
_HIV_COL_MAP = {
    "Weight_Loss":         "Weight loss",
    "Fatigue":             "Fatigue",
    "Night_Sweats":        "Night sweats",
    "Swollen_Lymph_Nodes": "Swollen lymph nodes",
    "Fever":               "Fever",
    "Loss_of_Appetite":    "Loss of appetite",
    "Diarrhea":            "Diarrhea",
    "Cough":               "Cough",
    "Sore_Throat":         "Sore throat",
    "Rash":                "Rash",
    "Weakness":            "Weakness",
}

# ─────────────────────────────────────────────────────────────────────────────
# REGISTER DATASETS HERE
# Add one DatasetConfig per CSV file you place in data/custom/
# ─────────────────────────────────────────────────────────────────────────────
DATASET_CONFIGS: list[DatasetConfig] = [

    # ── Real hospital Malaria records (the file you shared) ───────────────────
    DatasetConfig(
        filename="Malaria_Dataset.csv",
        disease="Malaria",
        col_map=_MALARIA_COL_MAP,
    ),

    # ── Uncomment and add the matching CSV to data/custom/ to activate ────────

    # DatasetConfig(
    #     filename="Typhoid_Dataset.csv",
    #     disease="Typhoid Fever",
    #     col_map=_TYPHOID_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="Dengue_Dataset.csv",
    #     disease="Dengue Fever",
    #     col_map=_DENGUE_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="Tuberculosis_Dataset.csv",
    #     disease="Tuberculosis",
    #     col_map=_TB_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="Cholera_Dataset.csv",
    #     disease="Cholera",
    #     col_map=_CHOLERA_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="Pneumonia_Dataset.csv",
    #     disease="Pneumonia",
    #     col_map=_PNEUMONIA_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="Hepatitis_A_Dataset.csv",
    #     disease="Hepatitis A",
    #     col_map=_HEPATITIS_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="Hepatitis_B_Dataset.csv",
    #     disease="Hepatitis B",
    #     col_map=_HEPATITIS_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="Diabetes_Dataset.csv",
    #     disease="Diabetes Mellitus",
    #     col_map=_DIABETES_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="COVID19_Dataset.csv",
    #     disease="COVID-19",
    #     col_map=_COVID_COL_MAP,
    # ),

    # DatasetConfig(
    #     filename="HIV_Dataset.csv",
    #     disease="HIV AIDS",
    #     col_map=_HIV_COL_MAP,
    # ),
]


# ─────────────────────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────────────────────

def _is_positive(val: str) -> bool:
    """Return True for '1', '1.0', 'yes', 'true', 'positive' etc."""
    v = val.strip().lower()
    return v in {"1", "1.0", "yes", "y", "true", "positive", "present"}


def parse_dataset(cfg: DatasetConfig, csv_path: Path) -> list[dict]:
    """Convert a single-disease CSV file to MediGuard training rows."""
    rows: list[dict] = []
    skipped = 0

    with csv_path.open(encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            print(f"  [WARN] {csv_path.name}: no header row found, skipping.")
            return []

        available_cols = set(reader.fieldnames)
        mapped_cols = {
            src: tgt
            for src, tgt in cfg.col_map.items()
            if src in available_cols and tgt in SYMPTOM_SET
        }
        missing = [src for src in cfg.col_map if src not in available_cols]
        if missing:
            print(f"  [WARN] {csv_path.name}: columns not found (will skip): {missing}")

        for raw in reader:
            # Determine disease label
            if cfg.label_col:
                raw_label = raw.get(cfg.label_col, "").strip()
                disease = cfg.label_map.get(raw_label)
                if not disease:
                    skipped += 1
                    continue
            else:
                disease = cfg.disease

            # Build MediGuard symptom row
            row: dict[str, str] = {s: "0" for s in ALL_SYMPTOMS}
            row["disease"] = disease
            for src_col, tgt_sym in mapped_cols.items():
                if _is_positive(raw.get(src_col, "0")):
                    row[tgt_sym] = "1"

            rows.append(row)

    if skipped:
        print(f"  [INFO] {csv_path.name}: {skipped} rows skipped (unrecognised label).")
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# ML helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_existing_rows(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with csv_path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ALL_SYMPTOMS + ["disease"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved {len(rows):,} rows → {path}")


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
    log_likelihoods = {
        d: {s: (symptom_counts[d][s] + 1) / (class_counts[d] + 2) for s in ALL_SYMPTOMS}
        for d in classes
    }
    return SimpleSymptomModel(ALL_SYMPTOMS, classes, log_priors, log_likelihoods, variant)


def evaluate(model: SimpleSymptomModel, rows: list[dict]) -> float:
    if not rows:
        return 0.0
    correct = sum(
        model.predict_ranked(
            [s for s in ALL_SYMPTOMS if str(row.get(s, "0")).strip() in ("1", "1.0")],
            top_k=1,
        )[0]["disease"] == row["disease"]
        for row in rows
    )
    return correct / len(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Import custom disease datasets")
    parser.add_argument("--no-synthetic", action="store_true",
                        help="Skip existing synthetic baseline; use real data only")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and print stats without writing any files")
    parser.add_argument("--list", action="store_true",
                        help="List registered dataset configs and exit")
    args = parser.parse_args()

    if args.list:
        print(f"{'File':<40} {'Disease':<35} {'Columns mapped'}")
        print("-" * 90)
        for cfg in DATASET_CONFIGS:
            print(f"{cfg.filename:<40} {cfg.disease:<35} {len(cfg.col_map)}")
        return

    custom_dir = BASE / "data/custom"
    custom_dir.mkdir(parents=True, exist_ok=True)

    # ── 1. Collect new real rows ───────────────────────────────────────────────
    new_rows: list[dict] = []
    for cfg in DATASET_CONFIGS:
        csv_path = custom_dir / cfg.filename
        if not csv_path.exists():
            print(f"[SKIP] {cfg.filename} not found in data/custom/ — place it there to import.")
            continue

        print(f"\nParsing {cfg.filename}  →  disease: '{cfg.disease}'")
        parsed = parse_dataset(cfg, csv_path)
        counts = Counter(r["disease"] for r in parsed)
        for disease, n in sorted(counts.items()):
            # Count symptom coverage (at least 1 symptom present)
            covered = sum(
                1 for r in parsed
                if r["disease"] == disease
                and any(r.get(s, "0") == "1" for s in ALL_SYMPTOMS)
            )
            print(f"  {disease}: {n:,} rows  ({covered:,} with ≥1 symptom mapped)")
        new_rows.extend(parsed)

    if not new_rows:
        print("\nNo new data imported. Nothing to do.")
        return

    if args.dry_run:
        print(f"\n[DRY RUN] Would add {len(new_rows):,} real rows to training data.")
        print("Re-run without --dry-run to apply.")
        return

    # ── 2. Merge with existing data ────────────────────────────────────────────
    all_rows: list[dict] = []
    if not args.no_synthetic:
        synth = load_existing_rows(BASE / "data/raw/mediguard_dataset_full.csv")
        if synth:
            print(f"\nLoaded {len(synth):,} existing rows (synthetic baseline).")
            all_rows.extend(synth)
        else:
            print("\nNo existing data found — run build_real_dataset.py first.")

    all_rows.extend(new_rows)
    random.shuffle(all_rows)

    print(f"\nTotal rows after merge: {len(all_rows):,}")
    disease_counts = Counter(r["disease"] for r in all_rows)
    print(f"Diseases: {len(disease_counts)}")
    for d, n in sorted(disease_counts.items()):
        print(f"  {d}: {n:,}")

    # ── 3. Save datasets ───────────────────────────────────────────────────────
    print()
    write_csv(BASE / "data/raw/mediguard_dataset_full.csv", all_rows)
    train_rows, test_rows = stratified_split(all_rows, test_ratio=0.2)
    print(f"  Train: {len(train_rows):,}  Test: {len(test_rows):,}")
    write_csv(BASE / "data/processed/mediguard_train.csv", train_rows)
    write_csv(BASE / "data/processed/mediguard_test.csv", test_rows)

    # ── 4. Update symptom list ─────────────────────────────────────────────────
    for sp in [BASE / "data_pipeline/symptoms_list.json", BASE / "models/symptoms_list.json"]:
        sp.parent.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps(ALL_SYMPTOMS, indent=2), encoding="utf-8")

    # ── 5. Retrain models ─────────────────────────────────────────────────────
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
        pkl = models_dir / f"{name}.pkl"
        with pkl.open("wb") as f:
            pickle.dump(model, f)
        print(f"  {name}: accuracy = {acc:.4f}  ({acc * 100:.1f}%)")

    classes = sorted(disease_counts)
    with (models_dir / "label_encoder.pkl").open("wb") as f:
        pickle.dump(SimpleLabelEncoder(classes), f)

    print(f"\nDone. {len(classes)} diseases, {len(ALL_SYMPTOMS)} symptoms.")
    print("Real patient data has been merged into training data. Models updated.")


if __name__ == "__main__":
    main()
