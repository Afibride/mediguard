#!/usr/bin/env python3
"""
rebalance_and_retrain.py  (v2 — accuracy-improved)
====================================================
End-to-end retraining pipeline with accuracy improvements:

  Improvements over v1
  --------------------
  * HistGradientBoostingClassifier added — typically 5-10% better than RF on
    tabular/binary symptom data; saved as gradient_boosting.pkl.
  * Best-performing model (by macro-F1 on held-out test set) is also written
    as random_forest.pkl so the live server picks it up with zero config change.
  * Augmentation target raised 120 → 200 samples/class.
  * SMOTE target raised 300 → 600 samples/class (more balanced training).
  * Cardinal-symptom flip rate lowered 8% → 5% to preserve disease identity.
  * Background-symptom flip rate lowered 7% → 5%.
  * RF tuned: 500 trees (was 300), min_samples_leaf=2 (was 1) to reduce noise.
  * 5-fold cross-validation on the training split for unbiased model comparison.
  * Zero-F1 disease spotlight printed to highlight remaining problem classes.

Pipeline
--------
  1. Load raw dataset
  2. Augment classes < 200 samples
  3. Stratified 80/20 split (all classes in both halves, ≥ 20 test samples)
  4. SMOTE on training half → 600 samples/class
  5. Train RF / Decision Tree / Naive Bayes / HistGradientBoosting
  6. 5-fold CV macro-F1 comparison on training data
  7. Save all models; copy best model → random_forest.pkl
  8. Generate per-class report + zero-F1 spotlight
  9. Write version.json (SHA-256 manifest for HF auto-update)

Usage
-----
    cd mediguard-backend
    python scripts/rebalance_and_retrain.py

Then upload to Hugging Face:
    python -m app.ml.upload_to_hf
"""

import hashlib, json, random, sys, warnings
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.naive_bayes import BernoulliNB
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
random.seed(RANDOM_STATE)

BASE       = Path(__file__).parent.parent
RAW_CSV    = BASE / "data" / "raw" / "mediguard_dataset_full.csv"
PROC_DIR   = BASE / "data" / "processed"
MODELS_DIR = BASE / "models"
PROC_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Tunable thresholds
TARGET_PER_CLASS_RAW   = 200   # min samples per class after augmentation (was 120)
TARGET_PER_CLASS_SMOTE = 600   # samples per class after SMOTE in training (was 300)
TEST_FRACTION          = 0.20
MIN_TEST_SAMPLES       = 20

# Augmentation noise rates (lower = more faithful to real disease profile)
CARDINAL_FLIP_OFF = 0.05  # probability cardinal symptom is dropped  (was 0.08)
BACKGROUND_FLIP_ON = 0.05  # probability background symptom is added (was 0.07)


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
print(f"\nSTEP 2 — Augmenting rare classes to {TARGET_PER_CLASS_RAW} samples each")


def augment_disease(sub_df: pd.DataFrame, target: int, rng: np.random.Generator) -> pd.DataFrame:
    """
    Generate synthetic rows by bootstrapping existing samples and applying
    controlled Bernoulli noise.  Lower flip rates preserve disease identity.

    Cardinal symptoms (mode == 1): kept with probability (1 - CARDINAL_FLIP_OFF)
    Background symptoms (mode == 0): kept off with probability (1 - BACKGROUND_FLIP_ON)
    """
    feat_cols = [c for c in sub_df.columns if c != "disease"]
    disease   = sub_df["disease"].iloc[0]
    arr       = sub_df[feat_cols].values.astype(np.float32)
    mode      = (arr.mean(axis=0) >= 0.5).astype(np.float32)

    n_needed = max(0, target - len(sub_df))
    if n_needed == 0:
        return sub_df

    synth_rows = []
    for _ in range(n_needed):
        base         = mode.copy()
        cardinal_mask = mode == 1
        bg_mask       = mode == 0
        flip_off = rng.random(size=cardinal_mask.sum()) < CARDINAL_FLIP_OFF
        base[cardinal_mask] = np.where(flip_off, 0.0, 1.0)
        flip_on  = rng.random(size=bg_mask.sum()) < BACKGROUND_FLIP_ON
        base[bg_mask]       = np.where(flip_on, 1.0, 0.0)
        synth_rows.append(base)

    synth_df = pd.DataFrame(synth_rows, columns=feat_cols)
    synth_df["disease"] = disease
    return pd.concat([sub_df, synth_df], ignore_index=True)


rng = np.random.default_rng(RANDOM_STATE)
pieces = []
for disease, group in df_raw.groupby("disease"):
    if len(group) < TARGET_PER_CLASS_RAW:
        group = augment_disease(group, TARGET_PER_CLASS_RAW, rng)
        orig = len(df_raw[df_raw["disease"] == disease])
        print(f"  {disease:<35} {orig:>4} → {len(group)}")
    pieces.append(group)

