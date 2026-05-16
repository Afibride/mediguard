from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.models import Disease
from app.db.session import get_db

router = APIRouter()


def serialize_disease(disease: Disease) -> dict:
    return {
        "id": disease.slug,
        "slug": disease.slug,
        "name": disease.name,
        "disease": disease.name,
        "category": disease.category,
        "featured": disease.featured,
        "severity": disease.severity,
        "symptoms": disease.symptoms or [],
        "description": disease.description,
        "causes": disease.causes,
        "treatment": disease.treatment,
        "prevention": disease.prevention or [],
        "sections": disease.sections or {},
    }


@router.get("")
def list_diseases(
    search: str | None = None,
    category: str | None = None,
    featured: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Disease)
    if featured is not None:
        query = query.filter(Disease.featured == featured)
    rows = [serialize_disease(row) for row in query.order_by(Disease.name.asc()).all()]
    if search:
        needle = search.lower()
        rows = [d for d in rows if needle in d["name"].lower() or needle in d["description"].lower() or any(needle in s.lower() for s in d["symptoms"])]
    if category and category.lower() != "all":
        rows = [d for d in rows if d["category"].lower() == category.lower()]
    return rows


@router.get("/{slug}")
def disease_detail(slug: str, db: Session = Depends(get_db)):
    disease = db.query(Disease).filter(Disease.slug == slug).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    return serialize_disease(disease)
