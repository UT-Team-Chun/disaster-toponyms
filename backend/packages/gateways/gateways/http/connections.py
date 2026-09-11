"""Shared httpx client with a filesystem response cache and per-host throttling."""

from __future__ import annotations

import hashlib
import json
import ssl
import time
import urllib.parse
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from gateways.http.config import HttpConfig

#: Statuses worth retrying. Everything else, notably 404, is a final answer.
_RETRY_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})
_LAST_REQUEST_AT: dict[str, float] = {}

#: Tile services sit behind a CDN and serve static files, so the polite
#: one-request-per-second default would make a nationwide sweep pointlessly slow.
_HOST_INTERVALS: dict[str, float] = {
    "disaportaldata.gsi.go.jp": 0.1,
    "cyberjapandata.gsi.go.jp": 0.1,
}

#: Marker file recording that a URL is known to be absent. Hazard tiles are only
#: published where a hazard exists, so a nationwide sweep hits many 404s and must
#: not ask for the same missing tile twice.
_MISSING_SUFFIX = ".missing"


@lru_cache(maxsize=1)
def get_http_config() -> HttpConfig:
    """Return the cached HTTP configuration."""
    return HttpConfig()


#: Several Japanese government servers still renegotiate TLS the old way, which
#: OpenSSL 3 refuses by default and which surfaces mid-download rather than at
#: the handshake. Allowing it is what makes those downloads reproducible.
_LEGACY_SERVER_CONNECT = 0x4


def _ssl_context() -> ssl.SSLContext:
    """Build the TLS context used for every request."""
    context = ssl.create_default_context()
    context.options |= _LEGACY_SERVER_CONNECT
    return context


@lru_cache(maxsize=1)
def get_http_client() -> httpx.Client:
    """Return a singleton httpx client configured from the environment."""
    config = get_http_config()
    return httpx.Client(
        headers={"User-Agent": config.http_user_agent},
        timeout=config.http_timeout_seconds,
        follow_redirects=True,
        verify=_ssl_context(),
    )


def _throttle(url: str) -> None:
    """Sleep so that requests to a single host stay below the configured rate."""
    config = get_http_config()
    host = urllib.parse.urlsplit(url).netloc
    interval = _HOST_INTERVALS.get(host, config.http_min_interval_seconds)
    previous = _LAST_REQUEST_AT.get(host)
    now = time.monotonic()
    if previous is not None:
        wait = interval - (now - previous)
        if wait > 0:
            time.sleep(wait)
    _LAST_REQUEST_AT[host] = time.monotonic()


def cache_path_for(url: str, params: dict[str, Any] | None, suffix: str) -> Path:
    """Build the deterministic cache file path for a request."""
    config = get_http_config()
    canonical = url
    if params:
        canonical = f"{url}?{urllib.parse.urlencode(sorted(params.items()))}"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    host = urllib.parse.urlsplit(url).netloc or "unknown"
    return config.http_cache_dir / host / f"{digest}{suffix}"


class ResourceMissingError(Exception):
    """The server said the resource does not exist."""

    def __init__(self, url: str, status_code: int) -> None:
        super().__init__(f"{url} returned {status_code}")
        self.url = url
        self.status_code = status_code


def fetch_bytes(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    suffix: str = ".bin",
    force: bool = False,
) -> bytes:
    """Fetch a URL, returning cached bytes when available.

    A response that is permanently unavailable is remembered as such, so a sweep
    over many coordinates does not re-request tiles the service never published.

    Args:
        url: Absolute URL to request.
        params: Optional query parameters.
        suffix: File extension used for the cache entry.
        force: Bypass the cache and refresh the stored response.

    Returns:
        Raw response body.

    Raises:
        ResourceMissingError: If the server reports the resource does not exist.
        httpx.HTTPStatusError: If a retryable error persists.
        httpx.TransportError: If the connection keeps failing.

    """
    path = cache_path_for(url, params, suffix)
    missing_path = path.with_name(path.name + _MISSING_SUFFIX)
    if not force:
        if path.exists():
            return path.read_bytes()
        if missing_path.exists():
            raise ResourceMissingError(url, int(missing_path.read_text(encoding="utf-8")))

    config = get_http_config()
    client = get_http_client()
    last_error: httpx.HTTPStatusError | httpx.TransportError | None = None
    for attempt in range(config.http_max_retries):
        _throttle(url)
        try:
            response = client.get(url, params=params)
        except httpx.TransportError as error:
            last_error = error
            time.sleep(2.0 * (attempt + 1))
            continue

        if response.is_success:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(response.content)
            return response.content

        if response.status_code not in _RETRY_STATUS:
            missing_path.parent.mkdir(parents=True, exist_ok=True)
            missing_path.write_text(str(response.status_code), encoding="utf-8")
            raise ResourceMissingError(url, response.status_code)

        last_error = httpx.HTTPStatusError(
            f"{url} returned {response.status_code}",
            request=response.request,
            response=response,
        )
        time.sleep(2.0 * (attempt + 1))

    if last_error is not None:
        raise last_error
    msg = f"Failed to fetch {url}"
    raise RuntimeError(msg)


def fetch_text(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    suffix: str = ".txt",
    encoding: str = "utf-8",
    force: bool = False,
) -> str:
    """Fetch a URL and decode the body as text."""
    raw = fetch_bytes(url, params=params, suffix=suffix, force=force)
    return raw.decode(encoding, errors="replace")


def fetch_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    force: bool = False,
) -> Any:  # noqa: ANN401
    """Fetch a URL and parse the body as JSON."""
    raw = fetch_bytes(url, params=params, suffix=".json", force=force)
    return json.loads(raw.decode("utf-8"))
