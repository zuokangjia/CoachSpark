from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite:///./coachspark.db"
    openai_api_key: str
    openai_model: str = "google/gemini-2.5-flash"
    openai_base_url: str = "https://openrouter.ai/api/v1"
    app_env: str = "development"
    cors_origins: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
