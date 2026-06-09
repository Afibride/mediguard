#!/usr/bin/env python3
"""
import_weak_disease_data.py
============================
Mines the large dhivyeshrk/diseases-and-symptoms-dataset (246k rows, 377 symptoms)
for diseases that have < 50 real samples in our current training data, maps them
to MediGuard's symptom schema, and merges them into mediguard_dataset_full.csv.

After running this script, run:
    python scripts/rebalance_and_retrain.py
    python scripts/upload_to_hf.py

Disease coverage from dhivyeshrk (rows found):
    conjunctivitis               909  (+ allergy/virus/bacteria variants)
    sepsis / Septicemia          909
    hemorrhoids                  908
    kidney stone                 904
    appendicitis                 903
    iron deficiency anemia       683
    stroke                       642
    tonsillitis                  446
    shingles (herpes zoster)     379
    meningitis                   297
    gonorrhea                    131
    epilepsy                      75
    mumps                         45
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE       = Path(__file__).parent.parent
SRC_CSV    = BASE / "data/external/dhivyeshrk_diseases-and-symptoms-dataset/Final_Augmented_dataset_Diseases_and_Symptoms.csv"
TARGET_CSV = BASE / "data/raw/mediguard_dataset_full.csv"
SYMS_JSON  = BASE / "models/symptoms_list.json"

# ── Disease name mapping: dhivyeshrk → MediGuard ──────────────────────────────
DISEASE_MAP = {
    "conjunctivitis":                   "Conjunctivitis",
    "conjunctivitis due to allergy":    "Conjunctivitis",
    "conjunctivitis due to virus":      "Conjunctivitis",
    "conjunctivitis due to bacteria":   "Conjunctivitis",
    "sepsis":                           "Septicemia",
    "hemorrhoids":                      "Hemorrhoids (Piles)",
    "kidney stone":                     "Kidney Stones",
    "appendicitis":                     "Appendicitis",
    "iron deficiency anemia":           "Iron Deficiency Anemia",
    "anemia":                           "Iron Deficiency Anemia",
    "stroke":                           "Stroke",
    "tonsillitis":                      "Tonsillitis",
    "shingles (herpes zoster)":         "Herpes Zoster",
    "meningitis":                       "Meningitis",
    "gonorrhea":                        "Gonorrhea",
    "epilepsy":                         "Epilepsy",
    "mumps":                            "Mumps",
    # Additional secondary mapping for completeness
    "rubella":                          "Rubella",
    "measles":                          "Measles",
    "tetanus":                          "Tetanus",
    "rabies":                           "Rabies",
}

# ── Symptom name mapping: dhivyeshrk column → MediGuard symptom ───────────────
# dhivyeshrk uses plain-english lowercase column names; MediGuard uses Title Case.
SYMPTOM_MAP = {
    # Direct / near-direct matches
    "shortness of breath":          "Shortness of breath",
    "dizziness":                    "Dizziness",
    "hoarse voice":                 "Hoarse voice",
    "sore throat":                  "Sore throat",
    "cough":                        "Cough",
    "nasal congestion":             "Nasal congestion",
    "blood in stool":               "Blood in stool",
    "abdominal pain":               "Abdominal pain",
    "nausea":                       "Nausea",
    "vomiting":                     "Vomiting",
    "fever":                        "Fever",
    "headache":                     "Headache",
    "fatigue":                      "Fatigue",
    "weakness":                     "Weakness",
    "back pain":                    "Back pain",
    "chest pain":                   "Chest pain",
    "joint pain":                   "Joint pain",
    "rash":                         "Rash",
    "itching":                      "Itchy skin",
    "weight loss":                  "Weight loss",
    "blurred vision":               "Blurred vision",
    "jaundice":                     "Jaundice",
    "neck pain":                    "Neck pain",
    "muscle pain":                  "Muscle aches",
    "stiff neck":                   "Stiff neck",
    "confusion":                    "Confusion",
    "seizures":                     "Seizures",
    "swollen lymph nodes":          "Swollen lymph nodes",
    "dark urine":                   "Dark urine",
    "loss of appetite":             "Loss of appetite",
    "painful urination":            "Painful urination",
    "frequent urination":           "Frequent urination",
    "blood in urine":               "Blood in urine",
    "eye discharge":                "Eye discharge",
    "red eyes":                     "Red eyes",
    "blisters":                     "Blisters",
    "skin lesions":                 "Skin lesions",
    "night sweats":                 "Night sweats",
    "pale skin":                    "Pale skin",
    "dehydration":                  "Dehydration",
    "diarrhea":                     "Diarrhea",
    "constipation":                 "Constipation",
    "bloating":                     "Bloating",
    "heartburn":                    "Heartburn",
    "ear pain":                     "Ear pain",
    "facial pain":                  "Facial pain",
    "hair loss":                    "Hair loss",
    "genital discharge":            "Genital discharge",
    "genital sores":                "Genital sores",
    "vaginal discharge":            "Vaginal discharge",
    "ankle swelling":               "Ankle swelling",
    "sneezing":                     "Sneezing",
    "sensitivity to light":         "Sensitivity to light",
    "hearing loss":                 "Hearing loss",
    "excessive sweating":           "Sweating",
    "sweating":                     "Sweating",
    "chills":                       "Chills",
    "high fever":                   "High fever",
    "severe headache":              "Severe headache",
    "loss of smell":                "Loss of smell",
    "loss of taste":                "Loss of taste",
    "difficulty swallowing":        "Difficulty swallowing",
    "difficulty in swallowing":     "Difficulty swallowing",
    "jaw stiffness":                "Jaw stiffness",
    "muscle spasms":                "Muscle cramps",
    "muscle cramps":                "Muscle cramps",
    "trembling":                    "Tremor",
    "tremor":                       "Tremor",
    "anxiety":                      "Anxiety",
    "anxiety and nervousness":      "Anxiety",
    "rectal bleeding":              "Rectal bleeding",
    "anal pain":                    "Anal pain",
    "anal itching":                 "Anal itching",
    "itchy anus":                   "Anal itching",
    "swelling near anus":           "Swelling near anus",
    "pain during bowel movements":  "Pain during bowel movement",
    "pain during bowel movement":   "Pain during bowel movement",
    "lower back pain":              "Back pain",
    "flank pain":                   "Back pain",
    "pelvic pain":                  "Pelvic pain",
    "lower abdominal pain":         "Lower abdominal pain",
    "urinary retention":            "Reduced urination",
    "reduced urination":            "Reduced urination",
    "facial drooping":              "Facial drooping",
    "facial weakness":              "Facial drooping",
    "speech difficulty":            "Speech difficulty",
    "slurred speech":               "Speech difficulty",
    "difficulty speaking":          "Speech difficulty",
    "loss of balance":              "Loss of balance",
    "loss of coordination":         "Poor coordination",
    "numbness":                     "Numbness",
    "weakness in limbs":            "Weakness",
    "limb weakness":                "Weakness",
    "arm weakness":                 "Weakness",
    "leg weakness":                 "Weakness",
    "sudden confusion":             "Confusion",
    "altered consciousness":        "Confusion",
    "sudden severe headache":       "Severe headache",
    "vision problems":              "Blurred vision",
    "double vision":                "Blurred vision",
    "eye pain":                     "Eye pain",
    "eye redness":                  "Red eyes",
    "eye itching":                  "Itchy skin",
    "photophobia":                  "Sensitivity to light",
    "light sensitivity":            "Sensitivity to light",
    "sound sensitivity":            "Sensitivity to sound",
    "neck stiffness":               "Stiff neck",
    "nuchal rigidity":              "Stiff neck",
    "kernig sign":                  "Stiff neck",
    "brudzinski sign":              "Stiff neck",
    "petechial rash":               "Rash",
    "skin rash":                    "Rash",
    "maculopapular rash":           "Rash",
    "vesicular rash":               "Blisters",
    "burning rash":                 "Blisters",
    "painful rash":                 "Blisters",
    "unilateral rash":              "Blisters",
    "herpes lesions":               "Blisters",
    "urethral discharge":           "Genital discharge",
    "penile discharge":             "Genital discharge",
    "testicular pain":              "Pelvic pain",
    "scrotal pain":                 "Pelvic pain",
    "dysuria":                      "Painful urination",
    "hematuria":                    "Blood in urine",
    "renal colic":                  "Back pain",
    "flank pain radiating to groin": "Back pain",
    "colicky pain":                 "Abdominal pain",
    "right lower quadrant pain":    "Lower abdominal pain",
    "periumbilical pain":           "Abdominal pain",
    "rebound tenderness":           "Abdominal pain",
    "muscle rigidity":              "Stiffness",
    "stiffness":                    "Stiffness",
    "opisthotonos":                 "Stiffness",
    "risus sardonicus":             "Jaw stiffness",
    "trismus":                      "Jaw stiffness",
    "lockjaw":                      "Jaw stiffness",
    "irritability":                 "Irritability",
    "agitation":                    "Agitation",
    "hydrophobia":                  "Hydrophobia",
    "aerophobia":                   "Hydrophobia",
    "hypersalivation":              "Excessive sweepiness",
    "drooling":                     "Excessive sleepiness",
    "parotid swelling":             "Jaw swelling",
    "jaw swelling":                 "Jaw swelling",
    "parotitis":                    "Jaw swelling",
    "testicular swelling":          "Swollen feet",
    "koplik spots":                 "Koplik spots",
    "coryza":                       "Runny nose",
    "runny nose":                   "Runny nose",
    "conjunctivitis (red eyes)":    "Red eyes",
    "maculopapular rash on face":   "Rash",
    "lymph node swelling":          "Swollen lymph nodes",
    "palpitations":                 "Fast heartbeat",
    "rapid heartbeat":              "Fast heartbeat",
    "fast heart rate":              "Fast heartbeat",
    "tachycardia":                  "Fast heartbeat",
    "brittle nails":                "Hair loss",
    "spoon-shaped nails":           "Hair loss",
    "pallor":                       "Pale skin",
    "shortness of breath on exertion": "Shortness of breath",
    "exertional dyspnea":           "Shortness of breath",
    "dysphagia":                    "Difficulty swallowing",
    "glossitis":                    "White patches in mouth",
    "angular stomatitis":           "White patches in mouth",
    "stomatitis":                   "White patches in mouth",
    "increased sensitivity to cold": "Cold intolerance",
    "cold extremities":             "Cold intolerance",
    "pica":                         "Loss of appetite",
    "low blood pressure":           "Low blood pressure",
    "hypotension":                  "Low blood pressure",
    "altered mental status":        "Confusion",
    "encephalopathy":               "Confusion",
    "high temperature":             "High fever",
    "pyrexia":                      "Fever",
    "malaise":                      "Fatigue",
    "body aches":                   "Body aches",
    "muscle aches":                 "Muscle aches",
    "myalgia":                      "Muscle aches",
    "arthralgia":                   "Joint pain",
    "joint swelling":               "Joint swelling",
    "lymphadenopathy":              "Swollen lymph nodes",
}


def build_mediguard_row(src_row: pd.Series, our_symptoms: list[str], disease: str) -> dict:
    """Map a dhivyeshrk binary row to our symptom schema."""
    row = {s: 0 for s in our_symptoms}
    row["disease"] = disease
    for col, val in src_row.items():
        if col == "diseases":
            continue
        col_lower = col.strip().lower()
        medi_sym = SYMPTOM_MAP.get(col_lower)
        if medi_sym is None:
            # Try direct title-case match
            tc = col.strip().title()
            if tc in row:
                medi_sym = tc
        if medi_sym and medi_sym in row:
            if str(val).strip() in ("1", "1.0", "True"):
                row[medi_sym] = 1
    return row


def main() -> None:
    if not SRC_CSV.exists():
        print(f"ERROR: Source CSV not found: {SRC_CSV}")
        print("Download it from HF with:")
        print("  python scripts/import_weak_disease_data.py --download")
        sys.exit(1)

    if not TARGET_CSV.exists():
        print(f"ERROR: Target CSV not found: {TARGET_CSV}")
        sys.exit(1)

    our_symptoms = json.loads(SYMS_JSON.read_text(encoding="utf-8"))
    print(f"MediGuard symptom list: {len(our_symptoms)} symptoms")

    # ── Load existing data and count current weak-disease samples ──────────────
    print(f"\nLoading existing dataset: {TARGET_CSV}")
    df_existing = pd.read_csv(TARGET_CSV)
    existing_counts = df_existing["disease"].value_counts()

    target_diseases = sorted(set(DISEASE_MAP.values()))
    print("\nCurrent sample counts for target diseases:")
    for d in target_diseases:
        print(f"  {d:<40} {existing_counts.get(d, 0):>5} existing")

    # ── Stream the large CSV and extract matching rows ─────────────────────────
    print(f"\nMining {SRC_CSV.name} ({SRC_CSV.stat().st_size // 1024 // 1024} MB) ...")
    CHUNK = 50_000
    new_rows: list[dict] = []
    found: dict[str, int] = {}

    reader = pd.read_csv(SRC_CSV, low_memory=False, chunksize=CHUNK)
    total_read = 0

    for chunk in reader:
        total_read += len(chunk)
        print(f"  Read {total_read:,} rows, new rows so far: {len(new_rows)}", end="\r", flush=True)

        for _, src_row in chunk.iterrows():
            disease_raw = str(src_row.get("diseases", "")).strip().lower()
            medi_disease = DISEASE_MAP.get(disease_raw)
            if not medi_disease:
                continue

            row = build_mediguard_row(src_row, our_symptoms, medi_disease)
            new_rows.append(row)
            found[medi_disease] = found.get(medi_disease, 0) + 1

    print(f"\n\nExtracted {len(new_rows):,} rows from dhivyeshrk dataset")
    print("\nRows extracted per disease:")
    for d in sorted(found):
        print(f"  {d:<40} {found[d]:>5}")

    if not new_rows:
        print("No rows matched — check DISEASE_MAP names.")
        sys.exit(1)

    # ── Merge ─────────────────────────────────────────────────────────────────
    df_new = pd.DataFrame(new_rows)

    # Ensure columns match (fill any missing symptom columns with 0)
    for col in df_existing.columns:
        if col not in df_new.columns:
            df_new[col] = 0
    df_new = df_new[df_existing.columns]

    print(f"\nExisting dataset: {len(df_existing):,} rows")
    print(f"New rows to add:  {len(df_new):,} rows")

    # Only drop exact duplicates WITHIN the new rows (don't touch existing data).
    # The existing dataset intentionally has repeated rows for SMOTE quality.
    before_dedup = len(df_new)
    df_new_dedup = df_new.drop_duplicates()
    print(f"New rows after internal dedup: {before_dedup:,} → {len(df_new_dedup):,}")

    df_merged = pd.concat([df_existing, df_new_dedup], ignore_index=True)
    print(f"Merged total: {len(df_merged):,} rows")

    # ── Show final counts ──────────────────────────────────────────────────────
    new_counts = df_merged["disease"].value_counts()
    print("\nFinal sample counts (target diseases):")
    for d in target_diseases:
        before = existing_counts.get(d, 0)
        after  = new_counts.get(d, 0)
        delta  = after - before
        flag   = " ✓" if delta > 0 else ""
        print(f"  {d:<40} {before:>5} → {after:>5}  (+{delta}){flag}")

    # ── Save ──────────────────────────────────────────────────────────────────
    df_merged.to_csv(TARGET_CSV, index=False)
    print(f"\nSaved merged dataset to {TARGET_CSV}")
    print(f"Total: {len(df_merged):,} rows, {df_merged['disease'].nunique()} diseases")
    print("\nNext: run   python scripts/rebalance_and_retrain.py")


if __name__ == "__main__":
    main()
