"""Split the scanned national gazetteer into citable entries.

Yoshida Tōgo's 大日本地名辞書 (1907) explains where tens of thousands of place
names come from, province by province. Read as one stream of OCR text it cannot
be cited, because there is no way to tell which sentence belongs to which name.
Read as a page layout it can: a heading in larger type opens an entry, the text
that follows belongs to it, and the running head says which province and
district the page is in.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from gateways.ndl.models.page import NdlPage
from gateways.nihu.models.place import HistoricalPlace

from alg.core.toponyms.tools.historical_index import HistoricalIndex
from alg.core.toponyms.tools.ndl_layout import classify_blocks, reading_beside

#: Longest body kept for one entry. A heading the parser missed would otherwise
#: let one entry swallow the next, and a quote could be attributed to the wrong
#: place. Anything past this is dropped rather than mis-attributed.
MAX_BODY_CHARS = 3000

#: A running head ending in this names the district of the page.
DISTRICT_SUFFIX = "郡"

#: District as it appears inside the concatenated margin of a page.
_DISTRICT_IN_MARGIN = re.compile(r"[一-龥々]{1,5}郡")


@dataclass
class GazetteerEntry:
    """One entry of the printed gazetteer, with the place it was matched to."""

    pid: str
    #: Identifier of the volume the entry was printed in.
    book_pid: str
    frame: int
    heading: str
    reading: str
    province: str
    district: str | None
    place: HistoricalPlace
    #: How many located entries shared the heading; 1 means unambiguous.
    candidates: int = 1
    parts: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Return the body of the entry as one string."""
        return "".join(self.parts)[:MAX_BODY_CHARS]

    def viewer_url(self) -> str:
        """Return the address of the frame this entry starts on."""
        return f"https://dl.ndl.go.jp/pid/{self.book_pid}/1/{self.frame}"


@dataclass
class ParseStats:
    """Counters describing one parsing run."""

    frames: int = 0
    headings: int = 0
    matched: int = 0
    unmatched: int = 0
    ambiguous: int = 0
    without_province: int = 0


def _running_context(
    running: list[str],
    index: HistoricalIndex,
    province: str | None,
    district: str | None,
) -> tuple[str | None, str | None]:
    """Update the province and district the margin of a page announces.

    A margin block usually holds the whole name, but the OCR sometimes splits it
    one character per block, so the margin is also read as one string.
    """
    for text in running:
        named = index.province_of(text)
        if named:
            province, district = named, None
            continue
        folded = index.modernise(text)
        if folded.endswith(DISTRICT_SUFFIX):
            district = folded

    joined = "".join(running)
    named = index.province_in(joined) or index.province_in(joined[::-1])
    if named and named != province:
        province, district = named, None
    if district is None:
        found = _DISTRICT_IN_MARGIN.search(index.modernise(joined))
        if found:
            district = found.group(0)
    return province, district


def parse_pages(
    pages: Iterable[NdlPage],
    index: HistoricalIndex,
    *,
    book_pid: str = "",
) -> tuple[list[GazetteerEntry], ParseStats]:
    """Split every page of one volume into entries.

    The running head is sticky: the province and district stay in force until a
    later page announces a different one, because the OCR does not recover the
    margin on every page.

    Args:
        pages: Frames of one volume, in printed order.
        index: Index of located historical place names.
        book_pid: Identifier of the volume, recorded on every entry.

    Returns:
        The entries found and the counters for the run.

    """
    stats = ParseStats()
    entries: list[GazetteerEntry] = []
    province: str | None = None
    district: str | None = None
    current: GazetteerEntry | None = None

    for page in pages:
        stats.frames += 1
        roled = classify_blocks(page)
        rubies = [item.block for item in roled if item.role == "ruby"]
        province, district = _running_context(
            [item.text for item in roled if item.role == "running"],
            index,
            province,
            district,
        )

        if province is None:
            stats.without_province += 1
            current = None
            continue

        for item in roled:
            if item.role == "heading":
                stats.headings += 1
                reading = reading_beside(item.block, rubies)
                found = index.lookup(item.text, province, district, reading)
                if found is None:
                    stats.unmatched += 1
                    current = None
                    continue
                place, candidates = found
                if candidates > 1:
                    stats.ambiguous += 1
                stats.matched += 1
                current = GazetteerEntry(
                    pid=place.place_id,
                    book_pid=book_pid or page.pid,
                    frame=page.frame,
                    heading=item.text,
                    reading=reading,
                    province=province,
                    district=district,
                    place=place,
                    candidates=candidates,
                )
                entries.append(current)
            elif item.role == "body" and current is not None:
                current.parts.append(item.text)
    return entries, stats


def deduplicate(entries: Iterable[GazetteerEntry]) -> Iterator[GazetteerEntry]:
    """Keep one entry per located place, preferring the fullest body.

    A heading can be detected on more than one frame when a page repeats it, so
    the longest body is the one that actually carries the explanation.

    Args:
        entries: Entries in parse order.

    Yields:
        One entry per place identifier.

    """
    best: dict[str, GazetteerEntry] = {}
    for entry in entries:
        previous = best.get(entry.pid)
        if previous is None or len(entry.text) > len(previous.text):
            best[entry.pid] = entry
    yield from best.values()
