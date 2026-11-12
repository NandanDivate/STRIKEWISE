"""Application configuration using pydantic-settings.

Loads settings from environment variables and .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    APP_NAME: str = Field(default="NIFTY Options Pricing API")
    VERSION: str = Field(default="0.1.0")
    DEBUG: bool = Field(default=False)
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    RISK_FREE_RATE_DEFAULT: float = Field(default=7.0)
    DIVIDEND_YIELD_DEFAULT: float = Field(default=1.2)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


settings = Settings()