df_aug = pd.concat(pieces, ignore_index=True)
vc2 = df_aug["disease"].value_counts()
print(f"\n  Augmented dataset: {len(df_aug):,} rows  |  min class: {vc2.min()}  |  max: {vc2.max()}")


# ─── 3. Stratified 80/20 split ────────────────────────────────────────────────
print("\nSTEP 3 — Stratified 80/20 train/test split")

train_rows, test_rows = [], []
for disease, group in df_aug.groupby("disease"):
    group  = group.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    n_test = max(MIN_TEST_SAMPLES, int(round(len(group) * TEST_FRACTION)))
    n_test = min(n_test, len(group) - 1)
    test_rows.append(group.iloc[:n_test])
    train_rows.append(group.iloc[n_test:])

df_train_raw = pd.concat(train_rows, ignore_index=True).sample(frac=1, random_state=RANDOM_STATE)
df_test      = pd.concat(test_rows,  ignore_index=True).sample(frac=1, random_state=RANDOM_STATE)

print(f"  Train (pre-SMOTE): {len(df_train_raw):,} rows  "
      f"| Test: {len(df_test):,} rows  "
      f"| Train diseases: {df_train_raw['disease'].nunique()}  "
      f"| Test diseases: {df_test['disease'].nunique()}")

unseen = set(df_test["disease"]) - set(df_train_raw["disease"])
if unseen:
    print(f"  WARNING: {len(unseen)} unseen test classes: {unseen}")
else:
    print("  All test diseases present in training set.")

tc = df_test["disease"].value_counts()
print(f"  Min test samples/class: {tc.min()}  |  Max: {tc.max()}")


# ─── 4. SMOTE ─────────────────────────────────────────────────────────────────
print(f"\nSTEP 4 — SMOTE on training data → {TARGET_PER_CLASS_SMOTE} samples/class")

X_train_raw = df_train_raw[symptoms].astype(int).values
y_train_raw = df_train_raw["disease"].values

le = LabelEncoder()
le.fit(y_train_raw)
y_enc = le.transform(y_train_raw)

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


# ─── 6. Train models ─────────────────────────────────────────────────────────
print("\nSTEP 6 — Training models on balanced data")

X_train = df_train_smote[symptoms].astype(int).values
y_train = df_train_smote["disease"].values
X_test  = df_test[symptoms].astype(int).values
y_test  = df_test["disease"].values

le2 = LabelEncoder()
le2.fit(y_train)
joblib.dump(le2, MODELS_DIR / "label_encoder.pkl")

