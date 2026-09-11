"""Map free-text Japanese disaster wording onto the hazard vocabulary."""

from __future__ import annotations

from alg.models.hazard import HAZARD_KEYWORDS_JA, HazardType


def hazard_types_from_text(text: str | None) -> list[HazardType]:
    """Infer hazard types from a Japanese label or narrative.

    Args:
        text: Free text such as ``洪水・土砂災害`` or a monument narrative.

    Returns:
        Distinct hazard types in the order the keywords were declared.

    """
    if not text:
        return []
    found: list[HazardType] = []
    for keyword, hazard in HAZARD_KEYWORDS_JA:
        if keyword in text and hazard not in found:
            found.append(hazard)
    return found
