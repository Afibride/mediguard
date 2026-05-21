"""
vectorize_cheesbrough.py
========================
Extracts clinical disease knowledge from Monica Cheesbrough's
"District Laboratory Practice in Tropical Countries" (Parts 1 & 2),
chunks it, and uploads to Pinecone as 'clinical_reference' vectors.

These chunks give the RAG pipeline authoritative, Africa-specific
clinical information sourced from the standard tropical-medicine
laboratory reference for sub-Saharan Africa.

Run from mediguard-backend/ root:
    python scripts/vectorize_cheesbrough.py

Prerequisites:
    pip install pypdf
    .env must have PINECONE_API_KEY and OPENAI_API_KEY
"""

import os
import re
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PDF_PART1 = Path(r"C:/Users/Fon/Downloads/monica-cheesbrough-district-laboratory-practice-in-tropical-countries-part-1.pdf")
PDF_PART2 = Path(r"C:/Users/Fon/Downloads/Monica cheeseburge.pdf")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
INDEX_NAME       = os.getenv("PINECONE_INDEX", "mediguard-health-knowledge")
EMBED_MODEL      = "text-embedding-3-large"
EMBED_DIM        = 1024

CHUNK_SIZE   = 500   # target words per chunk
CHUNK_OVERLAP = 80   # word overlap between consecutive chunks
BATCH_SIZE   = 50    # Pinecone upsert batch size

# Diseases we care about — used to score page relevance
DISEASE_TERMS = {
    "malaria", "typhoid", "cholera", "tuberculosis", "tb",
    "pneumonia", "meningitis", "dysentery", "gastroenteritis",
    "hepatitis", "hiv", "aids", "gonorrhoea", "gonorrhea",
    "syphilis", "chlamydia", "trichomoniasis", "herpes",
    "dengue", "yellow fever", "chickenpox", "varicella",
    "measles", "mumps", "rubella", "tetanus", "pertussis",
    "whooping cough", "diphtheria", "diabetes", "hypertension",
    "anaemia", "anemia", "sickle cell", "onchocerciasis",
    "filariasis", "scabies", "ringworm", "leprosy", "brucellosis",
    "leptospirosis", "typhus", "septicaemia", "septicemia",
    "urinary tract", "kidney", "appendicitis", "asthma",
    "conjunctivitis", "tonsillitis", "sinusitis", "epilepsy",
    "migraine", "appendicitis",
}

CLINICAL_TERMS = {
    "clinical features", "signs and symptoms", "symptoms",
    "diagnosis", "treatment", "prevention", "pathogenesis",
    "clinical presentation", "causes", "complications",
    "epidemiology", "incubation", "prognosis",
}

# ---------------------------------------------------------------------------
# Step 1: Extract and clean text from PDFs
# ---------------------------------------------------------------------------

def clean_text(raw: str) -> str:
    """Clean extracted PDF text — remove artifacts, normalize whitespace."""
    # Remove non-printable / replacement chars
    text = raw.replace("\x00", "").replace("�", " ")
    # Remove PDF encoding artifacts like /H18546 /H11003 etc.
    text = re.sub(r"/H\d+", " ", text)
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize line endings
    text = re.sub(r"\r\n|\r", "\n", text)
    # Remove lines that are just page numbers or section codes
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if re.fullmatch(r"\d{1,4}", stripped):
            continue
        if len(stripped) < 3:
            continue
        lines.append(stripped)
    return "\n".join(lines)


def page_relevance(text: str) -> float:
    """Score 0–1 for how clinically relevant a page is."""
    lower = text.lower()
    disease_hits = sum(1 for t in DISEASE_TERMS if t in lower)
    clinical_hits = sum(1 for t in CLINICAL_TERMS if t in lower)
    return (disease_hits * 2 + clinical_hits) / (len(DISEASE_TERMS) * 2 + len(CLINICAL_TERMS))


def extract_relevant_pages(pdf_path: Path, label: str, min_score: float = 0.04) -> list[dict]:
    """Extract pages above the relevance threshold."""
    try:
        import pypdf
    except ImportError:
        print("pypdf not installed. Run: pip install pypdf")
        sys.exit(1)

    print(f"  Reading {pdf_path.name} …")
    reader = pypdf.PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        if len(raw.strip()) < 50:
            continue
        cleaned = clean_text(raw)
        score = page_relevance(cleaned)
        if score >= min_score:
            pages.append({
                "page": i + 1,
                "source": label,
                "text": cleaned,
                "score": score,
            })
    print(f"    {label}: {len(reader.pages)} pages -> {len(pages)} relevant")
    return pages