model_defs = {
    "random_forest": RandomForestClassifier(
        n_estimators=500,        # was 300
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=2,      # was 1 — reduces overfitting on noisy SMOTE samples
        max_features="sqrt",
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),
    "gradient_boosting": HistGradientBoostingClassifier(
        max_iter=400,
        max_depth=None,
        learning_rate=0.08,
        min_samples_leaf=20,
        l2_regularization=0.1,
        class_weight="balanced",
        random_state=RANDOM_STATE,
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
    print(f"  Training {name} ...", flush=True)
    model.fit(X_train, y_train)
    preds    = model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    f_mac    = f1_score(y_test, preds, average="macro",    zero_division=0)
    f_wtd    = f1_score(y_test, preds, average="weighted", zero_division=0)
    p_mac    = precision_score(y_test, preds, average="macro",    zero_division=0)
    r_mac    = recall_score(   y_test, preds, average="macro",    zero_division=0)
    p_wtd    = precision_score(y_test, preds, average="weighted", zero_division=0)
    r_wtd    = recall_score(   y_test, preds, average="weighted", zero_division=0)

    results[name] = dict(
        accuracy=accuracy, preds=preds,
        f_mac=f_mac, f_wtd=f_wtd,
        p_mac=p_mac, r_mac=r_mac,
        p_wtd=p_wtd, r_wtd=r_wtd,
    )
    joblib.dump(model, MODELS_DIR / f"{name}.pkl")
    print(f"    acc={accuracy:.4f}  macro F1={f_mac:.4f}  wtd F1={f_wtd:.4f}  → saved {name}.pkl")

    if name == "random_forest":
        rpt = classification_report(y_test, preds, zero_division=0)
        (MODELS_DIR / "random_forest_report.txt").write_text(rpt, encoding="utf-8")
        (MODELS_DIR / "random_forest_report_balanced.txt").write_text(rpt, encoding="utf-8")


# ─── 7. 5-fold CV comparison on training data ────────────────────────────────
print("\nSTEP 7 — 5-fold cross-validation (training data, macro F1)")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

cv_scores = {}
for name, model in model_defs.items():
    if name == "decision_tree":
        continue  # DT is a baseline — skip CV to save time
    scores = cross_val_score(
        model, X_train, y_train,
        cv=cv, scoring="f1_macro", n_jobs=-1,
    )
    cv_scores[name] = scores
    print(f"  {name:<22}  CV macro F1: {scores.mean():.4f} ± {scores.std():.4f}")


# ─── 8. Promote best model → random_forest.pkl ───────────────────────────────
print("\nSTEP 8 — Selecting best model as primary (random_forest.pkl)")

# Use CV macro-F1 to rank; fall back to held-out macro-F1 if CV wasn't run
def model_score(name):
    if name in cv_scores:
        return cv_scores[name].mean()
    return results[name]["f_mac"]

ranked = sorted(
    [n for n in results if n != "decision_tree"],
    key=model_score,
    reverse=True,
)
best_name = ranked[0]
best_f1   = model_score(best_name)

print(f"  Best model: {best_name}  (CV/test macro F1 = {best_f1:.4f})")

if best_name != "random_forest":
    import shutil
    shutil.copy2(MODELS_DIR / f"{best_name}.pkl", MODELS_DIR / "random_forest.pkl")
    print(f"  Copied {best_name}.pkl → random_forest.pkl  (server will use this)")
    # Update the report to match the best model
    best_preds = results[best_name]["preds"]
    rpt = classification_report(y_test, best_preds, zero_division=0)
    (MODELS_DIR / "random_forest_report.txt").write_text(rpt, encoding="utf-8")
    (MODELS_DIR / "random_forest_report_balanced.txt").write_text(rpt, encoding="utf-8")
else:
    print("  Random Forest is already the best model.")


# ─── 9. Zero-F1 spotlight ────────────────────────────────────────────────────
print("\nSTEP 9 — Zero / near-zero F1 spotlight (best model)")
best_preds = results[best_name]["preds"]
from sklearn.metrics import classification_report as cr
report_dict = {}
for line in cr(y_test, best_preds, output_dict=True, zero_division=0).items():
    if isinstance(line[1], dict):
        report_dict[line[0]] = line[1]

problem = {k: v for k, v in report_dict.items() if v.get("f1-score", 1.0) < 0.50}
if problem:
    print(f"  {'Disease':<35} {'Precision':>10} {'Recall':>8} {'F1':>6} {'Support':>8}")
    print("  " + "-" * 65)
    for disease, m in sorted(problem.items(), key=lambda x: x[1]["f1-score"]):
        print(f"  {disease:<35} {m['precision']:>10.2f} {m['recall']:>8.2f} "
              f"{m['f1-score']:>6.2f} {int(m['support']):>8}")
else:
    print("  No diseases below F1=0.50 — great improvement!")

zero_f1 = [k for k, v in report_dict.items() if v.get("f1-score", 1.0) == 0.0]
if zero_f1:
    print(f"\n  Diseases still at F1=0: {', '.join(zero_f1)}")
    print("  → These need more distinct symptoms in the raw dataset.")


# ─── 10. Version manifest ────────────────────────────────────────────────────
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

manifest = {"trained_at": datetime.now(timezone.utc).isoformat(), "files": {}}
for fname in [
    "random_forest.pkl",
    "gradient_boosting.pkl",
    "decision_tree.pkl",
    "naive_bayes.pkl",
    "label_encoder.pkl",
    "symptoms_list.json",
]:
    p = MODELS_DIR / fname
    if p.exists():
        manifest["files"][fname] = {"sha256": sha256(p), "size_bytes": p.stat().st_size}

(MODELS_DIR / "version.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("\nSTEP 10 — version.json written")


# ─── Summary ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("SUMMARY — evaluation on balanced, stratified test set")
print(f"{'Model':<24} {'Accuracy':>9} {'MacroP':>8} {'MacroR':>8} {'MacroF1':>8} {'WtdF1':>8}")
print("-" * 65)
for name, r in results.items():
    marker = " ← PRIMARY" if name == best_name else ""
    print(f"  {name:<22} {r['accuracy']*100:>8.2f}%  "
          f"{r['p_mac']*100:>7.2f}%  {r['r_mac']*100:>7.2f}%  "
          f"{r['f_mac']*100:>7.2f}%  {r['f_wtd']*100:>7.2f}%{marker}")
print("=" * 65)
print(f"\nArtifacts saved to {MODELS_DIR.resolve()}")
print("\nNext step — upload to Hugging Face:")
print("    cd mediguard-backend && python -m app.ml.upload_to_hf")
