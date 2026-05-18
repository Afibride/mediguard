import json
import pickle
from pathlib import Path

try:
    import joblib
except ImportError:
    joblib = None

from app.config import get_settings
from app.data import DISEASES, SYMPTOMS
from app.ml.simple_model import SimpleLabelEncoder, SimpleSymptomModel  # noqa: F401 — needed for pickle resolution


class DiseasePredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.symptoms = self._load_symptoms()
        self.model = self._load_model()
        # Lazily initialised on first Pinecone call
        self._pinecone_idx = None
        self._embedder = None
        self._pinecone_loaded = False  # True once we've tried (even if failed)

    # -------------------------------------------------------------------------
    # Initialisation helpers
    # -------------------------------------------------------------------------

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
            try:
                with path.open("rb") as handle:
                    return pickle.load(handle)
            except Exception:
                pass
        return None

    def _try_init_pinecone(self) -> bool:
        """Try to connect to Pinecone and load the sentence-transformer embedder.
        Returns True if both are ready."""
        if self._pinecone_loaded:
            return self._pinecone_idx is not None and self._embedder is not None

        self._pinecone_loaded = True  # only attempt once per process

        api_key = self.settings.pinecone_api_key
        if not api_key:
            return False

        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            index_name = self.settings.pinecone_index
            info = pc.describe_index(index_name)
            self._pinecone_dim = getattr(info, "dimension", None) or 384
            self._pinecone_idx = pc.Index(index_name)
        except Exception:
            self._pinecone_idx = None
            return False

        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.settings.embedding_model)
            self._use_st = True
        except Exception:
            # Fall back to hash-based embedder — must use the index's actual dimension
            self._use_st = False

        return self._pinecone_idx is not None

    def _embed(self, text: str) -> list[float]:
        if getattr(self, "_use_st", False) and self._embedder is not None:
            result = self._embedder.encode(text, normalize_embeddings=True)
            return result.tolist() if hasattr(result, "tolist") else list(result)
        # Hash-based fallback with the correct index dimension
        from app.rag.embeddings import embed_text
        return embed_text(text, dim=getattr(self, "_pinecone_dim", 384))

    # -------------------------------------------------------------------------
    # Pinecone semantic prediction
    # -------------------------------------------------------------------------

    def _predict_pinecone(self, symptoms: list[str]) -> list[dict] | None:
        """Query disease_profile vectors in Pinecone and return ranked predictions.
        Returns None if Pinecone is not configured or has no disease profiles."""
        if not self._try_init_pinecone():
            return None

        query_text = "Symptoms present: " + ", ".join(symptoms)
        query_vec = self._embed(query_text)

        try:
            results = self._pinecone_idx.query(
                vector=query_vec,
                top_k=5,
                include_metadata=True,
                filter={"data_type": {"$eq": "disease_profile"}},
            )
        except Exception:
            return None

        matches = results.matches if hasattr(results, "matches") else results.get("matches", [])
        if not matches:
            return None

        by_name = {d["name"]: d for d in DISEASES}
        out = []
        for match in matches:
            meta = match.metadata if hasattr(match, "metadata") else match.get("metadata", {})
            disease_name = meta.get("disease", "")
            score_raw = match.score if hasattr(match, "score") else match.get("score", 0)
            # Cosine similarity is in [-1, 1]; map to [0, 100]
            probability = round(max(0.0, float(score_raw)) * 100, 2)

            disease = by_name.get(disease_name, {})
            out.append({
                "id": disease.get("id", disease_name.lower().replace(" ", "-")),
                "slug": disease.get("slug", disease_name.lower().replace(" ", "-")),
                "disease": disease_name,
                "name": disease_name,
                "probability": probability,
                "confidence": probability,
                "category": disease.get("category", meta.get("category", "General")),
                "severity": disease.get("severity", meta.get("severity", "Medium")),
                "description": disease.get("description", "Disease information is available in the library."),
                "symptoms": disease.get("symptoms", meta.get("symptoms", [])),
                "matchCount": sum(1 for s in symptoms if s in disease.get("symptoms", [])),
                "data_source": "pinecone",
            })
        return out

    # -------------------------------------------------------------------------
    # Local Naive-Bayes model prediction
    # -------------------------------------------------------------------------

    def _predict_local_model(self, symptoms: list[str]) -> list[dict] | None:
        if not (self.model and hasattr(self.model, "predict_ranked")):
            return None
        by_name = {d["name"]: d for d in DISEASES}
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
                "data_source": "local_model",
            })
        return results or None

    # -------------------------------------------------------------------------
    # Rule-based fallback
    # -------------------------------------------------------------------------

    def _predict_rule_based(self, symptoms: list[str]) -> list[dict]:
        selected = {s.strip().lower() for s in symptoms}
        ranked = []
        for disease in DISEASES:
            disease_symptoms = {s.lower() for s in disease["symptoms"]}
            matches = selected & disease_symptoms
            if not matches:
                continue
            probability = min(98, round(
                (len(matches) / max(len(selected), 1)) * 72
                + (len(matches) / len(disease_symptoms)) * 26
            ))
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
                "data_source": "rule_based",
            })
        return sorted(ranked, key=lambda x: x["probability"], reverse=True)[:5]

    # -------------------------------------------------------------------------
    # Public predict — chooses the most accurate available engine
    # -------------------------------------------------------------------------

    def predict(self, symptoms: list[str]) -> list[dict]:
        # When sentence-transformers is available, Pinecone semantic search
        # understands symptom meaning better.  When only the hash-based embedder
        # is available the local trained model is more reliable (93 % accuracy).
        use_pinecone_first = self._try_init_pinecone() and getattr(self, "_use_st", False)

        if use_pinecone_first:
            result = self._predict_pinecone(symptoms)
            if result:
                return result

        # Trained Naive-Bayes model (consistent 93 % accuracy)
        model_result = self._predict_local_model(symptoms)
        if model_result is not None:
            return model_result

        # Pinecone as secondary fallback (hash-based) when sentence-transformers absent
        if not use_pinecone_first:
            pinecone_result = self._predict_pinecone(symptoms)
            if pinecone_result:
                return pinecone_result

        # Deterministic rule-based overlap scoring (always available)
        return self._predict_rule_based(symptoms)
