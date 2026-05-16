from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import PredictionLog
from app.db.models import Disease
from app.db.session import get_db
from app.ml.predictor import DiseasePredictor
from app.schemas.predict import SymptomInput
from app.utils.dependencies import optional_user

router = APIRouter()
predictor = DiseasePredictor()


def enrich_predictions_from_database(results: list[dict], db: Session) -> list[dict]:
    rows = db.query(Disease).all()
    by_name = {row.name.lower(): row for row in rows}
    by_slug = {row.slug.lower(): row for row in rows}
    enriched = []
    for item in results:
        key = (item.get("disease") or item.get("name") or "").lower()
        slug = (item.get("slug") or "").lower()
        disease = by_name.get(key) or by_slug.get(slug)
        if disease:
            item = {
                **item,
                "id": disease.slug,
                "slug": disease.slug,
                "name": disease.name,
                "disease": disease.name,
                "category": disease.category,
                "severity": disease.severity,
                "description": disease.description,
                "symptoms": disease.symptoms or item.get("symptoms", []),
                "database_source": "diseases",
            }
        enriched.append(item)
    return enriched


@router.get("/symptoms")
def list_symptoms():
    return {"symptoms": predictor.symptoms}


@router.post("/predict")
def predict(body: SymptomInput, db: Session = Depends(get_db), user=Depends(optional_user)):
    results = enrich_predictions_from_database(predictor.predict(body.symptoms), db)
    pregnancy_note = None
    if body.is_pregnant:
        pregnancy_note = (
            "Pregnancy can change how symptoms should be assessed. Seek prompt antenatal or clinical care for "
            "vaginal bleeding, severe abdominal pain, severe headache, vision changes, swelling of face or hands, "
            "fever, reduced fetal movement, fainting, chest pain, or shortness of breath."
        )
        for item in results:
            item["pregnancy_context"] = True
            if item.get("disease") in {"Malaria", "Hypertension", "Iron Deficiency Anemia", "Cystitis UTI"}:
                item["pregnancy_warning"] = "This condition can be more important during pregnancy. Please seek clinical assessment promptly."
    top = results[0]["disease"] if results else "Unknown"
    db.add(PredictionLog(
        user_id=user.id if user else None,
        symptoms=body.symptoms,
        predictions=results,
        top_disease=top,
    ))
    db.commit()
    return {
        "predictions": results,
        "pregnancy_note": pregnancy_note,
        "disclaimer": "MediGuard is not a medical diagnosis. Consult a qualified health professional.",
    }
