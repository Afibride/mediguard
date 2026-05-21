"""
Build and ingest MediGuard's curated medical reference vector dataset.

The builder extracts concise, disease-focused facts from approved PDF
references. It avoids storing full pages by keeping only short snippets that
mention a MediGuard disease and contain practical clinical/laboratory terms.

Run from backend root:
    python app/rag/build_medical_reference_dataset.py --extract-only
    python app/rag/build_medical_reference_dataset.py --clear-pinecone --upsert
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
from app.rag.ingest_essentials_pdf import extract_chunks as extract_essentials_chunks
from app.rag.retriever import DISEASE_ALIASES

load_dotenv()

INDEX_NAME = os.environ.get("PINECONE_INDEX", "mediguard-health-knowledge")
BATCH_SIZE = 100
OUTPUT_FILE = BACKEND_ROOT / "data_pipeline" / "mediguard_reference_chunks.json"

ESSENTIALS_PDF = Path(
    r"C:\Users\Fon\Downloads\Essentials of Human Diseases and Conditions by Margaret Frazier Jeanette Drzymkowski z-liborg.pdf"
)

LAB_REFERENCES = [
    {
        "path": Path(r"C:\Users\Fon\Downloads\Monica cheeseburge.pdf"),
        "source": "District Laboratory Practice in Tropical Countries, Part 2",
    },
    {
        "path": Path(r"C:\Users\Fon\Downloads\monica-cheesbrough-district-laboratory-practice-in-tropical-countries-part-1.pdf"),
        "source": "District Laboratory Practice in Tropical Countries, Part 1",
    },
]

LAB_TERMS = {
    "laboratory",
    "diagnosis",
    "diagnostic",
    "test",
    "testing",
    "screen",
    "screening",
    "specimen",
    "sample",
    "smear",
    "stain",
    "gram",
    "culture",
    "microscopy",
    "microscop",
    "antigen",
    "antibody",
    "serology",
    "serological",
    "rapid",
    "wet preparation",
    "blood film",
    "urine",
    "faeces",
    "feces",
    "sputum",
    "csf",
    "pus",
    "discharge",
    "parasite",
    "trophozoite",
    "cyst",
    "ova",
    "microfilariae",
    "acid-fast",
    "afb",
    "diplococci",
    "spirochaetes",
    "spirochetes",
    "vibrio",
    "plasmodium",
    "quality",
    "transport",
    "collection",
}

PATHOGEN_ALIASES = {
    "Malaria": ["plasmodium", "malarial parasite", "blood film"],
    "Tuberculosis": ["mycobacterium tuberculosis", "afb", "acid-fast bacilli", "sputum"],
    "Cholera": ["vibrio cholerae", "v. cholerae", "tcbs"],
    "Gonorrhea": ["gonorrhoea", "gonorrhea", "n. gonorrhoeae", "neisseria gonorrhoeae", "gram negative diplococci"],
    "Syphilis": ["treponema pallidum", "t. pallidum", "spirochaetes", "spirochetes", "vdrl", "rpr"],
    "Chlamydia": ["chlamydia", "chlamydia trachomatis"],
    "Trichomoniasis": ["trichomonas", "t. vaginalis"],
    "Dysentery": ["dysentery", "shigella", "entamoeba histolytica", "blood and mucus"],
    "Gastroenteritis": ["gastroenteritis", "diarrhoeal", "diarrheal", "faeces", "feces"],
    "Filariasis": ["microfilariae", "wuchereria", "brugia"],
    "Onchocerciasis": ["onchocerca", "skin snip", "o. volvulus"],
    "Schistosomiasis": ["schistosoma", "s. haematobium", "s. mansoni"],
    "Meningitis": ["meningitis", "cerebrospinal fluid", "csf"],
    "HIV AIDS": ["hiv", "aids"],
}


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"([a-z])-\s+([a-z])", r"\1\2", text)
    text = re.sub(r"/H\d+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _load_pages(pdf_path: Path) -> list[tuple[int, str]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit("Install pypdf first: pip install pypdf") from exc

    reader = PdfReader(str(pdf_path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = _clean_text(page.extract_text() or "")
        if text:
            pages.append((index, text))
    return pages


def _normalize(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _term_pattern(term: str) -> re.Pattern:
    escaped = re.escape(_normalize(term)).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.I)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9●•])", text)
    return [part.strip(" ●•;:-") for part in parts if 45 <= len(part.strip()) <= 650]


def _disease_aliases() -> dict[str, list[str]]:
    by_disease = {disease["name"]: {disease["name"], disease["slug"].replace("-", " ")} for disease in DISEASES}
    for alias, canonical in DISEASE_ALIASES.items():
        if canonical in by_disease and len(alias) > 3:
            by_disease[canonical].add(alias)
    for disease, aliases in PATHOGEN_ALIASES.items():
        if disease in by_disease:
            by_disease[disease].update(aliases)
    return {name: sorted(aliases, key=len, reverse=True) for name, aliases in by_disease.items()}


def _contains_any(text: str, terms: set[str]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def _lab_score(sentence: str, alias_hit: bool) -> int:
    lower = sentence.lower()
    score = 5 if alias_hit else 0
    score += sum(1 for term in LAB_TERMS if term in lower)
    if re.search(r"\b(detect|identify|differentiate|confirm|collect|examine|report|screen)\b", lower):
        score += 2
    return score


def _extract_lab_chunks_from_reference(reference: dict, aliases_by_disease: dict[str, list[str]]) -> list[dict]:
    pdf_path = reference["path"]
    source = reference["source"]
    if not pdf_path.exists():
        print(f"Skipping missing PDF: {pdf_path}")
        return []

    pages = _load_pages(pdf_path)
    chunks: list[dict] = []

    for disease, aliases in aliases_by_disease.items():
        patterns = [_term_pattern(alias) for alias in aliases if len(_normalize(alias)) > 3]
        snippets = []
        seen = set()
        for page_number, page_text in pages:
            normalized_page = _normalize(page_text)
            if not any(pattern.search(normalized_page) for pattern in patterns):
                continue
            if not _contains_any(page_text, LAB_TERMS):
                continue

            sentences = _sentences(page_text)
            for index, sentence in enumerate(sentences):
                normalized_sentence = _normalize(sentence)
                alias_hit = any(pattern.search(normalized_sentence) for pattern in patterns)
                lab_hit = _contains_any(sentence, LAB_TERMS)
                if not alias_hit and not lab_hit:
                    continue
                if lab_hit and not alias_hit:
                    neighbor = " ".join(sentences[max(0, index - 1): index + 2])
                    if not any(pattern.search(_normalize(neighbor)) for pattern in patterns):
                        continue
                    sentence = _clean_text(neighbor)
                fingerprint = re.sub(r"\W+", "", sentence.lower())[:240]
                if fingerprint in seen:
                    continue
                seen.add(fingerprint)
                snippets.append({
                    "page": page_number,
                    "text": sentence,
                    "score": _lab_score(sentence, alias_hit),
                })

        snippets.sort(key=lambda item: item["score"], reverse=True)
        selected = snippets[:8]
        chunks.extend(_pack_lab_chunks(disease, selected, source))

    return chunks


def _pack_lab_chunks(disease: str, snippets: list[dict], source: str, max_chars: int = 1300) -> list[dict]:
    chunks = []
    parts = []
    pages = []
    slug = re.sub(r"[^a-z0-9]+", "-", disease.lower()).strip("-")
    source_slug = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")[:48]

    for snippet in snippets:
        next_text = " ".join(parts + [snippet["text"]])
        if parts and len(next_text) > max_chars:
            chunks.append(_make_lab_chunk(disease, slug, source_slug, source, parts, pages, len(chunks)))
            parts = [snippet["text"]]
            pages = [snippet["page"]]
        else:
            parts.append(snippet["text"])
            pages.append(snippet["page"])
    if parts:
        chunks.append(_make_lab_chunk(disease, slug, source_slug, source, parts, pages, len(chunks)))
    return chunks[:4]


def _make_lab_chunk(
    disease: str,
    slug: str,
    source_slug: str,
    source: str,
    parts: list[str],
    pages: list[int],
    index: int,
) -> dict:
    return {
        "id": f"lab-{source_slug}-{slug}-{index + 1}",
        "disease": disease,
        "text": _clean_text(f"{disease}. District laboratory notes: " + " ".join(parts)),
        "source": source,
        "pages": sorted(set(pages)),
        "section": "district_laboratory_notes",
        "data_type": "lab_reference",
    }


def build_dataset(output_file: Path = OUTPUT_FILE, include_essentials: bool = True) -> list[dict]:
    chunks: list[dict] = []
    if include_essentials and ESSENTIALS_PDF.exists():
        essentials_output = BACKEND_ROOT / "data_pipeline" / "essentials_disease_chunks.json"
        chunks.extend(extract_essentials_chunks(ESSENTIALS_PDF, essentials_output))

    aliases_by_disease = _disease_aliases()
    for reference in LAB_REFERENCES:
        chunks.extend(_extract_lab_chunks_from_reference(reference, aliases_by_disease))

    deduped = []
    seen_ids = set()
    for chunk in chunks:
        if chunk["id"] in seen_ids:
            continue
        seen_ids.add(chunk["id"])
        deduped.append(chunk)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8")
    return deduped


def _pinecone_client():
    try:
        from pinecone import Pinecone, ServerlessSpec
    except ImportError as exc:
        raise SystemExit("Install Pinecone dependency first: pip install pinecone") from exc

    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise SystemExit("PINECONE_API_KEY is missing from .env")
    return Pinecone(api_key=api_key), ServerlessSpec


def _ensure_index(pc, serverless_spec):
    existing_indexes = [index.name for index in pc.list_indexes()]
    if INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index {INDEX_NAME}...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=serverless_spec(cloud="aws", region="us-east-1"),
        )
        while not pc.describe_index(INDEX_NAME).status["ready"]:
            print("Waiting for index to be ready...")
            time.sleep(5)
    return pc.Index(INDEX_NAME)


def clear_pinecone() -> None:
    pc, serverless_spec = _pinecone_client()
    index = _ensure_index(pc, serverless_spec)
    index.delete(delete_all=True)
    print(f"Cleared all vectors from Pinecone index {INDEX_NAME}.")


def upsert_chunks(chunks: list[dict]) -> None:
    pc, serverless_spec = _pinecone_client()
    index = _ensure_index(pc, serverless_spec)
    description = pc.describe_index(INDEX_NAME)
    index_dimension = getattr(description, "dimension", None) or EMBEDDING_DIM

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
                    "pages": [str(page) for page in chunk.get("pages", [])],
                    "section": chunk["section"],
                    "data_type": chunk["data_type"],
                },
            })
        index.upsert(vectors=vectors)
        total += len(vectors)
        print(f"Upserted {total}/{len(chunks)} reference chunks")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and ingest MediGuard curated PDF reference chunks.")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    parser.add_argument("--extract-only", action="store_true")
    parser.add_argument("--clear-pinecone", action="store_true")
    parser.add_argument("--upsert", action="store_true")
    parser.add_argument("--no-essentials", action="store_true")
    args = parser.parse_args()

    chunks = build_dataset(args.output, include_essentials=not args.no_essentials)
    disease_count = len({chunk["disease"] for chunk in chunks})
    print(f"Wrote {len(chunks)} chunks for {disease_count} diseases to {args.output}")

    if args.clear_pinecone:
        clear_pinecone()
    if args.upsert:
        upsert_chunks(chunks)
        print("MediGuard reference ingestion complete.")
    elif not args.extract_only:
        print("Review the JSON first, then run with --clear-pinecone --upsert to refresh Pinecone.")


if __name__ == "__main__":
    main()
