from pydantic import BaseModel


class DiseaseListItem(BaseModel):
    id: str
    slug: str
    name: str
    category: str
    featured: bool = False
    severity: str
    symptoms: list[str]
    description: str


class DiseaseDetail(DiseaseListItem):
    causes: str | None = None
    treatment: str | None = None
    prevention: list[str] = []
    sections: dict = {}

