from pydantic import BaseModel


class ChatInput(BaseModel):
    query: str
    history: list[dict] = []
    filter_disease: str | None = None
    gender: str | None = None
    is_pregnant: bool = False
    pregnancy_weeks: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    disclaimer: str
