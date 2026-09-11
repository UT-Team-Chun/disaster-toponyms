"""Read plain-text article extracts from Japanese Wikipedia."""

from __future__ import annotations

from typing import Any, Final
from urllib.parse import quote

from gateways.http.connections import fetch_json

API_URL: Final = "https://ja.wikipedia.org/w/api.php"
ARTICLE_BASE: Final = "https://ja.wikipedia.org/wiki/"


def fetch_article_text(title: str, *, force: bool = False) -> str | None:
    """Fetch the plain-text body of a Japanese Wikipedia article.

    Args:
        title: Article title, for example ``災害地名``.
        force: Bypass the HTTP cache.

    Returns:
        The article text, or None when the page does not exist.

    """
    payload: Any = fetch_json(
        API_URL,
        params={
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "redirects": "1",
            "format": "json",
            "formatversion": "2",
            "titles": title,
        },
        force=force,
    )
    if not isinstance(payload, dict):
        return None
    pages = (payload.get("query") or {}).get("pages") or []
    for page in pages:
        if isinstance(page, dict) and not page.get("missing"):
            extract = page.get("extract")
            if isinstance(extract, str) and extract.strip():
                return extract
    return None


def article_url(title: str) -> str:
    """Return the canonical article URL for a title."""
    return ARTICLE_BASE + quote(title.replace(" ", "_"))
