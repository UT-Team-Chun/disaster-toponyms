"""Algorithm configuration models loaded from environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define backend root directory (backend/)
BACKEND_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = BACKEND_ROOT.parent / ".envrc"


class AlgConfig(BaseSettings):
    """Algorithm configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Data Path
    input_data: str = Field(default="data/input", description="Input data directory path")
    output_data: str = Field(default="data/output", description="Output data directory path")
    model_cache: str = Field(default="data/cache", description="Model cache directory path")

    # Embedding
    embedding_dimensions: int = Field(default=768, description="Embedding dimensions")
    embedding_batch_size: int = Field(default=32, description="Batch size for embedding")

    # Processing
    chunk_size: int = Field(default=1000, description="Text chunk size")
    chunk_overlap: int = Field(default=200, description="Text chunk overlap")
    max_concurrency: int = Field(default=10, description="Maximum concurrent tasks")
