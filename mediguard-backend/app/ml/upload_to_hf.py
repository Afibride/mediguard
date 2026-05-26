"""
Upload trained MediGuard models to Hugging Face Hub.

Run this after training:
    cd mediguard-backend
    python -m app.ml.upload_to_hf

Uploads:
    models/random_forest.pkl
    models/decision_tree.pkl
    models/naive_bayes.pkl
    models/label_encoder.pkl
    models/symptoms_list.json
    models/random_forest_report.txt   (accuracy report)
    models/version.json               (SHA-256 manifest for auto-update)

The HF_TOKEN is read from the environment or .env file.
"""

import json
import sys
from pathlib import Path

# Ensure .env is loaded so MODEL_DOWNLOAD_TOKEN is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

import os

# HF_WRITE_TOKEN needs write/repo.write permission on the HF repo.
# Generate at: https://huggingface.co/settings/tokens  -> New token -> Role: Write
# Add to .env:  HF_WRITE_TOKEN=hf_xxxxxxx
HF_TOKEN = (
    os.environ.get("HF_WRITE_TOKEN")
    or os.environ.get("MODEL_DOWNLOAD_TOKEN")
    or os.environ.get("HF_TOKEN")
)
HF_REPO  = "afiBride/mediguard-models"

MODELS_DIR = Path("models")

UPLOAD_FILES = [
    "random_forest.pkl",
    "decision_tree.pkl",
    "naive_bayes.pkl",
    "label_encoder.pkl",
    "symptoms_list.json",
    "random_forest_report.txt",
    "version.json",
]


def main() -> None:
    if not HF_TOKEN:
        print("ERROR: HF token not found. Set MODEL_DOWNLOAD_TOKEN in .env")
        sys.exit(1)

    try:
        from huggingface_hub import HfApi
    except ImportError:
        print("ERROR: huggingface_hub not installed. Run: pip install huggingface-hub")
        sys.exit(1)

    api = HfApi()

    # Verify repo exists and we have write access
    try:
        info = api.repo_info(repo_id=HF_REPO, repo_type="model", token=HF_TOKEN)
        print("Repo: %s  (private=%s)" % (HF_REPO, info.private))
    except Exception as exc:
        print("ERROR accessing repo %s: %s" % (HF_REPO, exc))
        sys.exit(1)

    # Show version.json summary before uploading
    version_path = MODELS_DIR / "version.json"
    if version_path.exists():
        v = json.loads(version_path.read_text(encoding="utf-8"))
        print("Uploading models trained at: %s" % v.get("trained_at", "unknown"))

    # Upload each file
    uploaded = 0
    failed = []
    for filename in UPLOAD_FILES:
        local = MODELS_DIR / filename
        if not local.exists():
            print("  SKIP  %s  (not found locally)" % filename)
            continue

        size_kb = local.stat().st_size / 1024
        print("  uploading %-30s  (%.1f KB) ..." % (filename, size_kb), end=" ", flush=True)
        try:
            api.upload_file(
                path_or_fileobj=str(local),
                path_in_repo=filename,
                repo_id=HF_REPO,
                repo_type="model",
                token=HF_TOKEN,
                commit_message="Auto-upload from training run",
            )
            print("OK")
            uploaded += 1
        except Exception as exc:
            print("FAILED: %s" % exc)
            failed.append(filename)

    print("\n%d/%d files uploaded to %s" % (uploaded, len(UPLOAD_FILES), HF_REPO))
    if failed:
        print("Failed: %s" % ", ".join(failed))
        sys.exit(1)
    else:
        print("All models are live on Hugging Face.")


if __name__ == "__main__":
    main()
