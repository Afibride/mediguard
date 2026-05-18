from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import ChatFeedback, ChatLog, PredictionLog, User
from app.db.session import get_db
from app.schemas.history import ChatFeedbackInput, ChatHistoryCreate
from app.utils.dependencies import get_current_user, optional_user

router = APIRouter()


@router.get("")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(PredictionLog).filter(PredictionLog.user_id == user.id).order_by(PredictionLog.timestamp.desc()).all()
    return [
        {
            "id": row.id,
            "symptoms": row.symptoms,
            "predictions": row.predictions,
            "results": row.predictions,
            "top_disease": row.top_disease,
            "created_at": row.timestamp.isoformat(),
        }
        for row in rows
    ]


@router.delete("/{history_id}")
def delete_history(history_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(PredictionLog).filter(PredictionLog.id == history_id, PredictionLog.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="History item not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}


@router.get("/chats")
def chat_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(ChatLog).filter(ChatLog.user_id == user.id).order_by(ChatLog.created_at.desc()).all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "message": row.message,
            "response": row.response,
            "sources": row.sources or [],
            "follow_up_questions": row.follow_up_questions or [],
            "mode": row.mode,
            "pregnancy_context": row.pregnancy_context,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


@router.post("/chats")
def save_chat_history(body: ChatHistoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = ChatLog(
        user_id=user.id,
        title=(body.title or body.message[:48] or "MediGuard AI Chat"),
        message=body.message,
        response=body.response,
        sources=body.sources,
        follow_up_questions=body.follow_up_questions,
        mode=body.mode,
        pregnancy_context=body.pregnancy_context,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "id": row.id,
        "title": row.title,
        "message": row.message,
        "response": row.response,
        "sources": row.sources or [],
        "follow_up_questions": row.follow_up_questions or [],
        "mode": row.mode,
        "pregnancy_context": row.pregnancy_context,
        "created_at": row.created_at.isoformat(),
    }


@router.delete("/chats/{chat_id}")
def delete_chat_history(chat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.query(ChatLog).filter(ChatLog.id == chat_id, ChatLog.user_id == user.id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Chat history item not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}


@router.post("/chats/feedback")
def submit_chat_feedback(
    body: ChatFeedbackInput,
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_user),
):
    row = ChatFeedback(
        session_id=body.session_id,
        user_id=user.id if user else None,
        query=body.query,
        response_preview=body.response_preview,
        rating=body.rating,
        query_keywords=body.query_keywords,
        mode=body.mode,
    )
    db.add(row)
    db.commit()
    return {"ok": True}
