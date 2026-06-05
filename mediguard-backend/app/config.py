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
    model_download_enabled: bool = True
    model_random_forest_url: str | None = None
    model_decision_tree_url: str | None = None
    model_naive_bayes_url: str | None = None
    model_label_encoder_url: str | None = None
    model_symptoms_list_url: str | None = None
    model_herbs_remedies_url: str | None = None
    model_download_token: str | None = None
    model_download_timeout_seconds: int = 180
    embedding_model: str = "all-MiniLM-L6-v2"
    frontend_origins: str = "http://localhost:3000,http://localhost:5173,https://mediguard.info"
    frontend_url: str = "https://mediguard.info"
    # SMTP email settings (leave smtp_user/smtp_password empty to disable email)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "MediGuard <support@mediguard.info>"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]

    @property
    def active_database_url(self) -> str:
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
