"""
model_store.py — Download and auto-update MediGuard model artefacts.

On server startup  ensure_model_files() is called:
  1. If a model file is missing → download it from Hugging Face.
  2. If version.json on HF has a different SHA-256 for any file → re-download
     that file automatically (zero-downtime hot-swap via temp file + atomic replace).

This means deploying a new model is as simple as:
    python -m app.ml.train            # retrain locally
    python -m app.ml.upload_to_hf     # push to HF (needs write token)

Every running server will pick up the updated file within one restart.
If you want live reloads without restart, schedule a periodic call to
check_and_update_models() via APScheduler (e.g. every 6 hours).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# File manifest — maps logical name -> (settings URL attr, local destination)
# ---------------------------------------------------------------------------

MODEL_TARGETS: dict[str, tuple[str, Path]] = {
    "random_forest":  ("model_random_forest_url",   Path("models/random_forest.pkl")),
    "decision_tree":  ("model_decision_tree_url",   Path("models/decision_tree.pkl")),
    "naive_bayes":    ("model_naive_bayes_url",     Path("models/naive_bayes.pkl")),
    "label_encoder":  ("model_label_encoder_url",  Path("models/label_encoder.pkl")),
    "model_symptoms": ("model_symptoms_list_url",  Path("models/symptoms_list.json")),
    # Cameroon herbs remedy lookup — downloaded alongside models so the
    # predict endpoint can suggest traditional remedies without a restart.
    "herbs_remedies": ("model_herbs_remedies_url", Path("data/herbs_remedies.json")),
}

# The version manifest is stored alongside the model files on HF.
# Its URL is derived by replacing the filename in any model URL.
_VERSION_FILENAME = "version.json"
_LOCAL_VERSION    = Path("models/version.json")


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _request_headers(token: str | None) -> dict[str, str]:
    h = {"User-Agent": "MediGuard-ModelDownloader/2.0"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _fetch_url_bytes(url: str, timeout: int, token: str | None = None) -> bytes:
    req = Request(url, headers=_request_headers(token))
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _download_file(url: str, destination: Path, timeout: int, token: str | None = None) -> None:
    """Download *url* to *destination* atomically (temp-file + rename)."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = _request_headers(token)
    req = Request(url, headers=headers)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".download",
        dir=str(destination.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)

    try:
        with urlopen(req, timeout=timeout) as response, temp_path.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)

        if temp_path.stat().st_size == 0:
            raise RuntimeError(f"Downloaded empty file from {url}")

        temp_path.replace(destination)   # atomic on POSIX; best-effort on Windows
    except (OSError, URLError, RuntimeError):
        temp_path.unlink(missing_ok=True)
        raise


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _version_url(any_model_url: str) -> str:
    """Derive the version.json URL from any model file URL on the same HF repo."""
    # e.g. .../resolve/main/random_forest.pkl  ->  .../resolve/main/version.json
    parts = any_model_url.rsplit("/", 1)
    return parts[0] + "/" + _VERSION_FILENAME


# ---------------------------------------------------------------------------
# Remote version manifest
# ---------------------------------------------------------------------------

def _fetch_remote_version(settings) -> dict | None:
    """Download version.json from HF and return its parsed content, or None."""
    # Find any model URL to derive the base path
    base_url = None
    for _, (url_attr, _) in MODEL_TARGETS.items():
        url = getattr(settings, url_attr, None)
        if url:
            base_url = url
            break

    if not base_url:
        return None

    version_url = _version_url(base_url)
    try:
        data = _fetch_url_bytes(
            version_url,
            timeout=min(settings.model_download_timeout_seconds, 30),
            token=settings.model_download_token,
        )
        return json.loads(data.decode("utf-8"))
    except Exception as exc:
        logger.debug("Could not fetch remote version.json: %s", exc)
        return None


def _file_needs_update(local_path: Path, remote_manifest: dict | None, filename: str) -> bool:
    """Return True if the local file's SHA-256 differs from the remote manifest entry."""
    if not local_path.exists():
        return True   # missing → definitely needs download
    if remote_manifest is None:
        return False  # no remote manifest → can't compare, keep local
    entry = remote_manifest.get("files", {}).get(filename)
    if not entry:
        return False  # file not in manifest → skip
    remote_sha = entry.get("sha256", "")
    if not remote_sha:
        return False
    local_sha = _sha256_file(local_path)
    return local_sha != remote_sha


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_model_files() -> dict[str, str]:
    """Download and/or update model artefacts from Hugging Face.

    Called once at server startup.  Behaviour:
      - Missing file  → download
      - File exists + SHA-256 matches remote → skip ("up_to_date")
      - File exists + SHA-256 differs from remote → re-download ("updated")
    """
    settings = get_settings()
    if not settings.model_download_enabled:
        return {"status": "disabled"}

    # Fetch the remote version manifest once (one HTTP request)
    remote_version = _fetch_remote_version(settings)
    if remote_version:
        logger.info(
            "Remote model version: trained_at=%s",
            remote_version.get("trained_at", "unknown"),
        )

    results: dict[str, str] = {}

    for name, (url_attr, destination) in MODEL_TARGETS.items():
        url = getattr(settings, url_attr, None)
        if not url:
            results[name] = "no_url"
            continue

        needs = _file_needs_update(destination, remote_version, destination.name)

        if not needs:
            results[name] = "up_to_date"
            continue

        action = "updating" if destination.exists() else "downloading"
        logger.info("%s %s ...", action, destination.name)
        try:
            _download_file(
                url,
                destination,
                settings.model_download_timeout_seconds,
                settings.model_download_token,
            )
            results[name] = "updated" if action == "updating" else "downloaded"
        except Exception as exc:
            logger.error("Failed to %s %s: %s", action, destination.name, exc)
            results[name] = f"failed: {exc}"

    # Also keep local version.json in sync with remote
    if remote_version:
        try:
            _LOCAL_VERSION.parent.mkdir(parents=True, exist_ok=True)
            _LOCAL_VERSION.write_text(
                json.dumps(remote_version, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

    return results


def check_and_update_models() -> dict[str, str]:
    """Re-run the update check without requiring missing files.

    Safe to call periodically (e.g. every 6 hours via APScheduler).
    Returns a dict of {model_name: status}.
    """
    logger.info("Checking for model updates on Hugging Face ...")
    return ensure_model_files()
