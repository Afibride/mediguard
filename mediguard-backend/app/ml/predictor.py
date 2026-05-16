import json
import pickle
from pathlib import Path

try:
    import joblib
except ImportError:  # Allows the API to run before full ML dependencies are installed.
    joblib = None

from app.config import get_settings
from app.data import DISEASES, SYMPTOMS


class DiseasePredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.symptoms = self._load_symptoms()
        self.model = self._load_model()

    def _load_symptoms(self) -> list[str]:
        path = Path(self.settings.symptoms_list)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return SYMPTOMS

    def _load_model(self):
        path = Path(self.settings.model_path)
        if path.exists() and joblib:
            try:
                return joblib.load(path)
            except Exception:
                pass
        if path.exists():
            with path.open("rb") as handle:
                return pickle.load(handle)
        return None

    def predict(self, symptoms: list[str]) -> list[dict]:
        if self.model and hasattr(self.model, "predict_ranked"):
            by_name = {disease["name"]: disease for disease in DISEASES}
            results = []
            for item in self.model.predict_ranked(symptoms, top_k=5):
                disease = by_name.get(item["disease"], {})
                probability = round(float(item["probability"]), 2)
                results.append({
                    "id": disease.get("id", item["disease"].lower().replace(" ", "-")),
                    "slug": disease.get("slug", item["disease"].lower().replace(" ", "-")),
                    "disease": item["disease"],
                    "name": item["disease"],
                    "probability": probability,
                    "confidence": probability,
                    "category": disease.get("category", "General"),
                    "severity": disease.get("severity", "Medium"),
                    "description": disease.get("description", "Disease information is available in the library."),
                    "symptoms": disease.get("symptoms", item.get("matched_symptoms", [])),
                    "matchCount": len(item.get("matched_symptoms", [])),
                })
            return results

        selected = {s.strip().lower() for s in symptoms}
        ranked = []
        for disease in DISEASES:
            disease_symptoms = {s.lower() for s in disease["symptoms"]}
            matches = selected & disease_symptoms
            if not matches:
                continue
            probability = min(98, round((len(matches) / max(len(selected), 1)) * 72 + (len(matches) / len(disease_symptoms)) * 26))
            ranked.append({
                "id": disease["id"],
                "slug": disease["slug"],
                "disease": disease["name"],
                "name": disease["name"],
                "probability": probability,
                "confidence": probability,
                "category": disease["category"],
                "severity": disease["severity"],
                "description": disease["description"],
                "symptoms": disease["symptoms"],
                "matchCount": len(matches),
            })
        return sorted(ranked, key=lambda item: item["probability"], reverse=True)[:5]
