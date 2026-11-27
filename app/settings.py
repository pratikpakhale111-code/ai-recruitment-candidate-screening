from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Recruitment & Candidate Screening System"
    environment: str = "development"
    database_url: str = "sqlite:///./recruitment.db"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "groq"
    llm_api_key: str = ""
    llm_model: str = "openai/gpt-oss-120b"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
