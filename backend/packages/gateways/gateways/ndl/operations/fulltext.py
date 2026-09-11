"""Read the full text of public-domain books from the NDL digital collections.

The 次世代デジタルライブラリー publishes the OCR of every out-of-copyright book
as JSON, one entry per scanned frame, with the bounding box of each recognised
block. That is enough to rebuild the vertical columns of a Meiji-era gazetteer
and to cite a claim by the frame a reader can open.
"""

from __future__ import annotations

import json
from typing import Any, Final

from gateways.http.connections import fetch_bytes
from gateways.ndl.models.page import NdlPage, TextBlock

FULLTEXT_URL: Final = "https://lab.ndl.go.jp/dl/api/book/fulltext-json/{pid}"
BOOK_SEARCH_URL: Final = "https://lab.ndl.go.jp/dl/api/book/search"


def _blocks_from(raw: Any) -> list[TextBlock]:  # noqa: ANN401
    """Build the block list from the coordinate payload of one frame."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    blocks: list[TextBlock] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        text = str(item.get("contenttext") or "")
        if not text:
            continue
        try:
            xmin = float(item["xmin"])
            ymin = float(item["ymin"])
            xmax = float(item["xmax"])
            ymax = float(item["ymax"])
        except (KeyError, TypeError, ValueError):
            continue
        blocks.append(
            TextBlock(text=text, x=xmin, y=ymin, width=xmax - xmin, height=ymax - ymin),
        )
    return blocks


def fetch_book_pages(pid: str, *, force: bool = False) -> list[NdlPage]:
    """Fetch every frame of one book.

    Args:
        pid: Persistent identifier of the book, for example ``2937057``.
        force: Bypass the response cache.

    Returns:
        The frames in printed order.

    """
    raw = fetch_bytes(FULLTEXT_URL.format(pid=pid), suffix=".json", force=force)
    payload = json.loads(raw.decode("utf-8"))
    entries = payload.get("list", []) if isinstance(payload, dict) else payload
    pages: list[NdlPage] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        pages.append(
            NdlPage(
                pid=pid,
                frame=int(entry.get("page") or 0),
                contents=str(entry.get("contents") or ""),
                blocks=_blocks_from(entry.get("coordjson")),
            ),
        )
    return pages
