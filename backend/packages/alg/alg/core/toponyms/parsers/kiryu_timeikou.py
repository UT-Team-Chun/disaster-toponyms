"""Parser for the municipal place-name study 『桐生市地名考』.

The book lists every 字 and 小字 of Kiryu (Gunma) with an explanation of its
origin, and states terrain-derived readings explicitly, for example
「間々久保 ... 山腹の崩壊で埋まって出来た久保。間々は崩壊地名。」. That makes it a
direct source of level-2 evidence: the disaster reading comes from the source
rather than from the spelling.

Layout notes. ``pdftotext -layout`` preserves the printed columns. Each village
section opens with a header line, one to three parenthesised lines naming the
present-day town blocks, and a column header ``字 小字 地名語源``. Data lines then
carry the 小字 name in the left column, the 字 name in the middle column and the
etymology on the right; readings appear on their own line in half-width katakana.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from alg.core.toponyms.parsers.layout import (
    Field,
    description_index,
    is_continuation,
    join_name,
    split_fields,
)
from alg.core.toponyms.tools.normalize import normalize_reading, strip_spaces

#: Display column where the 字 column starts; anything left of it is a 小字.
AZA_COLUMN = 17
#: Lowest display column the prose column may start at.
PROSE_MIN_COLUMN = 17
#: Longest plausible place name, in characters.
MAX_NAME_CHARS = 10

_HALFWIDTH_KATAKANA = re.compile(r"^[｡-ﾟ\s　]+$")
_PAGE_NUMBER = re.compile(r"^[\s　]*(\d{1,3})[\s　]*$")
_TOC_LINE = re.compile(r"・{3,}")
_VILLAGE_HEADER = re.compile(r"^(.{1,14}?(?:村|町|宿|新田))（([ァ-ヶー]{2,24})）$")
_COLUMN_HEADER = re.compile(r"^字小字地名")
_AREA_NOISE = re.compile(r"[＊*]\s*町別小字表[^）)]*参照|[＊*][^）)]*参照")
_HEADER_NOISE = re.compile(r"^[（(]\s*[０-９\d]{4}\s*[）)]の水帳|水帳の字による")
#: Safety valve for the parenthesised block naming a village's present-day area.
MAX_AREA_LINES = 6
_OPEN_PARENS = "（("
_CLOSE_PARENS = "）)"
_NAME_FORBIDDEN = re.compile(r"[。、，,；;：:（）()｛｝\[\]・～~＊*／/｜|＜＞<>\d０-９]")
_NAME_HAS_WORD = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")


@dataclass(frozen=True)
class GazetteerEntry:
    """One entry of the book: a place name and its stated origin."""

    name: str
    reading: str | None
    description: str
    level: str
    village: str | None = None
    village_reading: str | None = None
    modern_area: str | None = None
    aza: str | None = None
    page: int | None = None


def is_plausible_name(name: str) -> bool:
    """Return True when a string looks like a place name rather than prose.

    Args:
        name: Candidate spelling taken from the name columns.

    Returns:
        True for short punctuation-free strings containing Japanese script.

    """
    if not name or len(name) > MAX_NAME_CHARS:
        return False
    if _NAME_FORBIDDEN.search(name):
        return False
    return bool(_NAME_HAS_WORD.search(name))


@dataclass
class _State:
    """Mutable parser state carried across lines."""

    in_dictionary: bool = False
    collecting_area: bool = False
    village: str | None = None
    village_reading: str | None = None
    area_lines: list[str] = field(default_factory=list)
    modern_area: str | None = None
    page: int | None = None
    pending_reading: str | None = None
    entries: list[GazetteerEntry] = field(default_factory=list)
    open_description: list[str] = field(default_factory=list)

    def finish_area(self) -> None:
        """Turn the buffered parenthesised lines into the modern area string."""
        self.collecting_area = False
        if not self.area_lines:
            return
        joined = strip_spaces("".join(self.area_lines))
        joined = _AREA_NOISE.sub("", joined).strip("（）() 　、,")
        self.modern_area = joined or None
        self.area_lines.clear()

    def flush(self) -> None:
        """Attach any buffered continuation lines to the last entry."""
        if not self.open_description or not self.entries:
            self.open_description.clear()
            return
        last = self.entries[-1]
        self.entries[-1] = GazetteerEntry(
            name=last.name,
            reading=last.reading,
            description=last.description + "".join(self.open_description),
            level=last.level,
            village=last.village,
            village_reading=last.village_reading,
            modern_area=last.modern_area,
            aza=last.aza,
            page=last.page,
        )
        self.open_description.clear()


def _split_name_fields(fields: list[Field]) -> tuple[list[Field], list[Field]]:
    """Split name fields into the 小字 column and the 字 column."""
    left = [item for item in fields if item.column < AZA_COLUMN]
    right = [item for item in fields if item.column >= AZA_COLUMN]
    if left and len(join_name(left)) > MAX_NAME_CHARS:
        widest_index = max(
            range(1, len(left)),
            key=lambda index: left[index].column - left[index - 1].column,
            default=0,
        )
        if widest_index:
            right = left[widest_index:] + right
            left = left[:widest_index]
    return left, right


def _handle_section_start(line: str, stripped: str, state: _State) -> bool:
    """Consume the lines that open a village section."""
    if _COLUMN_HEADER.match(stripped):
        state.finish_area()
        state.in_dictionary = True
        return True

    village_match = _VILLAGE_HEADER.match(stripped)
    if village_match:
        state.flush()
        state.village = village_match.group(1)
        state.village_reading = normalize_reading(village_match.group(2))
        state.modern_area = None
        state.area_lines.clear()
        state.collecting_area = True
        return True

    if state.collecting_area:
        return _collect_area(stripped, state)

    if _HALFWIDTH_KATAKANA.match(line):
        state.pending_reading = normalize_reading(line)
        return True
    return False


def _handle_structure(line: str, state: _State) -> bool:
    """Consume structural lines and report whether the line was consumed."""
    stripped = strip_spaces(line)
    if not stripped or _TOC_LINE.search(line):
        return True

    page_match = _PAGE_NUMBER.match(line)
    if page_match:
        state.page = int(page_match.group(1))
        return True

    return _handle_section_start(line, stripped, state)


def _collect_area(stripped: str, state: _State) -> bool:
    """Accumulate the parenthesised block that names a village's modern area.

    The block always opens with a parenthesis right after the village header and
    may run over several printed lines, so collection ends when the parentheses
    balance again.

    Args:
        stripped: Line with all whitespace removed.
        state: Parser state being updated.

    Returns:
        True when the line was consumed as part of the area block.

    """
    if not state.area_lines and stripped[0] not in _OPEN_PARENS:
        state.collecting_area = False
        return False
    state.area_lines.append(stripped)
    depth = sum(
        stripped.count(char) for stripped in state.area_lines for char in _OPEN_PARENS
    ) - sum(stripped.count(char) for stripped in state.area_lines for char in _CLOSE_PARENS)
    if depth <= 0 or len(state.area_lines) >= MAX_AREA_LINES:
        state.finish_area()
    return True


def _append_continuation(line: str, state: _State) -> None:
    """Buffer a prose continuation line, dropping running-header noise."""
    stripped = strip_spaces(line)
    if _HEADER_NOISE.search(stripped):
        return
    state.open_description.append(stripped)


def _handle_entry(line: str, state: _State) -> None:
    """Consume a data line, either a new entry or a continuation of one."""
    fields = split_fields(line)
    if not fields:
        return

    prose_index = description_index(line, fields, min_column=PROSE_MIN_COLUMN)
    name_fields = fields[:prose_index] if prose_index is not None else []
    if prose_index is None or not name_fields:
        if is_continuation(line) and state.entries:
            _append_continuation(line, state)
        return

    left, right = _split_name_fields(name_fields)
    koaza = join_name(left)
    aza = join_name(right)
    name = koaza or aza
    if not is_plausible_name(name):
        state.pending_reading = None
        return

    state.flush()
    state.entries.append(
        GazetteerEntry(
            name=name,
            reading=state.pending_reading,
            description="".join(item.text for item in fields[prose_index:]),
            level="koaza" if koaza else "aza",
            village=state.village,
            village_reading=state.village_reading,
            modern_area=state.modern_area,
            aza=aza if (aza and aza != koaza) else None,
            page=state.page,
        ),
    )
    state.pending_reading = None


def parse_kiryu_text(text: str) -> list[GazetteerEntry]:
    """Parse the extracted text of 『桐生市地名考』 into entries.

    Args:
        text: Output of ``pdftotext -layout`` for the whole book.

    Returns:
        Every dictionary entry carrying a plausible name and an explanation.

    """
    state = _State()
    for raw_line in text.split("\n"):
        line = raw_line.replace("\f", "")
        if _handle_structure(line, state):
            continue
        if state.in_dictionary:
            _handle_entry(line, state)
    state.flush()
    return state.entries
