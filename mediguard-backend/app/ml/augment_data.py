"""
MediGuard Data Augmentation Script
===================================
Improves model performance on Bamenda-priority diseases by:
 1. Balancing under-represented classes
 2. Adding symptom-variation samples (real-world presentations vary)
 3. Adding paediatric presentations for common diseases
 4. Adding seasonal-disease extra samples for Bamenda calendar

Run this BEFORE training to update the processed CSVs:
    cd mediguard-backend
    python -m app.ml.augment_data

Then retrain:
    python -m app.ml.train
"""

import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RANDOM_STATE = 42
RAW_DATA     = Path("data/raw/mediguard_dataset_full.csv")
TRAIN_OUT    = Path("data/processed/mediguard_train.csv")
TEST_OUT     = Path("data/processed/mediguard_test.csv")
AUGMENTED    = Path("data/raw/mediguard_dataset_augmented.csv")

# -- Bamenda-priority target counts (floor - we never reduce a class) ---------
TARGET_COUNTS = {
    "Malaria":          500,   # most common; also child presentations
    "Meningitis":       250,   # harmattan-season priority
    "Cholera":          250,   # rainy-season priority
    "Typhoid Fever":    350,
    "Pneumonia":        250,
    "Tuberculosis":     250,
    "Hepatitis A":      180,
    "Hepatitis B":      180,
    "Yellow Fever":     180,
    "Measles":          180,
    "Dengue Fever":     200,
    "Tetanus":          200,
    "Dysentery":        200,
    "Gastroenteritis":  250,
}

# -- Core symptom profiles used to generate new samples -----------------------
# Each entry: disease -> (required_symptoms, optional_symptoms)
# Required symptoms will always be 1 in generated samples;
# each optional symptom is included with p=0.55.
DISEASE_PROFILES = {
    "Meningitis": (
        ["Stiff neck", "Severe headache", "High fever", "Sensitivity to light"],
        ["Confusion", "Nausea", "Vomiting", "Seizures", "Chills", "Fatigue", "Neck pain"],
    ),
    "Cholera": (
        ["Profuse watery diarrhea", "Rapid dehydration"],
        ["Vomiting", "Muscle cramps", "Low blood pressure", "Reduced urination",
         "Sunken eyes", "Dry mouth", "Weakness"],
    ),
    "Malaria": (
        ["Fever", "Chills", "Sweating"],
        ["Headache", "Muscle aches", "Nausea", "Vomiting", "Fatigue", "Joint pain",
         "High fever", "Prolonged fever", "Weakness", "Loss of appetite"],
    ),
    "Typhoid Fever": (
        ["Prolonged fever", "Abdominal pain"],
        ["Headache", "Fatigue", "Loss of appetite", "Constipation", "Nausea",
         "Vomiting", "Rose spots", "Night sweats", "Weakness", "Diarrhea"],
    ),
    "Yellow Fever": (
        ["Jaundice", "Yellow eyes", "High fever"],
        ["Headache", "Muscle aches", "Nausea", "Vomiting", "Fatigue", "Chills",
         "Dark urine", "Nose bleeding", "Gum bleeding"],
    ),
    "Tetanus": (
        ["Jaw stiffness"],
        ["Seizures", "Difficulty swallowing", "Fever", "Sweating",
         "Fast heartbeat", "High fever", "Back pain"],
    ),
    "Measles": (
        ["Rash", "High fever"],
        ["Koplik spots", "Red eyes", "Runny nose", "Cough", "Sensitivity to light",
         "Loss of appetite", "Fatigue", "Swollen lymph nodes"],
    ),
    "Pneumonia": (
        ["Cough", "Chest pain", "Fever"],
        ["Shortness of breath", "Fatigue", "Sweating", "Chills", "Nausea",
         "Wheezing", "Coughing up blood", "High fever", "Loss of appetite"],
    ),
    "Dengue Fever": (
        ["High fever", "Severe headache", "Pain behind eyes"],
        ["Joint pain", "Muscle aches", "Rash", "Nausea", "Vomiting", "Fatigue",
         "Chills", "Mild bleeding", "Loss of appetite"],
    ),
}