# ---------------------------------------------------------------------------
# Step 2: Identify disease sections and tag chunks
# ---------------------------------------------------------------------------

DISEASE_SECTION_MAP = {
    "malaria": "Malaria",
    "falciparum": "Malaria",
    "plasmodium": "Malaria",
    "typhoid": "Typhoid Fever",
    "salmonella typhi": "Typhoid Fever",
    "cholera": "Cholera",
    "vibrio cholerae": "Cholera",
    "tuberculosis": "Tuberculosis",
    "mycobacterium tuberculosis": "Tuberculosis",
    "pneumonia": "Pneumonia",
    "meningitis": "Meningitis",
    "dysentery": "Dysentery",
    "shigella": "Dysentery",
    "amoebic dysentery": "Dysentery",
    "gastroenteritis": "Gastroenteritis",
    "hepatitis a": "Hepatitis A",
    "hepatitis b": "Hepatitis B",
    "hepatitis c": "Hepatitis C",
    "hiv": "HIV AIDS",
    "aids": "HIV AIDS",
    "gonorrhoea": "Gonorrhea",
    "gonorrhea": "Gonorrhea",
    "neisseria gonorrhoeae": "Gonorrhea",
    "syphilis": "Syphilis",
    "treponema pallidum": "Syphilis",
    "chlamydia": "Chlamydia",
    "trichomoniasis": "Trichomoniasis",
    "trichomonas vaginalis": "Trichomoniasis",
    "herpes": "Genital Herpes",
    "dengue": "Dengue Fever",
    "yellow fever": "Yellow Fever",
    "chickenpox": "Chickenpox",
    "varicella": "Chickenpox",
    "measles": "Measles",
    "mumps": "Mumps",
    "rubella": "Rubella",
    "tetanus": "Tetanus",
    "clostridium tetani": "Tetanus",
    "whooping cough": "Whooping Cough",
    "pertussis": "Whooping Cough",
    "bordetella": "Whooping Cough",
    "diphtheria": "Diphtheria",
    "corynebacterium": "Diphtheria",
    "diabetes": "Diabetes Mellitus",
    "hypertension": "Hypertension",
    "anaemia": "Iron Deficiency Anemia",
    "anemia": "Iron Deficiency Anemia",
    "sickle cell": "Sickle Cell Crisis",
    "onchocerciasis": "Onchocerciasis",
    "onchocerca volvulus": "Onchocerciasis",
    "filariasis": "Filariasis",
    "wuchereria": "Filariasis",
    "scabies": "Scabies",
    "sarcoptes": "Scabies",
    "ringworm": "Ringworm",
    "tinea": "Ringworm",
    "leprosy": "Onchocerciasis",   # map leprosy content as related tropical skin
    "brucellosis": "Brucellosis",
    "brucella": "Brucellosis",
    "leptospirosis": "Leptospirosis",
    "leptospira": "Leptospirosis",
    "typhus": "Typhus",
    "rickettsia": "Typhus",
    "septicaemia": "Septicemia",
    "septicemia": "Septicemia",
    "urinary tract infection": "Cystitis UTI",
    "uti": "Cystitis UTI",
    "kidney stone": "Kidney Stones",
    "renal calculi": "Kidney Stones",
    "appendicitis": "Appendicitis",
    "asthma": "Asthma",
    "conjunctivitis": "Conjunctivitis",
    "tonsillitis": "Tonsillitis",
    "sinusitis": "Sinusitis",
    "epilepsy": "Epilepsy",
    "migraine": "Migraine",
    "pelvic inflammatory": "Pelvic Inflammatory Disease",
    "pid": "Pelvic Inflammatory Disease",
    "peptic ulcer": "Helicobacteriosis PepticUlcer",
    "helicobacter": "Helicobacteriosis PepticUlcer",
}


def detect_diseases(text: str) -> list[str]:
    lower = text.lower()
    found = set()
    for term, disease in DISEASE_SECTION_MAP.items():
        if term in lower:
            found.add(disease)
    return sorted(found)


# ---------------------------------------------------------------------------
# Step 3: Sliding-window chunker
# ---------------------------------------------------------------------------

def chunk_text(text: str, source: str, page: int,
               size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    words = text.split()
    if len(words) < 30:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + size, len(words))
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words)
        diseases = detect_diseases(chunk)
        chunks.append({
            "text": chunk,
            "source": source,
            "page": page,
            "diseases": diseases,
            "word_count": len(chunk_words),
        })
        if end >= len(words):
            break
        start += size - overlap

    return chunks


