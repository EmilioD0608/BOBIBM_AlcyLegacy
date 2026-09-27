
import os
import warnings
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


_ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE)


def _resolve_internal_secret() -> str:
    """Resolve the internal API secret from environment.

    In production, raises RuntimeError if no secret is set.
    In development, falls back to an insecure dev-only value with a warning.
    """
    secret = os.getenv("INTERNAL_API_SECRET") or os.getenv(
        "BOB_INTERNAL_SECRET"
    )

    if secret:
        return secret

    env = os.getenv("ENVIRONMENT", "development").lower()

    if env == "production":
        raise RuntimeError(
            "INTERNAL_API_SECRET environment variable is required in production. "
            "Set it before starting the service."
        )

    # Development-only fallback — NOT safe for production
    warnings.warn(
        "INTERNAL_API_SECRET not set. Using insecure dev-only default. "
        "DO NOT use in production.",
        stacklevel=2,
    )

    return "dev_only_secret_do_not_use_in_prod"


@dataclass
class Settings:
    """Application configuration and credentials loaded from environment."""

    # -----------------------------------------------------------------------
    # Internal API Secret
    # -----------------------------------------------------------------------
    INTERNAL_API_SECRET: str = field(
        default_factory=_resolve_internal_secret
    )

    # -----------------------------------------------------------------------
    # IBM watsonx.ai configuration
    # -----------------------------------------------------------------------
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
        default_factory=lambda: (
            os.getenv("WATSONX_URL")
            or "https://us-south.ml.cloud.ibm.com"
        )
    )

    WATSONX_MODEL_ID: str = field(
        default_factory=lambda: (
            os.getenv("WATSONX_MODEL_ID")
            or "ibm/granite-3-8b-instruct"
        )
    )

    BOB_MOCK_WATSONX: bool = field(
        default_factory=lambda: (
            os.getenv("BOB_MOCK_WATSONX", "false").lower()
            in ("true", "1", "yes")
        )
    )


    GROQ_API_KEY: str = field(
        default_factory=lambda: os.getenv("GROQ_API_KEY") or ""
    )

    GROQ_MODEL_ID: str = field(
        default_factory=lambda: (
            os.getenv("GROQ_MODEL_ID")
            or "qwen/qwen3.8-27b"
        )
    )


    ENVIRONMENT: str = field(
        default_factory=lambda: (
            os.getenv("ENVIRONMENT")
            or "development"
        )
    )

    SERVICE_NAME: str = "bob-backend"
    SERVICE_VERSION: str = "1.0.0"


@lru_cache
def _cached_settings() -> Settings:
    """Create and cache application settings."""
    return Settings()


def get_settings(reload: bool = False) -> Settings:
    """Return Settings instance, optionally clearing cache."""
    if reload:
        _cached_settings.cache_clear()

    return _cached_settings()



get_settings.cache_clear = _cached_settings.cache_clear