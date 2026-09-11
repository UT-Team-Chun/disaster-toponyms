"""Recover the structure of a vertically typeset page from its OCR blocks.

The national gazetteer is set in vertical columns: the reading of an entry is
printed as small katakana in a narrow column to the right of the heading, the
heading itself is set in larger type than the body, and the province and
district run along the outer margin of every page. The OCR keeps the bounding
box of each block, which is enough to tell those four things apart — and telling
them apart is what turns a wall of text into entries that can be cited.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass
from typing import Final, Literal

from gateways.ndl.models.page import NdlPage, TextBlock

BlockRole = Literal["running", "ruby", "heading", "body"]

#: How far from the outermost column a block still counts as being in the
#: margin, as a fraction of the glyph size. The running head sits about one
#: column clear of the text, so half a column separates the two reliably.
MARGIN_FACTOR: Final = 0.5
#: A running head is short: a province, a district, or a page number.
MAX_RUNNING_CHARS: Final = 6
#: Ruby is set at roughly two thirds of the body size.
MAX_RUBY_RATIO: Final = 45.0
#: A heading is set noticeably larger than the body.
MIN_HEADING_RATIO: Final = 55.0
#: …and its column is wider than the body columns of the same page.
HEADING_WIDTH_FACTOR: Final = 1.05
#: One character alone cannot be measured reliably.
MIN_HEADING_CHARS: Final = 2
#: Fallback glyph size for a page whose blocks carry no usable geometry.
DEFAULT_GLYPH_WIDTH: Final = 56.0

_KATAKANA_ONLY = re.compile(r"^[ァ-ヶー゙゚・〓]+$")
_KANJI_ONLY = re.compile(r"^[一-龥々〆ヶ〓]+$")


@dataclass(frozen=True)
class RoledBlock:
    """One OCR block together with the role it plays on the page."""

    role: BlockRole
    block: TextBlock

    @property
    def text(self) -> str:
        """Return the recognised text of the block."""
        return self.block.text


def glyph_ratio(block: TextBlock) -> float:
    """Return the height taken by one character, which is the type size."""
    return block.height / max(len(block.text), 1)


def classify_blocks(page: NdlPage) -> list[RoledBlock]:
    """Assign a role to every block of a page.

    Args:
        page: Page whose blocks carry their bounding boxes.

    Returns:
        The blocks in reading order, each labelled with its role. A page whose
        blocks have no geometry yields body blocks only.

    """
    blocks = [block for block in page.blocks if block.text]
    if not blocks:
        return []
    widths = [block.width for block in blocks if block.width > 0]
    median_width = statistics.median(widths) if widths else DEFAULT_GLYPH_WIDTH
    margin = max(block.x for block in blocks) - median_width * MARGIN_FACTOR
    # The margin holds the running head and nothing else. A page whose outermost
    # column carries running text has no margin the OCR could separate, so a
    # heading printed there must not be mistaken for one.
    in_margin = [block for block in blocks if block.x >= margin]
    has_margin = all(len(block.text) <= MAX_RUNNING_CHARS for block in in_margin)

    roled: list[RoledBlock] = []
    for block in blocks:
        ratio = glyph_ratio(block)
        if has_margin and block.x >= margin:
            role: BlockRole = "running"
        elif _KATAKANA_ONLY.match(block.text) and ratio < MAX_RUBY_RATIO:
            role = "ruby"
        elif (
            len(block.text) >= MIN_HEADING_CHARS
            and ratio >= MIN_HEADING_RATIO
            and block.width >= median_width * HEADING_WIDTH_FACTOR
            and _KANJI_ONLY.match(block.text)
        ):
            role = "heading"
        else:
            role = "body"
        roled.append(RoledBlock(role=role, block=block))
    return roled


def reading_beside(heading: TextBlock, rubies: list[TextBlock]) -> str:
    """Return the ruby printed alongside a heading.

    In vertical text the reading sits in its own narrow column to the right of
    the word it annotates and spans the same rows, so the ruby blocks that
    overlap the heading vertically and start to its right are its reading.

    Args:
        heading: The heading block.
        rubies: Every ruby block on the same page.

    Returns:
        The reading, or an empty string when the OCR did not record one.

    """
    span = heading.width * 2.5
    matched = [
        ruby
        for ruby in rubies
        if 0 < ruby.x - heading.x <= span
        and min(ruby.y + ruby.height, heading.y + heading.height) - max(ruby.y, heading.y) > 0
    ]
    matched.sort(key=lambda ruby: ruby.y)
    return "".join(ruby.text for ruby in matched)
