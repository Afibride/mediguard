"""
MediGuard model training script.

Trains three scikit-learn classifiers on the processed symptom dataset,
evaluates them on the held-out test set, and saves them to models/.
Also writes models/version.json so the server can detect when newer
models are available on Hugging Face.

Usage:
    cd mediguard-backend
    python -m app.ml.train

Outputs:
    models/random_forest.pkl
    models/decision_tree.pkl
    models/naive_bayes.pkl
    models/label_encoder.pkl
    models/symptoms_list.json
    models/random_forest_report.txt
    models/version.json          <- SHA-256 + timestamp manifest
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.naive_bayes import BernoulliNB          # BernoulliNB for binary features
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier


TRAIN_PATH = Path("data/processed/mediguard_train.csv")
TEST_PATH  = Path("data/processed/mediguard_test.csv")
MODELS_DIR = Path("models")
SYMPTOMS_PATH = Path("data_pipeline/symptoms_list.json")
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_dataset(path: Path) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    df = pd.read_csv(path)
    symptoms = [col for col in df.columns if col != "disease"]
    x = df[symptoms].astype(int)
    y = df["disease"].astype(str)
    return x, y, symptoms


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_version_manifest(model_files: list[Path]) -> None:
    """Write models/version.json with SHA-256 hashes and a timestamp.

    The live server compares this manifest against the remote copy on Hugging Face
    to decide whether to pull updated models.
    """
    manifest = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "files": {},
    }
    for p in model_files:
        if p.exists():
            manifest["files"][p.name] = {
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            }
    save_json(MODELS_DIR / "version.json", manifest)
    print("  version.json written (%d files)" % len(manifest["files"]))


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def build_models() -> dict[str, object]:
    return {
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
        # BernoulliNB is designed for binary (0/1) feature vectors.
        # It greatly outperforms GaussianNB on symptom-presence data.
        "naive_bayes": BernoulliNB(alpha=1.0),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Force UTF-8 output on Windows so print() doesn't fail on non-ASCII
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Loading dataset ...")
    x_train, y_train, symptoms = load_dataset(TRAIN_PATH)
    x_test,  y_test,  test_symptoms = load_dataset(TEST_PATH)

    if symptoms != test_symptoms:
        raise ValueError("Train and test symptom columns do not match.")

    print("  Train: %d rows x %d symptoms" % (x_train.shape[0], len(symptoms)))
    print("  Test:  %d rows x %d symptoms" % (x_test.shape[0], len(symptoms)))
    print("  Diseases: %d\n" % y_train.nunique())

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Label encoder
    label_encoder = LabelEncoder()
    label_encoder.fit(y_train)
    joblib.dump(label_encoder, MODELS_DIR / "label_encoder.pkl")
    print("  label_encoder         saved")

    # Train & evaluate each model
    trained_files: list[Path] = [MODELS_DIR / "label_encoder.pkl"]
    models = build_models()
    results: dict[str, float] = {}

    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        accuracy = accuracy_score(y_test, predictions)
        results[name] = accuracy
        out_path = MODELS_DIR / f"{name}.pkl"
        joblib.dump(model, out_path)
        trained_files.append(out_path)
        print("  %-20s accuracy=%.4f  saved" % (name, accuracy))

        if name == "random_forest":
            report = classification_report(y_test, predictions, zero_division=0)
            report_path = MODELS_DIR / "random_forest_report.txt"
            report_path.write_text(report, encoding="utf-8")
            print("  classification report saved")

    # Symptoms list
    symptoms_out = MODELS_DIR / "symptoms_list.json"
    save_json(symptoms_out, symptoms)
    trained_files.append(symptoms_out)
    if SYMPTOMS_PATH.parent.exists():
        save_json(SYMPTOMS_PATH, symptoms)
    print("  symptoms_list.json    %d symptoms saved" % len(symptoms))

    # Version manifest
    write_version_manifest(trained_files)

    print("\n-- Accuracy summary ------------------------------------------")
    for name, acc in results.items():
        bar = "#" * int(acc * 20)
        print("  %-20s %.2f%%  %s" % (name, acc * 100, bar))
    print("--------------------------------------------------------------")
    print("\nAll artefacts saved to %s" % MODELS_DIR.resolve())


if __name__ == "__main__":
    main()
