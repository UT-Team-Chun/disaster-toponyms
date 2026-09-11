"""Derive the evidence level of a toponym from its citations and records.

Two different facts are kept apart here. What a source says about where a name
comes from sets the *origin level*. Whether a disaster is actually recorded at
that place is a separate observation, and it can only raise the published level
when a documented origin already exists. Without that rule a name that merely
looks like a hazard word would be promoted by any flood that happened nearby.
"""

from __future__ import annotations

from alg.models.toponym import (
    ORIGIN_EVIDENCE_KINDS,
    DisasterRecord,
    Evidence,
    Toponym,
)

#: A source can state a disaster origin, but the correspondence with a recorded
#: event is what level 3 means, so origin evidence alone stops at 2.
MAX_ORIGIN_LEVEL = 2
#: Level a curator may assign directly when they have checked the correspondence.
CURATED_LEVEL_3 = 3


def origin_level(evidence: list[Evidence]) -> int:
    """Return what the sources claim about the origin of the name.

    Args:
        evidence: Citations attached to a toponym.

    Returns:
        0 when no source explains the name, 1 for a terrain origin and 2 when a
        source states a disaster origin or a substituted character. Citations
        that dispute the reading never raise the level.

    """
    levels = [
        min(item.level, MAX_ORIGIN_LEVEL)
        for item in evidence
        if item.stance == "supports" and item.kind in ORIGIN_EVIDENCE_KINDS
    ]
    return max(levels, default=0)


def evidence_level(evidence: list[Evidence], records: list[DisasterRecord] | None = None) -> int:
    """Return the strongest level justified by the citations and the records.

    Args:
        evidence: Citations attached to a toponym.
        records: Disasters recorded for the same place.

    Returns:
        0 when only the spelling matches, up to 3 when a documented origin is
        matched by a disaster recorded at the same place. A record attached to a
        name whose origin no source explains leaves the level at 0.

    """
    base = origin_level(evidence)
    if base == 0:
        return 0
    curated = any(
        item.stance == "supports"
        and item.level >= CURATED_LEVEL_3
        and item.extracted_by == "human"
        for item in evidence
    )
    if curated or any(record.corroborates_origin() for record in records or []):
        return CURATED_LEVEL_3
    return base


def apply_scores(toponym: Toponym) -> Toponym:
    """Recompute the derived fields of a record in place.

    Args:
        toponym: Record whose evidence and disaster records are final.

    Returns:
        The same record with its levels and dispute flag refreshed.

    """
    toponym.origin_level = origin_level(toponym.evidence)
    toponym.evidence_level = evidence_level(toponym.evidence, toponym.disaster_records)
    if any(item.stance == "disputes" for item in toponym.evidence):
        toponym.disputed = True
    return toponym
