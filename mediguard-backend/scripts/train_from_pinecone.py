"""
train_from_pinecone.py
=======================
Fetches training data stored in Pinecone by vectorize_diseases_to_pinecone.py,
reconstructs the symptom-disease dataset, and trains the SimpleSymptomModel.

The trained models are saved to models/ exactly as generate_50_disease_dataset.py does,
so the predictor picks them up automatically on next startup.

Run from mediguard-backend/:
    python scripts/train_from_pinecone.py
"""

import json
import pickle
import sys
from pathlib import Path

# Allow app package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
from app.ml.simple_model import SimpleLabelEncoder, SimpleSymptomModel
from app.ml.train import train_simple_model, evaluate

TRAINING_IDS_FILE = Path("data/pinecone_training_ids.json")
SYMPTOMS_LIST_FILE = Path("data_pipeline/symptoms_list.json")
MODELS_DIR = Path("models")
FETCH_BATCH = 100  # Pinecone fetch limit per call


# ---------------------------------------------------------------------------
# Pinecone connection
# ---------------------------------------------------------------------------

def get_pinecone_index():
    try:
        from pinecone import Pinecone
    except ImportError:
        raise SystemExit("Install pinecone: pip install pinecone-client")

    settings = get_settings()
    import os
    api_key = settings.pinecone_api_key or os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is missing from .env")

    pc = Pinecone(api_key=api_key)
    index_name = settings.pinecone_index
    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        raise SystemExit(
            f"Index '{index_name}' does not exist in Pinecone. "
            "Run vectorize_diseases_to_pinecone.py first."
        )

    idx = pc.Index(index_name)
    print(f"Connected to Pinecone index '{index_name}'")
    return idx


# ---------------------------------------------------------------------------
# Fetch training data from Pinecone
# ---------------------------------------------------------------------------

def fetch_training_rows(idx) -> tuple[list[str], list[dict]]:
    """
    Fetches all training_example vectors from Pinecone using stored IDs.
    Returns (symptoms_list, rows) where each row is a dict {symptom: "0"/"1", ..., disease: "..."}
    """
    if not TRAINING_IDS_FILE.exists():
        raise SystemExit(
            f"Training IDs file not found at {TRAINING_IDS_FILE}. "
            "Run vectorize_diseases_to_pinecone.py first."
        )

    all_ids: list[str] = json.loads(TRAINING_IDS_FILE.read_text(encoding="utf-8"))
    print(f"Fetching {len(all_ids)} training vectors from Pinecone...")

    # Load the canonical symptom list
    if not SYMPTOMS_LIST_FILE.exists():
        raise SystemExit(f"Symptoms list not found at {SYMPTOMS_LIST_FILE}.")
    symptoms: list[str] = json.loads(SYMPTOMS_LIST_FILE.read_text(encoding="utf-8"))

    rows = []
    fetched = 0
    for start in range(0, len(all_ids), FETCH_BATCH):
        batch_ids = all_ids[start:start + FETCH_BATCH]
        result = idx.fetch(ids=batch_ids)
        # Pinecone v5 returns a FetchResponse; .vectors is a dict id->VectorRecord
        vectors_dict = result.vectors if hasattr(result, "vectors") else result.get("vectors", {})

        for vec_id in batch_ids:
            vec = vectors_dict.get(vec_id)
            if vec is None:
                continue
            meta = vec.metadata if hasattr(vec, "metadata") else vec.get("metadata", {})
            disease = meta.get("disease", "")
            present_symptoms = set(meta.get("present_symptoms", []))

            # Reconstruct binary row (matching CSV format)
            row = {s: "1" if s in present_symptoms else "0" for s in symptoms}
            row["disease"] = disease
            rows.append(row)

        fetched += len(batch_ids)
        print(f"  Fetched {fetched}/{len(all_ids)}", end="\r")

    print(f"\n  Retrieved {len(rows)} training rows from Pinecone.")
    return symptoms, rows


# ---------------------------------------------------------------------------
# Train & save
# ---------------------------------------------------------------------------

def train_and_save(symptoms: list[str], rows: list[dict]) -> None:
    if not rows:
        raise SystemExit("No training rows found. Aborting.")

    # Simple 80/20 split (deterministic)
    split = int(len(rows) * 0.8)
    train_rows = rows[:split]
    test_rows = rows[split:]
    print(f"  Train: {len(train_rows)}  Test: {len(test_rows)}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print("\nTraining models from Pinecone data...")
    for variant_name, variant_tag in [
        ("random_forest", "random_forest_pinecone"),
        ("decision_tree", "decision_tree_pinecone"),
        ("naive_bayes",   "naive_bayes_pinecone"),
    ]:
        model = train_simple_model(symptoms, train_rows, variant_tag)
        acc = evaluate(model, test_rows)
        pkl_path = MODELS_DIR / f"{variant_name}.pkl"
        with pkl_path.open("wb") as f:
            pickle.dump(model, f)
        print(f"  {variant_name}: accuracy={acc:.4f}  -> saved {pkl_path}")

    # Label encoder
    classes = sorted({r["disease"] for r in train_rows})
    encoder = SimpleLabelEncoder(classes)
    enc_path = MODELS_DIR / "label_encoder.pkl"
    with enc_path.open("wb") as f:
        pickle.dump(encoder, f)
    print(f"  Label encoder saved ({len(classes)} classes) -> {enc_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Train from Pinecone ===\n")
    idx = get_pinecone_index()
    symptoms, rows = fetch_training_rows(idx)
    train_and_save(symptoms, rows)
    print("\nDone. Restart the API server to load the updated models.")


if __name__ == "__main__":
    main()
