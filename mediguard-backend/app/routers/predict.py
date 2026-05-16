from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import PredictionLog
from app.db.session import get_db
from app.ml.predictor import DiseasePredictor
from app.schemas.predict import SymptomInput
from app.utils.dependencies import optional_user

router = APIRouter()
predictor = DiseasePredictor()


@router.get("/symptoms")
def list_symptoms():
    return {"symptoms": predictor.symptoms}


@router.post("/predict")
def predict(body: SymptomInput, db: Session = Depends(get_db), user=Depends(optional_user)):
    results = predictor.predict(body.symptoms)
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
