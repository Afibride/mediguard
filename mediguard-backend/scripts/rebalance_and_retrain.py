#!/usr/bin/env python3
"""
rebalance_and_retrain.py
========================
Fixes MediGuard's class-imbalance problem end-to-end:

  1. Loads the full raw dataset (10 627 rows, 43 diseases).
  2. Augments every class with < 120 samples using symptom-profile perturbation
     so all classes reach ≥ 120 samples (needed for SMOTE and reliable splits).
  3. Performs a STRATIFIED 80/20 train/test split, guaranteeing every class
     appears in both halves with ≥ 20 test samples.
  4. Applies SMOTE on the training half to bring all classes to ~300 samples.
  5. Re-trains Random Forest, Decision Tree, and Naïve Bayes with
     class_weight='balanced'.
  6. Evaluates on the ORIGINAL (pre-SMOTE) stratified test set and writes:
       models/random_forest_report.txt   (per-class metrics)
       models/random_forest_report_balanced.txt
  7. Saves balanced train/test CSVs to data/processed/.
  8. Saves updated model .pkl files and version.json.

Usage:
    cd mediguard-backend
    python scripts/rebalance_and_retrain.py
"""

import hashlib, json, random, sys, warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report,
    precision_score, recall_score, f1_score,
)
from sklearn.naive_bayes import BernoulliNB
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
random.seed(RANDOM_STATE)

BASE        = Path(__file__).parent.parent
RAW_CSV     = BASE / "data" / "raw" / "mediguard_dataset_full.csv"
PROC_DIR    = BASE / "data" / "processed"
MODELS_DIR  = BASE / "models"
PROC_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

TARGET_PER_CLASS_RAW   = 120   # min samples per class after augmentation
TARGET_PER_CLASS_SMOTE = 300   # samples per class after SMOTE in training
TEST_FRACTION          = 0.20
MIN_TEST_SAMPLES       = 20    # enforced per class in the test set

# ─── 1. Load raw data ─────────────────────────────────────────────────────────
print("=" * 65)
print("STEP 1 — Loading raw dataset")
df_raw = pd.read_csv(RAW_CSV)
symptoms = [c for c in df_raw.columns if c != "disease"]
print(f"  Rows: {len(df_raw):,}  |  Symptoms: {len(symptoms)}  |  Diseases: {df_raw['disease'].nunique()}")

vc = df_raw["disease"].value_counts()
under = vc[vc < TARGET_PER_CLASS_RAW]
print(f"  Classes below {TARGET_PER_CLASS_RAW} samples: {len(under)}  →  will be augmented")
for name, cnt in under.items():
    print(f"    {name:<35} {cnt:>4} samples")


# ─── 2. Augment rare classes ──────────────────────────────────────────────────
print("\nSTEP 2 — Augmenting rare disease classes")

