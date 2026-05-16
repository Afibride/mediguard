from pydantic import BaseModel


class TrendData(BaseModel):
    week: str
    disease: str
    count: int


class TopDisease(BaseModel):
    disease: str
    count: int


class HeatmapData(BaseModel):
    region: str
    disease: str
    count: int
