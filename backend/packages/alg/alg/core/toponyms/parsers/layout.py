"""Helpers for reading column-preserving text extracted from scanned books.

``pdftotext -layout`` keeps the original column positions, so a page of a
place-name dictionary arrives as fixed columns: the small-section name, the
section name and the etymology. Names are letter-spaced while the etymology is
set solid, which is what lets the two be told apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from alg.core.toponyms.tools.normalize import display_width

_NON_SPACE_RUN = re.compile(r"[^\s　]+")
_WIDE_GAP = re.compile(r"[\s　]{3,}")

#: Minimum length for a trailing block to count as prose rather than a name.
MIN_DESCRIPTION_CHARS = 6


@dataclass(frozen=True)
class Field:
    """One run of non-space characters with its display column."""

    column: int
    text: str


def split_fields(line: str) -> list[Field]:
    """Split a layout line into character runs with their display columns.

    Args:
        line: One line of ``pdftotext -layout`` output.

    Returns:
        Every run of non-space characters, left to right.

    """
    return [
        Field(column=display_width(line[: match.start()]), text=match.group())
        for match in _NON_SPACE_RUN.finditer(line)
    ]


def description_index(line: str, fields: list[Field], *, min_column: int) -> int | None:
    """Find the field where the prose column starts.

    The etymology column is the trailing part of the line that contains no run
    of three or more spaces, because prose is set without letter spacing.

    Args:
        line: The original line.
        fields: Fields produced by :func:`split_fields`.
        min_column: Lowest display column the prose column may start at.

    Returns:
        Index into ``fields``, or None when the line carries no prose.

    """
    for index, field in enumerate(fields):
        if field.column < min_column:
            continue
        offset = line.index(field.text, _char_offset(line, field.column))
        tail = line[offset:]
        if _WIDE_GAP.search(tail):
            continue
        if len(tail.strip()) >= MIN_DESCRIPTION_CHARS:
            return index
    return None


def _char_offset(line: str, column: int) -> int:
    """Translate a display column back into a character offset."""
    width = 0
    for index, char in enumerate(line):
        if width >= column:
            return index
        width += display_width(char)
    return len(line)


def join_name(fields: list[Field]) -> str:
    """Join letter-spaced name fields into a single spelling."""
    return "".join(field.text for field in fields)


def is_continuation(line: str) -> bool:
    """Return True when a line continues the prose of the previous entry.

    Args:
        line: One layout line.

    Returns:
        True when the line is a single indented block of prose.

    """
    stripped = line.strip()
    if not stripped:
        return False
    if _WIDE_GAP.search(stripped):
        return False
    return display_width(line) - display_width(stripped) > 0


_PAGE_ONLY_LINE = re.compile(r"^[\s　]*\d{1,4}[\s　]*$")


def strip_running_numbers(text: str) -> str:
    """Drop lines that hold nothing but a printed page number.

    Page numbers land in the middle of a sentence when a paragraph spans a page
    break, which makes verbatim quotes hard to read. Removing the standalone
    number lines keeps the wording untouched while joining the sentence back up.

    Args:
        text: Layout-preserving text of a scanned document.

    Returns:
        The same text without page-number-only lines.

    """
    return "\n".join(line for line in text.split("\n") if not _PAGE_ONLY_LINE.match(line))