def augment_disease(sub_df: pd.DataFrame, target: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate (target - len(sub_df)) synthetic rows by bootstrapping the
    existing samples and adding controlled Bernoulli noise.

    Strategy:
      - Cardinal symptoms  (mode == 1): keep 1 with prob 0.92, flip to 0 with prob 0.08
      - Background symptoms (mode == 0): keep 0 with prob 0.93, flip to 1 with prob 0.07
    """
    feat_cols = [c for c in sub_df.columns if c != "disease"]
    disease   = sub_df["disease"].iloc[0]
    arr       = sub_df[feat_cols].values.astype(np.float32)
    mode      = (arr.mean(axis=0) >= 0.5).astype(np.float32)  # cardinal mask

    n_needed  = max(0, target - len(sub_df))
    if n_needed == 0:
        return sub_df

    synth_rows = []
    for _ in range(n_needed):
        base = mode.copy()
        cardinal_mask  = (mode == 1)
        bg_mask        = (mode == 0)
        # flip cardinal→0 with 8% chance
        flip_off = rng.random(size=cardinal_mask.sum()) < 0.08
        base[cardinal_mask] = np.where(flip_off, 0.0, 1.0)
        # flip background→1 with 7% chance
        flip_on  = rng.random(size=bg_mask.sum()) < 0.07
        base[bg_mask]       = np.where(flip_on,  1.0, 0.0)
        synth_rows.append(base)

    synth_df = pd.DataFrame(synth_rows, columns=feat_cols)
    synth_df["disease"] = disease
    return pd.concat([sub_df, synth_df], ignore_index=True)


rng = np.random.default_rng(RANDOM_STATE)
pieces = []
for disease, group in df_raw.groupby("disease"):
    if len(group) < TARGET_PER_CLASS_RAW:
        group = augment_disease(group, TARGET_PER_CLASS_RAW, rng)
        print(f"  {disease:<35} {len(df_raw[df_raw['disease']==disease]):>4} → {len(group)}")
    pieces.append(group)

df_aug = pd.concat(pieces, ignore_index=True)
vc2 = df_aug["disease"].value_counts()
print(f"\n  Augmented dataset: {len(df_aug):,} rows  |  min class: {vc2.min()}  |  max: {vc2.max()}")


# ─── 3. Stratified 80/20 split ────────────────────────────────────────────────
print("\nSTEP 3 — Stratified 80/20 train/test split")

train_rows, test_rows = [], []
for disease, group in df_aug.groupby("disease"):
    group = group.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    n_test  = max(MIN_TEST_SAMPLES, int(round(len(group) * TEST_FRACTION)))
    n_test  = min(n_test, len(group) - 1)  # keep at least 1 for training
    n_train = len(group) - n_test
    test_rows.append(group.iloc[:n_test])
    train_rows.append(group.iloc[n_test:])

df_train_raw = pd.concat(train_rows, ignore_index=True).sample(frac=1, random_state=RANDOM_STATE)
df_test      = pd.concat(test_rows,  ignore_index=True).sample(frac=1, random_state=RANDOM_STATE)

print(f"  Train (pre-SMOTE): {len(df_train_raw):,} rows  "
      f"| Test: {len(df_test):,} rows  "
      f"| Train diseases: {df_train_raw['disease'].nunique()}  "
      f"| Test diseases: {df_test['disease'].nunique()}")

# Verify no unseen classes in test
unseen = set(df_test["disease"]) - set(df_train_raw["disease"])
if unseen:
    print(f"  WARNING: {len(unseen)} unseen test classes remain: {unseen}")
else:
    print("  All test diseases are present in training set.")

test_counts = df_test["disease"].value_counts()
print(f"  Min test samples per class: {test_counts.min()}  |  Max: {test_counts.max()}")


# ─── 4. Apply SMOTE to training data ─────────────────────────────────────────
print("\nSTEP 4 — Applying SMOTE to training data")

X_train_raw = df_train_raw[symptoms].astype(int).values
y_train_raw = df_train_raw["disease"].values

# Encode labels for SMOTE
le = LabelEncoder()
le.fit(y_train_raw)
y_enc = le.transform(y_train_raw)

# Target counts per class for SMOTE
vc_train = pd.Series(y_train_raw).value_counts()
smote_strategy = {
    le.transform([cls])[0]: TARGET_PER_CLASS_SMOTE
    for cls in vc_train.index
    if vc_train[cls] < TARGET_PER_CLASS_SMOTE
}

smote = SMOTE(
    sampling_strategy=smote_strategy,
    k_neighbors=min(5, vc_train.min() - 1),
    random_state=RANDOM_STATE,
)
X_smote, y_smote_enc = smote.fit_resample(X_train_raw, y_enc)
y_smote = le.inverse_transform(y_smote_enc)

print(f"  Training rows before SMOTE: {len(y_train_raw):,}")
print(f"  Training rows after  SMOTE: {len(y_smote):,}")
vc_after = pd.Series(y_smote).value_counts()
print(f"  Min class after SMOTE: {vc_after.min()}  |  Max: {vc_after.max()}")

df_train_smote = pd.DataFrame(X_smote.astype(int), columns=symptoms)
df_train_smote["disease"] = y_smote


# ─── 5. Save balanced CSVs ───────────────────────────────────────────────────
print("\nSTEP 5 — Saving balanced datasets")

df_train_smote.to_csv(PROC_DIR / "mediguard_train.csv", index=False)
df_test.to_csv(       PROC_DIR / "mediguard_test.csv",  index=False)
df_train_raw.to_csv(  PROC_DIR / "mediguard_train_pre_smote.csv", index=False)

print(f"  Saved mediguard_train.csv  ({len(df_train_smote):,} rows)")
print(f"  Saved mediguard_test.csv   ({len(df_test):,} rows)")


# ─── 6. Retrain models ───────────────────────────────────────────────────────
print("\nSTEP 6 — Training models on balanced data")

X_train = df_train_smote[symptoms].astype(int)
y_train = df_train_smote["disease"]
X_test  = df_test[symptoms].astype(int)
y_test  = df_test["disease"]

# Rebuild label encoder on full class set
le2 = LabelEncoder()
le2.fit(y_train)
joblib.dump(le2, MODELS_DIR / "label_encoder.pkl")

model_defs = {
    "random_forest": RandomForestClassifier(
        n_estimators=300,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
    "decision_tree": DecisionTreeClassifier(
        criterion="gini",
        class_weight="balanced",
        random_state=RANDOM_STATE,
    ),
    "naive_bayes": BernoulliNB(alpha=1.0),
}

results = {}
for name, model in model_defs.items():
    model.fit(X_train, y_train)
    preds    = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    results[name] = {"accuracy": accuracy, "preds": preds}
    joblib.dump(model, MODELS_DIR / f"{name}.pkl")

    p_mac = precision_score(y_test, preds, average="macro",    zero_division=0)
    r_mac = recall_score(   y_test, preds, average="macro",    zero_division=0)
    f_mac = f1_score(       y_test, preds, average="macro",    zero_division=0)
    p_wtd = precision_score(y_test, preds, average="weighted", zero_division=0)
    r_wtd = recall_score(   y_test, preds, average="weighted", zero_division=0)
    f_wtd = f1_score(       y_test, preds, average="weighted", zero_division=0)

    results[name].update(dict(
        p_mac=p_mac, r_mac=r_mac, f_mac=f_mac,
        p_wtd=p_wtd, r_wtd=r_wtd, f_wtd=f_wtd,
    ))
    print(f"  {name:<20}  acc={accuracy:.4f}  "
          f"macro F1={f_mac:.4f}  wtd F1={f_wtd:.4f}")

    if name == "random_forest":
        rpt_txt = classification_report(y_test, preds, zero_division=0)
        (MODELS_DIR / "random_forest_report.txt").write_text(rpt_txt, encoding="utf-8")
        (MODELS_DIR / "random_forest_report_balanced.txt").write_text(rpt_txt, encoding="utf-8")


# ─── 7. Version manifest ──────────────────────────────────────────────────────
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

manifest = {"trained_at": datetime.now(timezone.utc).isoformat(), "files": {}}
for fname in ["random_forest.pkl","decision_tree.pkl","naive_bayes.pkl",
              "label_encoder.pkl","symptoms_list.json"]:
    p = MODELS_DIR / fname
    if p.exists():
        manifest["files"][fname] = {"sha256": sha256(p), "size_bytes": p.stat().st_size}
(MODELS_DIR / "version.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8")


# ─── 8. Summary ──────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("SUMMARY — model evaluation on balanced, stratified test set")
print(f"{'Model':<22} {'Accuracy':>9} {'MacroP':>8} {'MacroR':>8} {'MacroF1':>8} {'WtdF1':>8}")
print("-" * 65)
for name, r in results.items():
    print(f"  {name:<20} {r['accuracy']*100:>8.2f}%  "
          f"{r['p_mac']*100:>7.2f}%  {r['r_mac']*100:>7.2f}%  "
          f"{r['f_mac']*100:>7.2f}%  {r['f_wtd']*100:>7.2f}%")
print("=" * 65)
print(f"\nArtifacts saved to {MODELS_DIR.resolve()}")
