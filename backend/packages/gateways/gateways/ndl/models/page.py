"""Models for one scanned page of a book in the NDL digital collections."""

from __future__ import annotations

from pydantic import BaseModel

#: Viewer address of a single frame, used as the citation locator.
VIEWER_URL = "https://dl.ndl.go.jp/pid/{pid}/1/{frame}"


class TextBlock(BaseModel):
    """One OCR block on a page, with its position on the scanned image.

    The gazetteer is printed in vertical columns, so the geometry is what
    recovers the reading order and tells a ruby reading apart from body text.
    """

    text: str
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        """Return the right edge, which starts the column in vertical text."""
        return self.x + self.width


class NdlPage(BaseModel):
    """The OCR text of one frame together with its blocks."""

    pid: str
    frame: int
    contents: str
    blocks: list[TextBlock] = []

    def viewer_url(self) -> str:
        """Return the address a reader can open to check this page."""
        return VIEWER_URL.format(pid=self.pid, frame=self.frame)
