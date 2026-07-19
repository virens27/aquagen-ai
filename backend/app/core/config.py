"""
Centralized app configuration.
Reads from environment variables / .env file via pydantic-settings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    database_url: str  # postgresql+psycopg://postgres:<password>@<host>:5432/postgres

    # --- App ---
    app_env: str = "development"          # development | production
    debug: bool = True

    # --- LLM (Groq / future LangChain layer) ---
    groq_api_key: str | None = None

    # --- CORS ---
    frontend_origin: str = "http://localhost:5173"  # Vite dev server; update for Vercel URL later


@lru_cache
def get_settings() -> Settings:
    """Cached so .env is only parsed once per process."""
    return Settings()
