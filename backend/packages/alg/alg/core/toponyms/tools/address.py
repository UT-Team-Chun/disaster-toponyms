"""Extract present-day address components from municipal place-name studies."""

from __future__ import annotations

import re
from typing import Final

_KANJI_DIGITS: Final[dict[str, str]] = {
    "0": "〇",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
    "１": "一",
    "２": "二",
    "３": "三",
    "４": "四",
    "５": "五",
    "６": "六",
    "７": "七",
    "８": "八",
    "９": "九",
}
_TEN_PREFIXES: Final[frozenset[str]] = frozenset({"1", "１"})
#: A village is often described as a range of blocks, e.g. 新宿１～３丁目.
_CHOME = re.compile(
    r"^(?P<town>[^、,。／/0-9０-９]{1,14}?)(?P<number>[0-9０-９]{1,2})"
    r"(?:[～~〜\-][0-9０-９]{1,2})?丁目",
)
_TOWN = re.compile(r"^(?P<town>[^、,。／/0-9０-９]{1,16})")
_QUALIFIER = re.compile(r"(?:の一部|の大部分|の内|の残り|分|一部|大部分)$")
_SEPARATORS = re.compile(r"[、,／/]")
_CHOME_NUMBER_LENGTH = 2


def kanji_chome(number: str) -> str:
    """Convert an Arabic 丁目 number into the kanji form used in address tables.

    Args:
        number: One or two digit number in ASCII or full-width form.

    Returns:
        Kanji numeral, for example ``5`` becomes ``五`` and ``12`` becomes ``十二``.

    """
    if len(number) == _CHOME_NUMBER_LENGTH and number[0] in _TEN_PREFIXES:
        tail = _KANJI_DIGITS.get(number[1], number[1])
        return "十" if tail == "〇" else f"十{tail}"
    return "".join(_KANJI_DIGITS.get(char, char) for char in number)


def strip_qualifier(town: str) -> str:
    """Remove the "part of" wording municipal studies append to a block name."""
    previous = ""
    result = town
    while result != previous:
        previous = result
        result = _QUALIFIER.sub("", result)
    return result


def first_oaza(area_text: str | None) -> str | None:
    """Pick the first present-day town block out of a listing.

    Municipal studies describe a former village as a list of today's blocks, for
    example ``梅田町５丁目の一部、平井町``. The first entry becomes the
    representative large section used for geocoding.

    Args:
        area_text: Raw listing text, or None.

    Returns:
        Normalised block name such as ``梅田町五丁目``, or None.

    """
    if not area_text:
        return None
    head = _SEPARATORS.split(area_text)[0].strip()
    if not head:
        return None

    chome = _CHOME.match(head)
    if chome:
        town = strip_qualifier(chome.group("town"))
        if town:
            return f"{town}{kanji_chome(chome.group('number'))}丁目"

    town_match = _TOWN.match(head)
    if not town_match:
        return None
    town = strip_qualifier(town_match.group("town"))
    return town or None
