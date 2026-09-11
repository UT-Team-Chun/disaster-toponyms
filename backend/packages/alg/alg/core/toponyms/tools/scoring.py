"""Derive the evidence level and hazard ordering of a toponym record."""

from __future__ import annotations

from alg.models.toponym import Evidence, Toponym


def evidence_level(evidence: list[Evidence]) -> int:
    """Return the strongest level justified by the attached citations.

    Args:
        evidence: Citations attached to a toponym.

    Returns:
        0 when only the spelling matches, up to 3 when a recorded disaster or
        surviving oral tradition ties the name to an actual event. Citations that
        dispute the reading never raise the level.

    """
    return max((item.level for item in evidence if item.stance == "supports"), default=0)


def apply_scores(toponym: Toponym) -> Toponym:
    """Recompute the derived fields of a record in place.

    Args:
        toponym: Record whose evidence list is final.

    Returns:
        The same record with ``evidence_level`` refreshed.

    """
    toponym.evidence_level = evidence_level(toponym.evidence)
    if any(item.stance == "disputes" for item in toponym.evidence):
        toponym.disputed = True
    return toponym
