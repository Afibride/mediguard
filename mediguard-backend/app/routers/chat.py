from fastapi import APIRouter

from app.rag.retriever import generate_answer
from app.schemas.chat import ChatInput

router = APIRouter()


@router.post("/chat")
def chat(body: ChatInput):
    return generate_answer(
        body.query,
        body.filter_disease,
        body.history,
        gender=body.gender,
        is_pregnant=body.is_pregnant,
        pregnancy_weeks=body.pregnancy_weeks,
    )
