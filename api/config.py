"""
Phase 4: API Layer & Auth — Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT
    secret_key: str = "dev-secret-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # LLM (re-use from phase 3.5)
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Embedding
    embedding_model: str = "BAAI/bge-m3"

    # App
    app_name: str = "RAG API (PoC)"
    debug: bool = True

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
