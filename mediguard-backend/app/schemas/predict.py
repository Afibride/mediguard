from pydantic import BaseModel, Field


class SymptomInput(BaseModel):
    symptoms: list[str] = Field(min_length=1)
    gender: str | None = None
    is_pregnant: bool = False
    pregnancy_weeks: int | None = None


class PredictionResponse(BaseModel):
    predictions: list[dict]
    disclaimer: str
