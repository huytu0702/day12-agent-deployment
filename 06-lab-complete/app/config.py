"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv(value: str | None, default: str = "*") -> list[str]:
    raw = value if value is not None else default
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = _parse_bool(os.getenv("DEBUG"), default=False)
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()

    app_name: str = os.getenv("APP_NAME", "Day12 Production Agent")
    app_version: str = os.getenv("APP_VERSION", "2.0.0")
    llm_model: str = os.getenv("LLM_MODEL", "mock-gpt-4o-mini")

    redis_url: str = os.getenv("REDIS_URL", "")
    agent_api_key: str = os.getenv("AGENT_API_KEY", "")
    allowed_origins: list[str] = field(
        default_factory=lambda: _parse_csv(os.getenv("ALLOWED_ORIGINS"), default="*")
    )

    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    monthly_budget_usd: float = float(os.getenv("MONTHLY_BUDGET_USD", "10.0"))
    history_limit: int = int(os.getenv("HISTORY_LIMIT", "20"))
    conversation_ttl_seconds: int = int(os.getenv("CONVERSATION_TTL_SECONDS", "604800"))

    def validate(self) -> "Settings":
        if not self.redis_url:
            raise ValueError("REDIS_URL is required.")
        if not self.agent_api_key:
            raise ValueError("AGENT_API_KEY is required.")
        if self.rate_limit_per_minute <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be greater than 0.")
        if self.monthly_budget_usd <= 0:
            raise ValueError("MONTHLY_BUDGET_USD must be greater than 0.")
        if self.history_limit <= 0:
            raise ValueError("HISTORY_LIMIT must be greater than 0.")
        return self


settings = Settings().validate()
