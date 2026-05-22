import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier


TRAIN_PATH = Path("data/processed/mediguard_train.csv")
TEST_PATH = Path("data/processed/mediguard_test.csv")
MODELS_DIR = Path("models")
SYMPTOMS_PATH = Path("data_pipeline/symptoms_list.json")
RANDOM_STATE = 42


def load_dataset(path: Path) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    df = pd.read_csv(path)
    symptoms = [column for column in df.columns if column != "disease"]
    x = df[symptoms].astype(int)
    y = df["disease"].astype(str)
    return x, y, symptoms


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
        "naive_bayes": GaussianNB(),
    }


def save_json(path: Path, data: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> None:
    x_train, y_train, symptoms = load_dataset(TRAIN_PATH)
    x_test, y_test, test_symptoms = load_dataset(TEST_PATH)

    if symptoms != test_symptoms:
        raise ValueError("Train and test symptom columns do not match.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    label_encoder = LabelEncoder()
    label_encoder.fit(y_train)
    joblib.dump(label_encoder, MODELS_DIR / "label_encoder.pkl")

    models = build_models()
    for name, model in models.items():
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        accuracy = accuracy_score(y_test, predictions)
        joblib.dump(model, MODELS_DIR / f"{name}.pkl")
        print(f"{name}: {model.__class__.__name__} accuracy={accuracy:.4f}")

        if name == "random_forest":
            report = classification_report(y_test, predictions, zero_division=0)
            (MODELS_DIR / "random_forest_report.txt").write_text(report, encoding="utf-8")

    save_json(MODELS_DIR / "symptoms_list.json", symptoms)
    save_json(SYMPTOMS_PATH, symptoms)
    print(f"Saved {len(models)} scikit-learn models, label encoder, and {len(symptoms)} symptoms.")


if __name__ == "__main__":
    main()
