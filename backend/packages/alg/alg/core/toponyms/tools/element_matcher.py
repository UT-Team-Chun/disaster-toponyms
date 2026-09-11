"""Match place names against the element dictionary."""

from __future__ import annotations

from dataclasses import dataclass

from alg.core.toponyms.tools.normalize import comparison_key, normalize_reading
from alg.models.element import ElementDictionary, ToponymElement
from alg.models.hazard import HazardType
from alg.models.toponym import ElementRef

#: A one-character reading is far too common to identify an element.
MIN_READING_CHARS = 2


@dataclass(frozen=True)
class ElementMatch:
    """One element found inside a place name."""

    element: ToponymElement
    surface: str
    matched_on: str

    def to_ref(self) -> ElementRef:
        """Convert to the serialisable reference stored on a toponym."""
        return ElementRef(
            element_id=self.element.id,
            surface=self.surface,
            reading=self.element.readings[0] if self.element.readings else None,
            meaning=self.element.meaning,
        )


def match_elements(
    name: str,
    reading: str | None,
    dictionary: ElementDictionary,
    *,
    surface_only: bool = False,
) -> list[ElementMatch]:
    """Find every dictionary element present in a place name.

    Surfaces are matched against the folded spelling and readings against the
    folded katakana reading, so ``梅ヶ久保`` matches both ウメ（梅・埋）and
    クボ（窪・久保）.

    Reading matches are useful when the reading comes from a gazetteer that
    prints it for the name itself. They are far too loose for a nationwide sweep,
    where a reading such as ナギ also matches ヤナギ（柳）, so a sweep should pass
    ``surface_only``.

    Args:
        name: Place-name spelling.
        reading: Katakana reading if known.
        dictionary: Loaded element dictionary.
        surface_only: Ignore readings and match spellings only.

    Returns:
        Matches ordered by descending element specificity.

    """
    name_key = comparison_key(name)
    reading_key = "" if surface_only or not reading else normalize_reading(reading)

    matches: list[ElementMatch] = []
    for element in dictionary.elements:
        surface_hit = next(
            (surface for surface in element.surfaces if comparison_key(surface) in name_key),
            None,
        )
        if surface_hit is not None:
            matches.append(
                ElementMatch(element=element, surface=surface_hit, matched_on="surface")
            )
            continue
        if not reading_key:
            continue
        reading_hit = next(
            (
                candidate
                for candidate in element.readings
                if len(candidate) >= MIN_READING_CHARS
                and normalize_reading(candidate) in reading_key
            ),
            None,
        )
        if reading_hit is not None:
            matches.append(
                ElementMatch(element=element, surface=reading_hit, matched_on="reading"),
            )

    matches.sort(key=lambda match: match.element.specificity, reverse=True)
    return matches


def hazard_types_from_matches(matches: list[ElementMatch]) -> list[HazardType]:
    """Collect the distinct hazard types implied by matched elements."""
    hazards: list[HazardType] = []
    for match in matches:
        for hazard in match.element.hazard_types:
            if hazard not in hazards:
                hazards.append(hazard)
    return hazards


def max_specificity(matches: list[ElementMatch]) -> float:
    """Return the highest specificity among the matches, or zero."""
    return max((match.element.specificity for match in matches), default=0.0)
