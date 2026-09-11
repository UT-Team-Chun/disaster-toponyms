"""Filesystem layout for the toponym dataset build."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# alg/core/toponyms/tools/paths.py -> repository root
REPO_ROOT = Path(__file__).parents[7]
ENV_FILE = REPO_ROOT / ".envrc"


class ToponymPaths(BaseSettings):
    """Directories used by the dataset build."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    repo_root: Path = REPO_ROOT

    @property
    def data_dir(self) -> Path:
        """Root of all dataset files."""
        return self.repo_root / "data"

    @property
    def raw_dir(self) -> Path:
        """Downloaded third-party datasets (not committed)."""
        return self.data_dir / "raw"

    @property
    def curated_dir(self) -> Path:
        """Hand-maintained YAML seeds (committed)."""
        return self.data_dir / "curated"

    @property
    def build_dir(self) -> Path:
        """Intermediate build artefacts (not committed)."""
        return self.data_dir / "build"

    @property
    def cache_dir(self) -> Path:
        """HTTP and LLM caches (not committed)."""
        return self.data_dir / "cache"

    @property
    def output_dir(self) -> Path:
        """Static files served by the frontend (committed)."""
        return self.repo_root / "frontend" / "public" / "data"

    @property
    def geolonia_csv(self) -> Path:
        """Nationwide address table with representative coordinates."""
        return self.raw_dir / "geolonia" / "latest.csv"

    @property
    def local_history_dir(self) -> Path:
        """Extracted text of municipal place-name studies."""
        return self.raw_dir / "local_history"

    @property
    def monument_dir(self) -> Path:
        """Extracted GSI natural disaster monument dataset."""
        return self.raw_dir / "gsi"

    @property
    def boundary_dir(self) -> Path:
        """Census small-area boundary shapefiles, one directory per prefecture."""
        return self.raw_dir / "estat_boundaries"


@lru_cache(maxsize=1)
def get_paths() -> ToponymPaths:
    """Return the cached path configuration."""
    return ToponymPaths()
