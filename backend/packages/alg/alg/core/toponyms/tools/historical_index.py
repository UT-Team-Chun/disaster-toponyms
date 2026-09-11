"""Identify a heading printed in a Meiji-era gazetteer.

The printed book spells names in pre-war characters (豐後, 澤); the located
dataset spells the same names in modern ones (豊後, 沢). Rather than hard-code a
conversion table, the mapping is learned from the dataset itself, which records
both the modern transcription and the spelling as originally printed for tens of
thousands of names.

Matching a heading then means: fold it to modern characters and look it up
inside the province and district the running head of the page announces. The
district is what keeps two villages of the same name apart.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Final

from gateways.nihu.models.place import HistoricalPlace

#: A character mapping is only trusted when the dataset shows it more than once.
MIN_MAPPING_SUPPORT: Final = 2

#: Generic tails the printed heading often drops or the OCR loses. Trying them
#: lets 「八坂〓」 reach 八坂郷 without weakening the match to a bare prefix.
NAME_SUFFIXES: Final[tuple[str, ...]] = (
    "",
    "郷",
    "村",
    "郡",
    "川",
    "山",
    "浦",
    "島",
    "荘",
    "庄",
    "城",
    "町",
    "原",
    "崎",
    "岳",
    "嶽",
    "池",
    "神社",
    "城址",
)

#: Characters the OCR could not recognise.
UNREADABLE: Final = "〓"

#: Shortest stem a heading may be reduced to. Without this, one surviving
#: character plus a generic tail would match an unrelated place: 山城 would
#: reach 山崎 through 山 + 崎.
MIN_STEM_CHARS: Final = 2
#: Most characters that may be dropped from the end of a heading. The OCR loses
#: a tail character now and then; it does not lose half a name.
MAX_DROPPED_CHARS: Final = 2


def _fold_reading(value: str) -> str:
    """Fold a reading so an OCR ruby can be compared with a recorded one."""
    return "".join(char for char in value or "" if "ァ" <= char <= "ヴ")


def _pick(found: list[HistoricalPlace], reading: str) -> HistoricalPlace:
    """Choose between entries that share a name, using the printed reading."""
    folded = _fold_reading(reading)
    if not folded or len(found) == 1:
        return found[0]
    for place in found:
        if any(_fold_reading(recorded) == folded for recorded in place.readings):
            return place
    return found[0]


def spelling_pairs(places: Iterable[HistoricalPlace]) -> list[tuple[str, str]]:
    """Return the (printed spelling, modern spelling) pairs carried by entries."""
    return [(old, place.name) for place in places for old in place.old_forms]


def learn_character_mapping(pairs: Iterable[tuple[str, str]]) -> dict[str, str]:
    """Learn the pre-war to modern character mapping from spelling pairs.

    Args:
        pairs: Each entry's spelling as printed beside its modern transcription.

    Returns:
        Mapping from a pre-war character to its modern form.

    """
    votes: dict[str, Counter[str]] = defaultdict(Counter)
    for old, new in pairs:
        if len(old) != len(new):
            continue
        for old_char, new_char in zip(old, new, strict=True):
            if old_char != new_char:
                votes[old_char][new_char] += 1
    mapping: dict[str, str] = {}
    for old_char, counter in votes.items():
        new_char, support = counter.most_common(1)[0]
        if support >= MIN_MAPPING_SUPPORT:
            mapping[old_char] = new_char
    return mapping


@dataclass
class HistoricalIndex:
    """Lookup tables over the located historical place names."""

    character_mapping: dict[str, str] = field(default_factory=dict)
    provinces: set[str] = field(default_factory=set)
    by_province_district: dict[tuple[str, str, str], list[HistoricalPlace]] = field(
        default_factory=dict,
    )
    by_province: dict[tuple[str, str], list[HistoricalPlace]] = field(default_factory=dict)
    children: dict[tuple[str, str], list[HistoricalPlace]] = field(default_factory=dict)

    def modernise(self, text: str) -> str:
        """Fold a pre-war spelling to its modern characters."""
        return "".join(self.character_mapping.get(char, char) for char in text or "")

    def province_of(self, text: str) -> str | None:
        """Return the province a running head names, or None."""
        folded = self.modernise(text)
        return folded if folded in self.provinces else None

    def province_in(self, text: str) -> str | None:
        """Return the province named anywhere inside a margin's text.

        The OCR sometimes breaks a two-character province in the margin into one
        block per character, so the name only reappears once the margin is read
        as a whole. The longest match wins, so 陸中 is not read as 陸奥.

        Args:
            text: Every margin block of one page, concatenated.

        Returns:
            The province in modern characters, or None.

        """
        folded = self.modernise(text)
        found = [name for name in self.provinces if name in folded]
        if not found:
            return None
        return max(found, key=len)

    def _candidates(self, key: str, province: str, district: str | None) -> list[HistoricalPlace]:
        """Return the entries filed under a name, narrowest scope first."""
        if district:
            hit = self.by_province_district.get((province, district, key))
            if hit:
                return hit
        return self.by_province.get((province, key), [])

    def lookup(
        self,
        heading: str,
        province: str,
        district: str | None = None,
        reading: str = "",
    ) -> tuple[HistoricalPlace, int] | None:
        """Find the entry a printed heading refers to.

        Args:
            heading: Heading exactly as printed, in pre-war characters.
            province: Province announced by the running head, in modern form.
            district: District announced by the running head, in modern form.
            reading: Reading printed beside the heading, used to choose between
                entries that share a name.

        Returns:
            The matched entry and how many entries shared the same name, or None
            when the heading matches nothing in the province.

        """
        folded = self.modernise(heading).replace(UNREADABLE, "")
        if not folded or not province:
            return None
        shortest = max(MIN_STEM_CHARS, len(folded) - MAX_DROPPED_CHARS)
        lengths = range(len(folded), min(shortest, len(folded)) - 1, -1)
        for length in lengths:
            stem = folded[:length]
            for suffix in NAME_SUFFIXES:
                found = self._candidates(stem + suffix, province, district)
                if found:
                    return _pick(found, reading), len(found)
        return None

    def children_of(self, place: HistoricalPlace) -> list[HistoricalPlace]:
        """Return the entries the source describes inside another entry.

        Args:
            place: The entry whose heading the page prints.

        Returns:
            Entries whose printed source names this one as their heading.

        """
        if not place.province:
            return []
        return self.children.get((place.province, place.name), [])


def build_index(
    places: list[HistoricalPlace],
    *,
    pairs: Iterable[tuple[str, str]] | None = None,
) -> HistoricalIndex:
    """Build the lookup tables for one source of historical place names.

    Args:
        places: Entries to index, normally the national gazetteer half.
        pairs: Spelling pairs to learn the character mapping from. The gazetteer
            half barely records printed spellings, so the caller normally passes
            the pairs of the whole dataset here.

    Returns:
        An index able to resolve a printed heading to a located entry.

    """
    index = HistoricalIndex(
        character_mapping=learn_character_mapping(
            spelling_pairs(places) if pairs is None else pairs,
        ),
    )
    for place in places:
        province = place.province
        if not province:
            continue
        index.provinces.add(province)
        spellings = {index.modernise(place.name)}
        spellings.update(index.modernise(form) for form in place.old_forms)
        for spelling in spellings:
            if not spelling:
                continue
            index.by_province.setdefault((province, spelling), []).append(place)
            if place.district:
                key = (province, place.district, spelling)
                index.by_province_district.setdefault(key, []).append(place)
        if place.parent_entry:
            parent = index.modernise(place.parent_entry)
            index.children.setdefault((province, parent), []).append(place)
    return index
