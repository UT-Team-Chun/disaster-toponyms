"""Convert public web pages into plain text for evidence extraction."""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from typing import ClassVar

from gateways.http.connections import fetch_bytes

_WHITESPACE = re.compile(r"[ \t　]+")
_BLANK_LINES = re.compile(r"\n{3,}")
_CHARSET = re.compile(rb'charset=["\']?([\w\-]+)', re.IGNORECASE)


class _TextExtractor(HTMLParser):
    """Collect visible text, dropping script, style and navigation noise."""

    SKIP_TAGS: ClassVar[frozenset[str]] = frozenset(
        {"script", "style", "noscript", "svg", "head"},
    )
    BLOCK_TAGS: ClassVar[frozenset[str]] = frozenset(
        {
            "p",
            "div",
            "br",
            "li",
            "tr",
            "table",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "section",
            "article",
            "dt",
            "dd",
        },
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in self.BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self) -> str:
        """Return the collected text with whitespace collapsed."""
        joined = unescape("".join(self._chunks))
        joined = _WHITESPACE.sub(" ", joined)
        lines = [line.strip() for line in joined.split("\n")]
        return _BLANK_LINES.sub("\n\n", "\n".join(line for line in lines if line))


def html_to_text(html: str) -> str:
    """Extract readable text from an HTML document."""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.text()


def fetch_page_text(url: str, *, force: bool = False) -> str:
    """Download a web page and return its readable text.

    Args:
        url: Absolute URL of an HTML page.
        force: Bypass the HTTP cache.

    Returns:
        Plain text with blocks separated by newlines.

    """
    raw = fetch_bytes(url, suffix=".html", force=force)
    encoding = "utf-8"
    match = _CHARSET.search(raw[:4096])
    if match:
        encoding = match.group(1).decode("ascii", errors="ignore") or "utf-8"
    try:
        html = raw.decode(encoding, errors="replace")
    except LookupError:
        html = raw.decode("utf-8", errors="replace")
    return html_to_text(html)