# ---------------------------------------------------------------------------
# Step 4: Embed with OpenAI
# ---------------------------------------------------------------------------

_openai_client = None

def get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def embed_batch(texts: list[str]) -> list[list[float]]:
    client = get_openai()
    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
        dimensions=EMBED_DIM,
    )
    return [item.embedding for item in resp.data]


# ---------------------------------------------------------------------------
# Step 5: Upsert to Pinecone
# ---------------------------------------------------------------------------

_pinecone_index = None

def get_pinecone():
    global _pinecone_index
    if _pinecone_index is None:
        from pinecone import Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        _pinecone_index = pc.Index(INDEX_NAME)
    return _pinecone_index


def upsert_chunks(chunks: list[dict], id_prefix: str) -> int:
    index = get_pinecone()
    total = 0

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]

        try:
            embeddings = embed_batch(texts)
        except Exception as e:
            print(f"    Embed error (skipping batch): {e}")
            continue

        vectors = []
        for j, (chunk, emb) in enumerate(zip(batch, embeddings)):
            vec_id = f"{id_prefix}_{i + j}"
            vectors.append({
                "id": vec_id,
                "values": emb,
                "metadata": {
                    "text": chunk["text"][:1000],   # Pinecone metadata limit
                    "source": chunk["source"],
                    "page": chunk["page"],
                    "diseases": ", ".join(chunk["diseases"]) if chunk["diseases"] else "general",
                    "chunk_type": "clinical_reference",
                    "word_count": chunk["word_count"],
                },
            })

        try:
            index.upsert(vectors=vectors)
            total += len(vectors)
        except Exception as e:
            print(f"    Pinecone upsert error: {e}")

        time.sleep(0.3)   # rate-limit courtesy pause

    return total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Cheesbrough PDF -> Pinecone vectorization pipeline")
    print("=" * 60)

    if not PINECONE_API_KEY or not OPENAI_API_KEY:
        print("ERROR: PINECONE_API_KEY and OPENAI_API_KEY must be set in .env")
        sys.exit(1)

    # Verify PDFs exist
    for path in [PDF_PART1, PDF_PART2]:
        if not path.exists():
            print(f"ERROR: PDF not found: {path}")
            sys.exit(1)

    # Extract relevant pages
    print("\n[1/4] Extracting clinical pages from PDFs …")
    pages_p1 = extract_relevant_pages(PDF_PART1, "Cheesbrough_Part1")
    pages_p2 = extract_relevant_pages(PDF_PART2, "Cheesbrough_Part2")
    all_pages = pages_p1 + pages_p2
    print(f"  Total relevant pages: {len(all_pages)}")

    # Chunk
    print("\n[2/4] Chunking text …")
    all_chunks = []
    for p in all_pages:
        chunks = chunk_text(p["text"], p["source"], p["page"])
        all_chunks.extend(chunks)

    # Filter — keep only chunks that reference at least one disease OR have strong clinical terms
    def is_valuable(chunk: dict) -> bool:
        if chunk["diseases"]:
            return True
        lower = chunk["text"].lower()
        return any(ct in lower for ct in CLINICAL_TERMS)

    all_chunks = [c for c in all_chunks if is_valuable(c)]
    print(f"  Total chunks to vectorize: {len(all_chunks)}")

    # Disease distribution
    from collections import Counter
    disease_counts: Counter = Counter()
    for c in all_chunks:
        for d in c["diseases"]:
            disease_counts[d] += 1
    print(f"  Diseases covered: {len(disease_counts)}")
    for d, cnt in sorted(disease_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"    {d}: {cnt} chunks")

    if not all_chunks:
        print("No chunks found — exiting.")
        sys.exit(0)

    # Embed and upsert
    print(f"\n[3/4] Embedding and uploading {len(all_chunks)} chunks to Pinecone …")
    total_uploaded = upsert_chunks(all_chunks, "cheesb")
    print(f"  Uploaded: {total_uploaded} vectors")

    # Verify index stats
    print("\n[4/4] Verifying Pinecone index …")
    index = get_pinecone()
    stats = index.describe_index_stats()
    print(f"  Total vectors in index: {stats.get('total_vector_count', stats)}")

    print("\nDone. Cheesbrough clinical knowledge is now in Pinecone.")


if __name__ == "__main__":
    main()
