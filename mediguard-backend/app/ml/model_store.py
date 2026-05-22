from __future__ import annotations

import os
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.config import get_settings


MODEL_TARGETS = {
    "random_forest": ("model_random_forest_url", Path("models/random_forest.pkl")),
    "decision_tree": ("model_decision_tree_url", Path("models/decision_tree.pkl")),
    "naive_bayes": ("model_naive_bayes_url", Path("models/naive_bayes.pkl")),
    "label_encoder": ("model_label_encoder_url", Path("models/label_encoder.pkl")),
    "model_symptoms": ("model_symptoms_list_url", Path("models/symptoms_list.json")),
}


def _download_file(url: str, destination: Path, timeout: int, token: str | None = None) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "MediGuard-ModelDownloader/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".download",
        dir=str(destination.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)

    try:
        with urlopen(request, timeout=timeout) as response, temp_path.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)

        if temp_path.stat().st_size == 0:
            raise RuntimeError(f"Downloaded empty model file from {url}")

        temp_path.replace(destination)
    except (OSError, URLError, RuntimeError):
        temp_path.unlink(missing_ok=True)
        raise


def ensure_model_files() -> dict[str, str]:
    """Download configured model artifacts when they are missing locally.

    This keeps GitHub as code-only while letting deployed servers hydrate
    `models/*.pkl` from cloud storage before predictions are served.
    """
    settings = get_settings()
    if not settings.model_download_enabled:
        return {"status": "disabled"}

    results: dict[str, str] = {}
    for name, (url_attr, destination) in MODEL_TARGETS.items():
        url = getattr(settings, url_attr, None)
        if not url:
            results[name] = "no_url"
            continue
        if destination.exists() and destination.stat().st_size > 0:
            results[name] = "exists"
            continue

        try:
            _download_file(
                url,
                destination,
                settings.model_download_timeout_seconds,
                settings.model_download_token,
            )
            results[name] = "downloaded"
        except Exception as exc:
            results[name] = f"failed: {exc}"

    return results
