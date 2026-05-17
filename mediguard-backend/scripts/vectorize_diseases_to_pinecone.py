"""
vectorize_diseases_to_pinecone.py
==================================
Embeds all 50 disease profiles and training examples into Pinecone.

Two vector types are stored in the same index (filter with data_type):
  data_type=disease_profile   — one vector per disease (used for semantic prediction)
  data_type=training_example  — one vector per training row (used to rebuild dataset)

All training vector IDs are saved to data/pinecone_training_ids.json so that
train_from_pinecone.py can fetch them back in batches.

Run from mediguard-backend/:
    python scripts/vectorize_diseases_to_pinecone.py
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

# Allow app package imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from app.data import DISEASES
from app.config import get_settings

BATCH_SIZE = 100
TRAINING_IDS_FILE = Path("data/pinecone_training_ids.json")
TRAIN_CSV = Path("data/processed/mediguard_train.csv")

# Resolved at runtime after connecting to Pinecone
_INDEX_DIM = 384


# ---------------------------------------------------------------------------
# Embedding — tries sentence-transformers, falls back to hash-based embedder
# using whatever dimension the Pinecone index was created with.
# ---------------------------------------------------------------------------

_embedder = None
_use_st = False  # True if sentence-transformers is available


def get_embedder():
    global _embedder, _use_st
    if _embedder is not None:
        return _embedder

    settings = get_settings()
    try:
        from sentence_transformers import SentenceTransformer
        print(f"Loading sentence-transformers model: {settings.embedding_model}")
        _embedder = SentenceTransformer(settings.embedding_model)
        _use_st = True
        print("  Sentence-transformer model loaded.")
    except Exception:
        print(f"  sentence-transformers unavailable — using hash-based embedder (dim={_INDEX_DIM}).")
        _embedder = None  # will use embed_text() directly per-call

    return _embedder


def embed_batch(texts: list[str]) -> list[list[float]]:
    from app.rag.embeddings import embed_text
    embedder = get_embedder()  # ensures _use_st is set

    if _use_st and embedder is not None:
        results = embedder.encode(texts, normalize_embeddings=True)
        if hasattr(results, "tolist"):
            return results.tolist()
        return [r.tolist() if hasattr(r, "tolist") else list(r) for r in results]

    # Hash-based fallback — respect the actual Pinecone index dimension
    return [embed_text(t, dim=_INDEX_DIM) for t in texts]


def embed_one(text: str) -> list[float]:
    return embed_batch([text])[0]


# ---------------------------------------------------------------------------
# Pinecone connection
# ---------------------------------------------------------------------------

def get_pinecone_index():
    global _INDEX_DIM
    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError:
        raise SystemExit("Install pinecone: pip install pinecone-client")

    settings = get_settings()
    api_key = settings.pinecone_api_key or os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is missing. Set it in .env")

    index_name = settings.pinecone_index
    pc = Pinecone(api_key=api_key)
    existing = [idx.name for idx in pc.list_indexes()]

    if index_name not in existing:
        print(f"Creating Pinecone index '{index_name}' (dim={_INDEX_DIM}, cosine)...")
        pc.create_index(
            name=index_name,
            dimension=_INDEX_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print("  Waiting for index to be ready...")
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(5)

    info = pc.describe_index(index_name)
    detected_dim = getattr(info, "dimension", None) or _INDEX_DIM
    _INDEX_DIM = detected_dim  # use the index's actual dimension for all embeddings
    idx = pc.Index(index_name)
    print(f"Connected to Pinecone index '{index_name}' (dim={_INDEX_DIM})")
    return idx


# ---------------------------------------------------------------------------
# Build disease profile vectors
# ---------------------------------------------------------------------------

def build_disease_profile_vectors() -> list[dict]:
    """One rich-text vector per disease for semantic similarity prediction."""
    print(f"\nBuilding disease profile vectors ({len(DISEASES)} diseases)...")
    texts = []
    records = []

    for d in DISEASES:
        name = d["name"]
        symptoms = d.get("symptoms") or []
        symptom_str = ", ".join(symptoms) if symptoms else "unspecified"
        description = (d.get("description") or "")[:400]
        text = (
            f"Disease: {name}. "
            f"Category: {d.get('category', 'General')}. "
            f"Severity: {d.get('severity', 'Medium')}. "
            f"Symptoms: {symptom_str}. "
            f"{description}"
        ).strip()
        texts.append(text)
        records.append({
            "id": f"disease_profile_{d['slug']}",
            "metadata": {
                "disease": name,
                "slug": d["slug"],
                "data_type": "disease_profile",
                "category": d.get("category", "General"),
                "severity": d.get("severity", "Medium"),
                "symptoms": symptoms[:50],
                "description": description,
            },
        })

    # Embed in one batch (only 50 texts)
    vectors_values = embed_batch(texts)
    vectors = []
    for record, values in zip(records, vectors_values):
        vectors.append({
            "id": record["id"],
            "values": values,
            "metadata": record["metadata"],
        })
    print(f"  Built {len(vectors)} disease profile vectors.")
    return vectors


# ---------------------------------------------------------------------------
# Build training example vectors
# ---------------------------------------------------------------------------

def build_training_example_vectors() -> tuple[list[dict], list[str]]:
    """One vector per training CSV row.  Returns (vectors, ids)."""
    if not TRAIN_CSV.exists():
        print(f"  Training CSV not found at {TRAIN_CSV}. Run generate_50_disease_dataset.py first.")
        return [], []

    print(f"\nBuilding training example vectors from {TRAIN_CSV}...")
    with TRAIN_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        symptom_cols = [c for c in (reader.fieldnames or []) if c != "disease"]

    vectors = []
    ids = []
    for i, row in enumerate(rows):
        disease = row["disease"]
        present = [s for s in symptom_cols if row.get(s, "0") == "1"]
        symptom_str = ", ".join(present) if present else "none"
        text = f"Patient with {disease} has symptoms: {symptom_str}."
        vectors.append({
            "_text": text,  # we'll embed in batches, not stored directly
            "id": f"train_{i}",
            "metadata": {
                "disease": disease,
                "data_type": "training_example",
                "present_symptoms": present,
                "symptom_count": len(present),
            },
        })
        ids.append(f"train_{i}")

    print(f"  Prepared {len(vectors)} training example vectors.")

    # Embed in batches to avoid memory spikes
    all_vectors = []
    for start in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[start:start + BATCH_SIZE]
        texts = [v["_text"] for v in batch]
        values_list = embed_batch(texts)
        for v, values in zip(batch, values_list):
            all_vectors.append({
                "id": v["id"],
                "values": values,
                "metadata": v["metadata"],
            })
        print(f"  Embedded {min(start + BATCH_SIZE, len(vectors))}/{len(vectors)}", end="\r")

    print(f"\n  Embedded {len(all_vectors)} training example vectors.")
    return all_vectors, ids


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------

def upsert_in_batches(index, vectors: list[dict], label: str) -> int:
    total = 0
    for start in range(0, len(vectors), BATCH_SIZE):
        batch = vectors[start:start + BATCH_SIZE]
        index.upsert(vectors=batch)
        total += len(batch)
        print(f"  Upserted {total}/{len(vectors)} {label}", end="\r")
    print()
    return total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    idx = get_pinecone_index()

    # 1. Disease profile vectors
    profile_vectors = build_disease_profile_vectors()
    upsert_in_batches(idx, profile_vectors, "disease profiles")
    print(f"  Done: {len(profile_vectors)} disease profiles in Pinecone.")

    # 2. Training example vectors
    training_vectors, training_ids = build_training_example_vectors()
    if training_vectors:
        upsert_in_batches(idx, training_vectors, "training examples")
        TRAINING_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        TRAINING_IDS_FILE.write_text(json.dumps(training_ids, indent=2), encoding="utf-8")
        print(f"  Done: {len(training_vectors)} training examples in Pinecone.")
        print(f"  Training IDs saved to {TRAINING_IDS_FILE}")

    stats = idx.describe_index_stats()
    total_vectors = getattr(stats, "total_vector_count", "unknown")
    print(f"\nPinecone index now contains ~{total_vectors} vectors total.")
    print("\nVectorization complete. Run train_from_pinecone.py to train the model from Pinecone data.")


if __name__ == "__main__":
    main()
