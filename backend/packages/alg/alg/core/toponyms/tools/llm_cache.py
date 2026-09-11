"""Cache structured LLM extractions on disk so rebuilds need no API key."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from alg.core.toponyms.tools.paths import get_paths


def cache_key(*parts: str) -> str:
    """Build a stable cache key from the prompt and the input text."""
    digest = hashlib.sha256(" ".join(parts).encode("utf-8")).hexdigest()
    return digest[:24]


def cache_path(key: str) -> Path:
    """Return the file that stores one cached extraction."""
    return get_paths().cache_dir / "llm" / f"{key}.json"


def load(key: str) -> dict[str, Any] | None:
    """Read a cached extraction, or None when it has not been computed."""
    path = cache_path(key)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def store(key: str, payload: dict[str, Any]) -> None:
    """Write an extraction to the cache."""
    path = cache_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )
