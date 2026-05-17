from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mediguard.db"
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 1440
    pinecone_api_key: str | None = None
    pinecone_index: str = "mediguard-health-knowledge"
    openai_api_key: str | None = None
    model_path: str = "models/random_forest.pkl"
    symptoms_list: str = "data_pipeline/symptoms_list.json"
    embedding_model: str = "all-MiniLM-L6-v2"
    frontend_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def active_database_url(self) -> str:
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
