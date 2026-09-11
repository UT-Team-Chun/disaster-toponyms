"""Decide what a place-name explanation actually claims about disaster history.

The evidence level of a record is driven entirely by the wording of its source.
A gazetteer that says 「崩壊地名」 or 「山腹の崩壊で埋まって出来た傾斜地」 states a
disaster origin; one that only says 「くぼ」 states terrain. Keeping the two apart
is what stops the dataset from turning spelling coincidences into warnings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from alg.core.toponyms.tools.hazard_text import hazard_types_from_text
from alg.core.toponyms.tools.normalize import strip_spaces
from alg.models.hazard import HazardType

#: Wording that states the name derives from a disaster or from a 替字 for one.
DISASTER_MARKERS: Final[tuple[str, ...]] = (
    "崩壊地名",
    "災害地名",
    "土石流",
    "山崩れ",
    "土砂崩れ",
    "土砂崩",
    "崖崩れ",
    "地すべり",
    "地滑り",
    "崩壊",
    "崩れ",
    "落石",
    "雪崩",
    "洪水",
    "氾濫",
    "水害",
    "浸水",
    "冠水",
    "押し出",
    "押出",
    "津波",
    "決壊",
    "流失",
    "流され",
    "埋まって",
    "埋って",
    "埋立",
)

#: Wording that states a terrain origin without naming a disaster.
TERRAIN_MARKERS: Final[tuple[str, ...]] = (
    "湿地",
    "低湿",
    "急傾斜",
    "傾斜地",
    "崖",
    "段丘",
    "くぼ",
    "窪",
    "川原",
    "河原",
    "土手",
    "水はけ",
    "沼",
    "泥",
    "沢の水",
    "溜池",
    "堆積",
)

#: Sentences about administrative mergers carry no etymological information.
ADMIN_MARKERS: Final[tuple[str, ...]] = ("地租改正", "町村制", "合併し")

_SENTENCE_SPLIT = re.compile(r"(?<=。)")
_DATED_EVENT = re.compile(r"[（(][０-９\d]{3,4}[）)]")
_MAX_QUOTE_CHARS = 220
_MAX_QUOTE_SENTENCES = 2
_MAX_SUMMARY_CHARS = 140


@dataclass(frozen=True)
class Claim:
    """What a source says about one place name."""

    level: int
    markers: tuple[str, ...]
    hazard_types: tuple[HazardType, ...]
    quote: str
    summary: str

    def is_evidence(self) -> bool:
        """Return True when the source says more than the spelling alone."""
        return self.level >= 1


def _sentences(text: str) -> list[str]:
    """Split Japanese prose into sentences on the full stop."""
    return [part.strip() for part in _SENTENCE_SPLIT.split(text) if part.strip()]


def _markers_in(text: str, markers: tuple[str, ...]) -> tuple[str, ...]:
    """Return the markers present in a text, in declaration order."""
    return tuple(marker for marker in markers if marker in text)


def classify_description(description: str, *, name: str = "") -> Claim | None:
    """Classify a place-name explanation into an evidence claim.

    Args:
        description: The explanation exactly as printed in the source.
        name: Place name, used only for the summary fallback.

    Returns:
        A claim when the explanation states a disaster or terrain origin,
        otherwise None.

    """
    del name
    sentences = _sentences(description)
    informative = [sentence for sentence in sentences if not _markers_in(sentence, ADMIN_MARKERS)]
    if not informative:
        return None

    body = "".join(informative)
    disaster = _markers_in(body, DISASTER_MARKERS)
    terrain = _markers_in(body, TERRAIN_MARKERS)
    if not disaster and not terrain:
        return None

    chosen = DISASTER_MARKERS if disaster else TERRAIN_MARKERS
    quote_sentences = [sentence for sentence in informative if _markers_in(sentence, chosen)][
        :_MAX_QUOTE_SENTENCES
    ]
    quote = "".join(quote_sentences)[:_MAX_QUOTE_CHARS]

    level = 1
    if disaster:
        level = 3 if _DATED_EVENT.search(quote) else 2

    return Claim(
        level=level,
        markers=disaster or terrain,
        hazard_types=tuple(hazard_types_from_text(body)),
        quote=quote,
        summary="".join(informative)[:_MAX_SUMMARY_CHARS],
    )


def verify_quote(quote: str, source_text: str) -> bool:
    """Check that a quote appears verbatim in the source.

    Whitespace is ignored because the source is a column layout in which one
    sentence is split across printed lines. A quote that fails this check was
    stitched together from non-adjacent text and must not be cited.

    Args:
        quote: Candidate excerpt.
        source_text: Full text of the source document.

    Returns:
        True when the quote is a contiguous excerpt of the source.

    """
    if not quote:
        return False
    return strip_spaces(quote) in strip_spaces(source_text)
