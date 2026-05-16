"""
One-time Pinecone ingestion for MediGuard encyclopedia RAG chunks.

Run from backend root:
    python app/rag/ingest.py
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from app.rag.embeddings import EMBEDDING_DIM, embed_text

load_dotenv()

INDEX_NAME = os.environ.get("PINECONE_INDEX", "mediguard-health-knowledge")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
CHUNKS_FILE = Path(__file__).resolve().parents[2] / "data_pipeline" / "mediguard_rag_chunks.json"
BATCH_SIZE = 100

def main() -> None:
    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError as exc:
        raise SystemExit("Install Pinecone dependency first: pip install pinecone") from exc

    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is missing from .env")

    chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
    print(f"Loaded {len(chunks)} RAG chunks from {CHUNKS_FILE}")

    pc = Pinecone(api_key=api_key)
    existing_indexes = [index.name for index in pc.list_indexes()]

    if INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index {INDEX_NAME}...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            print("Waiting for index to be ready...")
            time.sleep(5)

    index_description = pc.describe_index(INDEX_NAME)
    index_dimension = getattr(index_description, "dimension", None) or EMBEDDING_DIM
    print(f"Using Pinecone index dimension: {index_dimension}")

    index = pc.Index(INDEX_NAME)
    total_upserted = 0
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        vectors = []
        for chunk in batch:
            vectors.append({
                "id": chunk["id"],
                "values": embed_text(chunk["text"], dim=index_dimension),
                "metadata": {
                    "text": chunk["text"][:1000],
                    "disease": chunk["disease"],
                    "source": chunk.get("source", "Gale Encyclopedia of Medicine"),
                    "type": chunk.get("type", chunk.get("section", "encyclopedia")),
                },
            })
        index.upsert(vectors=vectors)
        total_upserted += len(vectors)
        print(f"Upserted {total_upserted}/{len(chunks)} chunks")

    print("Pinecone ingestion complete.")


if __name__ == "__main__":
    main()
