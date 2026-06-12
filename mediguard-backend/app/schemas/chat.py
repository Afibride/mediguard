from pydantic import BaseModel


class ChatInput(BaseModel):
    query: str
    history: list[dict] = []
    filter_disease: str | None = None
    gender: str | None = None
    is_pregnant: bool = False
    pregnancy_weeks: int | None = None
    user_lat: float | None = None
    user_lng: float | None = None
    child_mode: bool = False   # True when user is asking about a child/infant
    lang: str | None = None    # UI language code, e.g. "en" or "fr"


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    disclaimer: str
