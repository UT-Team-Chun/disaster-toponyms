"""Normalisation of Japanese place-name spellings and readings.

Place names in old gazetteers use pre-war character forms, letter spacing and
half-width katakana, so every surface form has to be folded to a canonical
shape before names from different sources can be compared.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

_SPACES = re.compile(r"[\s\u3000]+")
_KATAKANA_SMALL_KE: Final = "ヶ"
#: Hiragana block, converted to katakana by adding this offset.
_HIRAGANA_FIRST: Final = 0x3041
_HIRAGANA_LAST: Final = 0x3096
_TO_KATAKANA_OFFSET: Final = 0x60

#: Pre-war / variant kanji -> modern form, restricted to forms seen in place names.
VARIANT_KANJI: Final[dict[str, str]] = {
    "澤": "沢",
    "瀧": "滝",
    "嶋": "島",
    "嵨": "島",
    "﨑": "崎",
    "邊": "辺",
    "邉": "辺",
    "櫻": "桜",
    "藪": "薮",
    "曾": "曽",
    "圓": "円",
    "國": "国",
    "驛": "駅",
    "濱": "浜",
    "淵": "渕",
    "藏": "蔵",
    "臺": "台",
    "巖": "巌",
    "峯": "峰",
    "龍": "竜",
    "拔": "抜",
    "彌": "弥",
    "廣": "広",
    "澁": "渋",
    "壽": "寿",
    "萬": "万",
    "禮": "礼",
    "數": "数",
    "體": "体",
}

#: Interchangeable connective characters inside compound place names.
CONNECTIVES: Final[dict[str, str]] = {
    "ヶ": "ケ",
    "ケ": "ケ",
    "ガ": "ケ",
    "が": "ケ",
    "之": "ノ",
    "乃": "ノ",
    "の": "ノ",
    "ノ": "ノ",
}


def strip_spaces(value: str) -> str:
    """Remove every kind of whitespace, including the wide ideographic space."""
    return _SPACES.sub("", value)


def normalize_reading(value: str) -> str:
    """Fold a reading to full-width katakana without spaces.

    Args:
        value: Reading in half-width katakana, hiragana or mixed form.

    Returns:
        Canonical full-width katakana reading.

    """
    folded = unicodedata.normalize("NFKC", strip_spaces(value))
    result: list[str] = []
    for char in folded:
        code = ord(char)
        # Hiragana -> katakana, keeping the small ke as-is.
        if _HIRAGANA_FIRST <= code <= _HIRAGANA_LAST:
            result.append(chr(code + _TO_KATAKANA_OFFSET))
        else:
            result.append(char)
    return "".join(result)


def normalize_name(value: str) -> str:
    """Fold a place-name spelling to a canonical comparable form.

    Args:
        value: Raw surface form, possibly letter-spaced or using variant kanji.

    Returns:
        Canonical spelling with spaces removed and variant kanji unified.

    """
    text = strip_spaces(value)
    text = "".join(VARIANT_KANJI.get(char, char) for char in text)
    return unicodedata.normalize("NFC", text)


def comparison_key(value: str) -> str:
    """Build the key used to detect that two spellings denote the same name.

    Connective characters (ヶ / ケ / ガ / が, ノ / 之 / 乃 / の) are unified because
    the same place is written both ways across sources.

    Args:
        value: Raw or normalised spelling.

    Returns:
        Aggressively folded key suitable for equality checks only.

    """
    text = normalize_name(value)
    return "".join(CONNECTIVES.get(char, char) for char in text)


def display_width(value: str) -> int:
    """Return the monospace display width, counting wide characters as two.

    Used to recover column positions from ``pdftotext -layout`` output.

    Args:
        value: Text fragment.

    Returns:
        Display width in half-width cells.

    """
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in value)


def has_small_ke(value: str) -> bool:
    """Return True when the name contains the small katakana ke (ヶ)."""
    return _KATAKANA_SMALL_KE in value


_FOLDED_SPACE = re.compile(r"(?<=[぀-ヿ㐀-䶿一-鿿。、）」])[ ]+(?=[぀-ヿ㐀-䶿一-鿿「（])")


def collapse_folded_japanese(value: str) -> str:
    """Remove the spaces a YAML folded scalar inserts inside Japanese prose.

    Writing a long Japanese sentence as a folded block scalar is the only
    readable option in a curated file, but folding turns each line break into a
    space that does not belong in Japanese text.

    Args:
        value: Text loaded from a folded YAML scalar.

    Returns:
        The same text with spaces between Japanese characters removed.

    """
    return _FOLDED_SPACE.sub("", value)


_JAPANESE = "぀-ヿ㐀-䶿一-鿿。、）」（「・"
_FOLDED_SPACE_BROAD = re.compile(
    rf"(?<=[{_JAPANESE}])[ ]+|[ ]+(?=[{_JAPANESE}])",
)


def collapse_folded_prose(value: str) -> str:
    """Remove folding spaces from Japanese prose that mixes digits and Latin.

    Unlike :func:`collapse_folded_japanese` this also drops a space that sits
    between a Japanese character and a number, which is what a YAML folded
    scalar produces in a sentence such as ``伝わり、 1953年``. It must not be used
    on verbatim quotes, where the original spacing has to survive.

    Args:
        value: Text loaded from a folded YAML scalar.

    Returns:
        The same text with folding spaces removed.

    """
    return _FOLDED_SPACE_BROAD.sub("", value)