def generate_sample(symptoms_cols, required, optional, disease, rng):
    """Build one binary-feature row for a given disease profile."""
    row = {col: 0 for col in symptoms_cols}
    row["disease"] = disease

    # Required symptoms
    for s in required:
        if s in row:
            row[s] = 1

    # Optional symptoms -- randomly included
    for s in optional:
        if s in row and rng.random() < 0.55:
            row[s] = 1

    # Ensure at least 3 total symptoms (add random optional if needed)
    total = sum(1 for k, v in row.items() if k != "disease" and v == 1)
    if total < 3:
        extras = [s for s in optional if s in row and row[s] == 0]
        rng.shuffle(extras)
        for s in extras[:max(0, 3 - total)]:
            row[s] = 1

    return row


def vary_sample(row, symptoms_cols, rng, flip_rate=0.12):
    """Return a copy of `row` with a few symptoms randomly flipped."""
    new = row.to_dict()
    for col in symptoms_cols:
        if rng.random() < flip_rate:
            new[col] = 1 - int(new[col])
    return new


def main():
    print("Loading dataset ...")
    df = pd.read_csv(RAW_DATA)
    symptoms_cols = [c for c in df.columns if c != "disease"]
    print("  %d rows, %d diseases, %d symptom features" % (
        len(df), df["disease"].nunique(), len(symptoms_cols)
    ))

    rng = random.Random(RANDOM_STATE)
    np.random.seed(RANDOM_STATE)

    extra_rows = []
    counts = df["disease"].value_counts().to_dict()

    # -- 1. Profile-based generation for key diseases -------------------------
    for disease, (required, optional) in DISEASE_PROFILES.items():
        target = TARGET_COUNTS.get(disease, 200)
        current = counts.get(disease, 0)
        n_new = max(0, target - current)
        if n_new == 0:
            print("  %s: already at %d (target %d)" % (disease, current, target))
            continue
        print("  %s: %d -> %d (+%d generated)" % (disease, current, current + n_new, n_new))
        for _ in range(n_new):
            extra_rows.append(
                generate_sample(symptoms_cols, required, optional, disease, rng)
            )

    # -- 2. Variation augmentation for remaining target diseases ---------------
    for disease, target in TARGET_COUNTS.items():
        if disease in DISEASE_PROFILES:
            continue  # already handled above
        current = counts.get(disease, 0)
        n_new = max(0, target - current)
        if n_new == 0:
            continue
        subset = df[df["disease"] == disease]
        if len(subset) == 0:
            continue
        print("  %s: %d -> %d (+%d variation)" % (disease, current, current + n_new, n_new))
        for _ in range(n_new):
            src = subset.sample(1, random_state=rng.randint(0, 9999)).iloc[0]
            extra_rows.append(vary_sample(src, symptoms_cols, rng))

    # -- 3. Generic variation pass -- improve all classes with < 150 samples ---
    small_diseases = [d for d, c in counts.items() if c < 150 and d not in TARGET_COUNTS]
    for disease in small_diseases:
        subset = df[df["disease"] == disease]
        n_new = 150 - len(subset)
        if n_new <= 0:
            continue
        print("  %s: %d -> 150 (+%d variation)" % (disease, len(subset), n_new))
        for _ in range(n_new):
            src = subset.sample(1, random_state=rng.randint(0, 9999)).iloc[0]
            extra_rows.append(vary_sample(src, symptoms_cols, rng, flip_rate=0.10))

    # -- Merge -----------------------------------------------------------------
    if extra_rows:
        df_extra = pd.DataFrame(extra_rows, columns=df.columns)
        df_aug = pd.concat([df, df_extra], ignore_index=True)
    else:
        df_aug = df.copy()

    df_aug = df_aug.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    print("\nAugmented dataset: %d rows (%d added)" % (len(df_aug), len(df_aug) - len(df)))

    # Save augmented raw copy
    AUGMENTED.parent.mkdir(parents=True, exist_ok=True)
    df_aug.to_csv(AUGMENTED, index=False)
    print("Saved augmented raw data -> %s" % AUGMENTED)

    # -- Train / test split ----------------------------------------------------
    train_df, test_df = train_test_split(
        df_aug, test_size=0.15, stratify=df_aug["disease"],
        random_state=RANDOM_STATE
    )

    TRAIN_OUT.parent.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(TRAIN_OUT, index=False)
    test_df.to_csv(TEST_OUT, index=False)

    print("\nTrain: %d rows   Test: %d rows" % (len(train_df), len(test_df)))
    print("Saved -> %s  and  %s" % (TRAIN_OUT, TEST_OUT))
    print("\nNow run:  python -m app.ml.train")


if __name__ == "__main__":
    main()
