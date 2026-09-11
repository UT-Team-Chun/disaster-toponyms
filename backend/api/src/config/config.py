"""Backend application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define backend root directory (backend/)
BACKEND_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = BACKEND_ROOT.parent / ".envrc"


class BackendConfig(BaseSettings):
    """Backend application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App settings
    app_name: str = Field(default="FastAPI Backend", description="Application name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")  # noqa: S104
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of workers")

    # CORS settings
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Allowed CORS origins (comma-separated)",
    )

    # License file path
    licenses_txt_path: Path = Field(
        default=BACKEND_ROOT / "ThirdPartyNotices.txt",
        description="Path to ThirdPartyNotices.txt",
    )


@lru_cache
def get_backend_config() -> BackendConfig:
    """Get the backend configuration instance (cached).

    Returns:
        BackendConfig: Backend configuration object

    """
    return BackendConfig()
