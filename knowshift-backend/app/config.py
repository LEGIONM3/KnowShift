"""
KnowShift Backend — Application Configuration
Uses Pydantic BaseSettings to load environment variables from .env
and provide typed, centralised access across the entire service layer.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """All configurable values for KnowShift backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # -------------------------------------------------------------------------
    # Supabase
    # -------------------------------------------------------------------------
    supabase_url: str
    supabase_key: str

    # -------------------------------------------------------------------------
    # Google Gemini
    # -------------------------------------------------------------------------
    gemini_api_key: str

    # -------------------------------------------------------------------------
    # Redis / Celery
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379"

    # -------------------------------------------------------------------------
    # App meta
    # -------------------------------------------------------------------------
    environment: str = "development"

    # -------------------------------------------------------------------------
    # Domain validity horizons (days before a document is considered stale)
    # -------------------------------------------------------------------------
    medical_validity_days: int = 180      # Medical knowledge changes frequently
    finance_validity_days: int = 90       # Financial regulations are very fast-moving
    ai_policy_validity_days: int = 365    # AI policy evolves at a slower pace

    def get_validity_days(self, domain: str) -> int:
        """Return the validity horizon for the given domain.

        Falls back to 365 days for unrecognised domains.
        """
        mapping = {
            "medical": self.medical_validity_days,
            "finance": self.finance_validity_days,
            "ai_policy": self.ai_policy_validity_days,
        }
        return mapping.get(domain, 365)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Convenient module-level alias used throughout the codebase:
#   from app.config import settings
settings: Settings = get_settings()
