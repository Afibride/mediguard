"""
upload_to_hf.py
===============
Uploads MediGuard models AND training datasets to Hugging Face.

Run from mediguard-backend/ root:
    python scripts/upload_to_hf.py

After running, large data files can be removed from git tracking.
Everything needed to reproduce training lives on HuggingFace.

HF repo layout (afiBride/mediguard-models):
    models/
        random_forest.pkl
        decision_tree.pkl
        naive_bayes.pkl
        label_encoder.pkl
        symptoms_list.json
        version.json
        random_forest_report.txt
    datasets/
        mediguard_dataset_full.csv       <- merged real+synthetic training data
        mediguard_train.csv
        mediguard_test.csv
        custom/
            Malaria_Dataset.csv          <- real hospital records
        external/
            <kaggle dataset files>
"""

import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:
    pass

HF_TOKEN = (
    os.environ.get("HF_WRITE_TOKEN")
    or os.environ.get("MODEL_DOWNLOAD_TOKEN")
    or os.environ.get("HF_TOKEN")
)
HF_REPO = "afiBride/mediguard-models"
BASE = Path(__file__).parent.parent

# Files to upload with their destination path in the HF repo
UPLOAD_PLAN: list[tuple[Path, str]] = [
    # ── Models ────────────────────────────────────────────────────────────────
    (BASE / "models/random_forest.pkl",      "models/random_forest.pkl"),
    (BASE / "models/decision_tree.pkl",      "models/decision_tree.pkl"),
    (BASE / "models/naive_bayes.pkl",        "models/naive_bayes.pkl"),
    (BASE / "models/label_encoder.pkl",      "models/label_encoder.pkl"),
    (BASE / "models/symptoms_list.json",     "models/symptoms_list.json"),
    (BASE / "models/version.json",           "models/version.json"),
    (BASE / "models/random_forest_report.txt", "models/random_forest_report.txt"),

    # ── Processed training data ───────────────────────────────────────────────
    (BASE / "data/raw/mediguard_dataset_full.csv",  "datasets/mediguard_dataset_full.csv"),
    (BASE / "data/processed/mediguard_train.csv",   "datasets/mediguard_train.csv"),
    (BASE / "data/processed/mediguard_test.csv",    "datasets/mediguard_test.csv"),

    # ── Custom real-patient CSVs ──────────────────────────────────────────────
    (BASE / "data/custom/Malaria_Dataset.csv", "datasets/custom/Malaria_Dataset.csv"),
]

# External Kaggle downloads — upload every CSV + JSON found under data/external/
def collect_external() -> list[tuple[Path, str]]:
    ext = BASE / "data/external"
    if not ext.exists():
        return []
    pairs = []
    for f in sorted(ext.rglob("*")):
        if f.is_file() and f.suffix.lower() in (".csv", ".json") and f.stat().st_size > 0:
            rel = f.relative_to(BASE / "data/external")
            pairs.append((f, f"datasets/external/{rel.as_posix()}"))
    return pairs


def main() -> None:
    if not HF_TOKEN:
        print("ERROR: HF token not found.")
        print("  Set HF_WRITE_TOKEN or MODEL_DOWNLOAD_TOKEN in .env")
        sys.exit(1)

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("ERROR: pip install huggingface-hub")
        sys.exit(1)

    api = HfApi()

    # Verify repo access
    try:
        info = api.repo_info(repo_id=HF_REPO, repo_type="model", token=HF_TOKEN)
        print(f"Repo: {HF_REPO}  (private={info.private})")
    except Exception as exc:
        print(f"ERROR accessing {HF_REPO}: {exc}")
        sys.exit(1)

    # Build full upload plan (static + external)
    plan = [p for p in UPLOAD_PLAN if p[0].exists()]
    plan += collect_external()

    skipped = [p for p in UPLOAD_PLAN if not p[0].exists()]
    if skipped:
        print(f"\nSkipping {len(skipped)} missing files:")
        for local, _ in skipped:
            print(f"  {local}")

    total_mb = sum(local.stat().st_size for local, _ in plan) / 1024 / 1024
    print(f"\nUploading {len(plan)} files  ({total_mb:.1f} MB total) to {HF_REPO}\n")

    uploaded = 0
    failed = []

    for local, repo_path in plan:
        size_mb = local.stat().st_size / 1024 / 1024
        print(f"  {repo_path:<65} {size_mb:6.1f} MB ... ", end="", flush=True)
        try:
            api.upload_file(
                path_or_fileobj=str(local),
                path_in_repo=repo_path,
                repo_id=HF_REPO,
                repo_type="model",
                token=HF_TOKEN,
                commit_message="Upload datasets and models",
            )
            print("OK")
            uploaded += 1
        except Exception as exc:
            print(f"FAILED: {exc}")
            failed.append(repo_path)

    print(f"\n{uploaded}/{len(plan)} files uploaded to {HF_REPO}")
    if failed:
        print("Failed:")
        for f in failed:
            print(f"  {f}")
        sys.exit(1)

    print("\nAll files are live on Hugging Face:")
    print(f"  https://huggingface.co/{HF_REPO}")

    # Print download URL mapping for .env reference
    print("\nDataset download URLs (add to .env if needed):")
    for _, repo_path in plan:
        if "datasets/" in repo_path:
            url = f"https://huggingface.co/{HF_REPO}/resolve/main/{repo_path}"
            key = Path(repo_path).stem.upper().replace("-", "_")
            print(f"  DATASET_{key}_URL={url}")


if __name__ == "__main__":
    main()
