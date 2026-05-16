from datetime import datetime

from pydantic import BaseModel


class HistoryItem(BaseModel):
    id: int
    symptoms: list[str]
    predictions: list[dict]
    top_disease: str | None = None
    created_at: datetime | str


class HistoryList(BaseModel):
    items: list[HistoryItem]


class ChatHistoryCreate(BaseModel):
    title: str | None = None
    message: str
    response: str
    sources: list[str] = []
    follow_up_questions: list[str] = []
    mode: str | None = None
    pregnancy_context: bool = False


class ChatHistoryItem(ChatHistoryCreate):
    id: int
    created_at: datetime | str
