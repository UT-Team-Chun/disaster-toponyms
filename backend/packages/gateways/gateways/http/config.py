"""HTTP gateway configuration."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/packages/gateways/gateways/http/config.py -> repository root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".envrc"


class HttpConfig(BaseSettings):
    """Configuration for outbound HTTP requests and the on-disk response cache."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    http_cache_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "cache" / "http",
        description="Directory holding cached HTTP responses",
    )
    http_user_agent: str = Field(
        default=(
            "disaster-toponyms/0.1 (research; https://github.com/UT-Team-Chun/disaster-toponyms)"
        ),
        description="User-Agent header sent with every request",
    )
    http_timeout_seconds: float = Field(default=60.0, description="Per-request timeout")
    http_min_interval_seconds: float = Field(
        default=1.0,
        description="Minimum delay between two requests to the same host",
    )
    http_max_retries: int = Field(default=3, description="Retry count for transient failures")
