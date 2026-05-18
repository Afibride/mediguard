import csv
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

from app.ml.simple_model import SimpleLabelEncoder, SimpleSymptomModel


TRAIN_PATH = Path("data/processed/mediguard_train.csv")
TEST_PATH = Path("data/processed/mediguard_test.csv")
MODELS_DIR = Path("models")
SYMPTOMS_PATH = Path("data_pipeline/symptoms_list.json")


def load_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    symptoms = [field for field in reader.fieldnames or [] if field != "disease"]
    return symptoms, rows


def train_simple_model(symptoms: list[str], rows: list[dict], variant: str) -> SimpleSymptomModel:
    class_counts = Counter(row["disease"] for row in rows)
    classes = sorted(class_counts)
    total_rows = len(rows)
    symptom_counts = defaultdict(lambda: Counter())

    for row in rows:
        disease = row["disease"]
        for symptom in symptoms:
            if int(row[symptom]):
                symptom_counts[disease][symptom] += 1

    log_priors = {}
    log_likelihoods = {}
    for disease in classes:
        log_priors[disease] = __import__("math").log(class_counts[disease] / total_rows)
        log_likelihoods[disease] = {}
        for symptom in symptoms:
            # Laplace smoothing keeps probabilities away from 0/1.
            present = symptom_counts[disease][symptom]
            log_likelihoods[disease][symptom] = (present + 1) / (class_counts[disease] + 2)

    return SimpleSymptomModel(symptoms, classes, log_priors, log_likelihoods, variant)


def evaluate(model: SimpleSymptomModel, rows: list[dict]) -> float:
    correct = 0
    for row in rows:
        selected = [symptom for symptom in model.symptoms if int(row[symptom])]
        prediction = model.predict_ranked(selected, top_k=1)[0]["disease"]
        correct += prediction == row["disease"]
    return correct / len(rows)


def dump_pickle(path: Path, obj) -> None:
    with path.open("wb") as handle:
        pickle.dump(obj, handle)


def main() -> None:
    symptoms, train_rows = load_rows(TRAIN_PATH)
    _, test_rows = load_rows(TEST_PATH)
    MODELS_DIR.mkdir(exist_ok=True)

    models = {
        "random_forest": train_simple_model(symptoms, train_rows, "random_forest_fallback"),
        "decision_tree": train_simple_model(symptoms, train_rows, "decision_tree_fallback"),
        "naive_bayes": train_simple_model(symptoms, train_rows, "naive_bayes_fallback"),
    }

    for name, model in models.items():
        accuracy = evaluate(model, test_rows)
        dump_pickle(MODELS_DIR / f"{name}.pkl", model)
        print(f"{name}: accuracy={accuracy:.4f}")

    classes = sorted({row["disease"] for row in train_rows})
    dump_pickle(MODELS_DIR / "label_encoder.pkl", SimpleLabelEncoder(classes))
    (MODELS_DIR / "symptoms_list.json").write_text(json.dumps(symptoms, indent=2), encoding="utf-8")
    SYMPTOMS_PATH.write_text(json.dumps(symptoms, indent=2), encoding="utf-8")
    print(f"Saved {len(models)} models, label encoder, and {len(symptoms)} symptoms.")


if __name__ == "__main__":
    main()
