from pydantic import BaseModel, Field


class SymptomInput(BaseModel):
    symptoms: list[str] = Field(min_length=1)
    gender: str | None = None
    age_group: str | None = None   # e.g. "0-10", "11-20", "21-30", "31-40", "41-50", "51-60", "60+"
    is_pregnant: bool = False
    pregnancy_weeks: int | None = None
    fatigue_context: bool = False
    lang: str | None = None   # UI language code, e.g. "en" or "fr"


class FeedbackInput(BaseModel):
    prediction_log_id: int | None = None
    top_predicted: str
    was_helpful: bool
    confirmed_disease: str | None = None
    comment: str | None = None


class PredictionResponse(BaseModel):
    predictions: list[dict]
    disclaimer: str


class NormalizeInput(BaseModel):
    """Free-text symptom description to normalize into canonical names."""
    text: str = Field(min_length=1, max_length=500)


class NormalizeResponse(BaseModel):
    matched: list[str]
    original: str


class ClarifyInput(BaseModel):
    """Request for follow-up clarification questions."""
    current_symptoms: list[str]
    top_diseases: list[str] = Field(default_factory=list)
    already_asked: list[str] = Field(default_factory=list)
    lang: str | None = None   # UI language code, e.g. "en" or "fr"


class ClarifyQuestion(BaseModel):
    symptom: str
    question: str
    helps_distinguish: list[str]


class ClarifyResponse(BaseModel):
    questions: list[ClarifyQuestion]
    should_ask: bool
