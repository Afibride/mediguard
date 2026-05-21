"""
Extract concise disease notes from "Essentials of Human Diseases and Conditions"
and optionally upsert them to Pinecone.

Run from backend root:
    python app/rag/ingest_essentials_pdf.py --extract-only
    python app/rag/ingest_essentials_pdf.py --upsert

This script intentionally does not vectorize whole book pages. It keeps short,
topic-focused snippets for MediGuard diseases so retrieval stays accurate and
does not flood Pinecone with unrelated textbook text.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.data import DISEASES
from app.rag.embeddings import EMBEDDING_DIM, embed_text
from app.rag.retriever import DISEASE_ALIASES

load_dotenv()

DEFAULT_PDF = Path(
    r"C:\Users\Fon\Downloads\Essentials of Human Diseases and Conditions by Margaret Frazier Jeanette Drzymkowski z-liborg.pdf"
)
OUTPUT_FILE = BACKEND_ROOT / "data_pipeline" / "essentials_disease_chunks.json"
PAGE_CACHE_FILE = BACKEND_ROOT / "data_pipeline" / "essentials_pdf_pages_cache.json"
INDEX_NAME = os.environ.get("PINECONE_INDEX", "mediguard-health-knowledge")
BATCH_SIZE = 100
SOURCE_NAME = "Essentials of Human Diseases and Conditions, 6th Ed."

IMPORTANT_TERMS = {
    "definition",
    "description",
    "etiology",
    "cause",
    "caused",
    "risk",
    "risk factor",
    "symptom",
    "sign",
    "diagnosis",
    "diagnostic",
    "laboratory",
    "test",
    "treatment",
    "therapy",
    "management",
    "medication",
    "prevention",
    "prevent",
    "complication",
    "prognosis",
    "emergency",
    "urgent",
    "patient education",
    "assessment",
}


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"([a-z])-\s+([a-z])", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [part.strip() for part in parts if 40 <= len(part.strip()) <= 550]


def _term_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term.lower()).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.I)


def _disease_aliases() -> dict[str, list[str]]:
    by_disease = {disease["name"]: {disease["name"], disease["slug"].replace("-", " ")} for disease in DISEASES}
    for alias, canonical in DISEASE_ALIASES.items():
        if canonical in by_disease and len(alias) > 3:
            by_disease[canonical].add(alias)
    return {name: sorted(aliases, key=len, reverse=True) for name, aliases in by_disease.items()}


def _load_pages(pdf_path: Path) -> list[tuple[int, str]]:
    use_cache = os.environ.get("ESSENTIALS_CACHE_PAGES") == "1"
    if use_cache and PAGE_CACHE_FILE.exists():
        cached = json.loads(PAGE_CACHE_FILE.read_text(encoding="utf-8"))
        return [(item["page"], item["text"]) for item in cached]

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit("Install pypdf first: pip install pypdf") from exc

    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
        if text:
            pages.append((index, text))
    if use_cache:
        PAGE_CACHE_FILE.write_text(
            json.dumps([{"page": page, "text": text} for page, text in pages], ensure_ascii=False),
            encoding="utf-8",
        )
    return pages


def _score_sentence(sentence: str, alias_hit: bool) -> int:
    lower = sentence.lower()
    score = 4 if alias_hit else 0
    score += sum(1 for term in IMPORTANT_TERMS if term in lower)
    if re.search(r"\b(fever|pain|rash|cough|vomit|diarrhea|bleeding|discharge|swelling)\b", lower):
        score += 1
    if re.search(r"\b(antibiotic|vaccine|surgery|screening|blood test|x ray|culture)\b", lower):
        score += 1
    return score


def _build_full_text(pages: list[tuple[int, str]]) -> str:
    return " ".join(f" [PAGE:{page}] {text}" for page, text in pages)


def _page_numbers(text: str) -> list[int]:
    return [int(match) for match in re.findall(r"\[PAGE:(\d+)\]", text)]


def _strip_page_markers(text: str) -> str:
    return re.sub(r"\s*\[PAGE:\d+\]\s*", " ", text)


def _entry_pattern(alias: str) -> re.Pattern:
    escaped = re.escape(alias).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?:/[A-Z][A-Za-z ]{{2,45}})?\s+Description\b", re.I)


def _generic_entry_pattern() -> re.Pattern:
    return re.compile(r"\b[A-Z][A-Za-z][A-Za-z /()'-]{2,70}\s+Description\b")


def _find_entry_block(full_text: str, aliases: list[str]) -> str | None:
    starts = []
    for alias in aliases:
        match = _entry_pattern(alias).search(full_text)
        if match:
            starts.append(match.start())
    if not starts:
        return None

    start = min(starts)
    next_match = _generic_entry_pattern().search(full_text, start + 80)
    end = next_match.start() if next_match else min(len(full_text), start + 9000)
    return full_text[start:end]


def _extract_disease_notes(pages: list[tuple[int, str]], full_text: str, disease: str, aliases: list[str]) -> list[dict]:
    patterns = [_term_pattern(alias) for alias in aliases]
    candidates: list[dict] = []
    seen = set()

    entry_block = _find_entry_block(full_text, aliases)
    search_units = []
    if entry_block:
        pages_in_block = _page_numbers(entry_block) or [0]
        search_units.append((pages_in_block[0], _strip_page_markers(entry_block), True))
    else:
        return []

    for page_number, text, from_entry in search_units:
        sentences = _sentences(text)
        for index, sentence in enumerate(sentences):
            alias_hit = any(pattern.search(sentence.lower()) for pattern in patterns)
            important_hit = any(term in sentence.lower() for term in IMPORTANT_TERMS)
            if from_entry:
                if not alias_hit and not important_hit and index > 1:
                    continue
            elif not alias_hit and not important_hit:
                continue

            if from_entry:
                heading_match = next((_entry_pattern(alias).search(sentence) for alias in aliases if _entry_pattern(alias).search(sentence)), None)
                first_alias = next((pattern.search(sentence.lower()) for pattern in patterns if pattern.search(sentence.lower())), None)
                trim_match = heading_match or first_alias
                if trim_match and trim_match.start() > 0:
                    sentence = sentence[trim_match.start():].strip()
                sentence = re.sub(
                    r"ICD-9-CM.*?(?=(Symptoms and Signs|Etiology|Diagnosis|Treatment|Prevention|Prognosis|Patient Screening|Patient Teaching|$))",
                    "",
                    sentence,
                    flags=re.I,
                )
                sentence = re.sub(r"\bICD-10-CM\s+Code\s+[A-Z0-9.()=\-\s]+", " ", sentence)
                sentence = re.sub(r"\s*•\s*Figure\s+\d+[-–]\d+.*?(?=[A-Z][a-z]+:|Symptoms and Signs|Etiology|Diagnosis|Treatment|Prevention|$)", " ", sentence)
                sentence = _clean_text(sentence)
                if len(sentence) < 40 or ("rocky mountain spotted fever" in sentence.lower() and disease != "Rocky Mountain Spotted Fever"):
                    continue

            window = [sentence] if from_entry else sentences[max(0, index - 1): index + 2]
            text = _clean_text(" ".join(window))
            fingerprint = re.sub(r"\W+", "", text.lower())[:220]
            if not text or fingerprint in seen:
                continue
            seen.add(fingerprint)
            candidates.append({
                "page": page_number,
                "text": text,
                "score": _score_sentence(sentence, alias_hit) + (3 if from_entry else 0),
            })

    candidates.sort(key=lambda item: item["score"], reverse=True)
    return candidates[:12]


def _chunk_notes(disease: str, notes: list[dict], max_chars: int = 1300) -> list[dict]:
    chunks: list[dict] = []
    current_parts: list[str] = []
    current_pages: list[int] = []

    for note in notes:
        part = note["text"]
        next_text = " ".join(current_parts + [part])
        if current_parts and len(next_text) > max_chars:
            chunks.append(_make_chunk(disease, current_parts, current_pages, len(chunks)))
            current_parts = [part]
            current_pages = [note["page"]]
        else:
            current_parts.append(part)
            current_pages.append(note["page"])

    if current_parts:
        chunks.append(_make_chunk(disease, current_parts, current_pages, len(chunks)))
    return chunks[:6]


def _make_chunk(disease: str, parts: list[str], pages: list[int], index: int) -> dict:
    text = _clean_text(f"{disease}. Important clinical notes: " + " ".join(parts))
    return {
        "id": f"essentials-{re.sub(r'[^a-z0-9]+', '-', disease.lower()).strip('-')}-{index + 1}",
        "disease": disease,
        "text": text,
        "source": SOURCE_NAME,
        "pages": sorted(set(pages)),
        "section": "important_clinical_notes",
        "data_type": "disease_reference",
    }


def extract_chunks(pdf_path: Path = DEFAULT_PDF, output_file: Path = OUTPUT_FILE) -> list[dict]:
    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {pdf_path}")

    pages = _load_pages(pdf_path)
    full_text = _build_full_text(pages)
    aliases_by_disease = _disease_aliases()
    chunks: list[dict] = []

    for disease, aliases in aliases_by_disease.items():
        notes = _extract_disease_notes(pages, full_text, disease, aliases)
        if notes:
            chunks.extend(_chunk_notes(disease, notes))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    return chunks


def upsert_chunks(chunks: list[dict]) -> None:
    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError as exc:
        raise SystemExit("Install Pinecone dependency first: pip install pinecone") from exc

    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is missing from .env")

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

    description = pc.describe_index(INDEX_NAME)
    index_dimension = getattr(description, "dimension", None) or EMBEDDING_DIM
    index = pc.Index(INDEX_NAME)

    total = 0
    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]
        vectors = []
        for chunk in batch:
            vectors.append({
                "id": chunk["id"],
                "values": embed_text(chunk["text"], dim=index_dimension),
                "metadata": {
                    "text": chunk["text"][:1600],
                    "disease": chunk["disease"],
                    "source": chunk["source"],
                    "pages": [str(page) for page in chunk["pages"]],
                    "section": chunk["section"],
                    "data_type": chunk["data_type"],
                },
            })
        index.upsert(vectors=vectors)
        total += len(vectors)
        print(f"Upserted {total}/{len(chunks)} Essentials chunks")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and ingest concise Essentials PDF disease chunks.")
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--upsert", action="store_true")
    args = parser.parse_args()

    chunks = extract_chunks(args.pdf, args.output)
    disease_count = len({chunk["disease"] for chunk in chunks})
    print(f"Wrote {len(chunks)} chunks for {disease_count} diseases to {args.output}")

    if args.upsert:
        upsert_chunks(chunks)
        print("Pinecone Essentials ingestion complete.")
    elif not args.extract_only:
        print("Review the JSON first, then run again with --upsert to vectorize it to Pinecone.")


if __name__ == "__main__":
    main()
