"""Configuration settings for BOB Backend."""

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Settings:
    """Application configuration and credentials loaded from environment."""

    # Internal API Secret for microservice-to-microservice authentication
    INTERNAL_API_SECRET: str = field(
        default_factory=lambda: (
            os.getenv("INTERNAL_API_SECRET")
            or os.getenv("BOB_INTERNAL_SECRET")
            or "bob_secret_key_alcy_legacy_2026"
        )
    )

    # IBM watsonx.ai configuration
    WATSONX_APIKEY: str = field(
        default_factory=lambda: (
            os.getenv("BOB_API_KEY")
            or os.getenv("IBM_API_KEY")
            or os.getenv("WATSONX_APIKEY")
            or os.getenv("IBM_CLOUD_API_KEY")
            or ""
        )
    )
    WATSONX_PROJECT_ID: str = field(
        default_factory=lambda: (
            os.getenv("WATSONX_PROJECT_ID")
            or os.getenv("BOB_PROJECT_ID")
            or ""
        )
    )
    WATSONX_URL: str = field(
        default_factory=lambda: os.getenv("WATSONX_URL") or "https://us-south.ml.cloud.ibm.com"
    )
    WATSONX_MODEL_ID: str = field(
        default_factory=lambda: os.getenv("WATSONX_MODEL_ID") or "ibm/granite-3-8b-instruct"
    )
    BOB_MOCK_WATSONX: bool = field(
        default_factory=lambda: os.getenv("BOB_MOCK_WATSONX", "false").lower() in ("true", "1", "yes")
    )

    # Environment
    ENVIRONMENT: str = field(default_factory=lambda: os.getenv("ENVIRONMENT") or "development")
    SERVICE_NAME: str = "bob-backend"
    SERVICE_VERSION: str = "1.0.0"


@lru_cache
def _cached_settings() -> Settings:
    return Settings()


def get_settings(reload: bool = False) -> Settings:
    """Return Settings instance, optionally clearing cache."""
    if reload:
        _cached_settings.cache_clear()
    return _cached_settings()


get_settings.cache_clear = _cached_settings.cache_clear
