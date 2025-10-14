# api/core/config.py
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-secret-key-here"
    )  # Generate with: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RAG API"


settings = Settings()
