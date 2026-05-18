from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import ContactMessage
from app.db.session import get_db
from app.schemas.contact import ContactRequest

router = APIRouter()


@router.post("")
def send_contact(body: ContactRequest, db: Session = Depends(get_db)):
    message = ContactMessage(**body.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return {"message": "Message received", "id": message.id}

