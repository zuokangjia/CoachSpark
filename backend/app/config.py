from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite:///./coachspark.db"
    openai_api_key: str
    embedding_api_key: str
    openai_model: str
    openai_base_url: str
    embedding_model: str
    embedding_base_url: str
    llm_timeout_seconds: int = 45
    llm_max_retries: int = 1
    app_env: str = "development"
    cors_origins: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
