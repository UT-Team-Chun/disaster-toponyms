"""Attach recorded disasters to the place names they actually name.

A record only belongs to a place name when the source names that place: the same
section of the same municipality, and a disaster of a kind the name could be
warning about. Distance alone is not evidence — a flood two kilometres away says
nothing about why a hillside above it is called what it is — so a mention that
only lands nearby is kept as context and never raises the evidence level.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field

from alg.core.toponyms.pipelines.corroborate_hazard import haversine_km
from alg.core.toponyms.tools.disaster_records import DisasterMention
from alg.core.toponyms.tools.normalize import comparison_key
from alg.core.toponyms.tools.scoring import apply_scores
from alg.models.toponym import Toponym

#: A mention further than this from the place is not about the same place.
MAX_LINK_KM = 10.0
#: Records kept per place, so one much-commemorated disaster cannot bury a page.
MAX_RECORDS_PER_PLACE = 6


@dataclass
class LinkStats:
    """Counters describing one linking run."""

    mentions: int = 0
    linked: int = 0
    demoted_hazard: int = 0
    too_far: int = 0
    unmatched: int = 0
    places_with_records: int = 0
    raised_to_level_3: int = 0
    candidates_with_records: int = 0
    messages: list[str] = field(default_factory=list)


def _keys_of(record: Toponym) -> set[tuple[str, str]]:
    """Return the municipality-and-name keys a record can be addressed by."""
    municipality = comparison_key(record.admin.municipality or "")
    if not municipality:
        return set()
    names = {record.name, *record.variants}
    if record.admin.koaza:
        names.add(record.admin.koaza)
    if record.admin.oaza:
        names.add(record.admin.oaza)
    return {(municipality, comparison_key(name)) for name in names if name}


def _compatible(record_hazards: Sequence[str], place_hazards: Sequence[str]) -> bool:
    """Say whether a disaster is of a kind the name could be warning about."""
    if not record_hazards or not place_hazards:
        return True
    return bool(set(record_hazards) & set(place_hazards))


def _distance_to(mention: DisasterMention, target: Toponym) -> float | None:
    """Return the distance between a mention and a place, when both are located."""
    if target.location is None or mention.lat is None or mention.lon is None:
        return None
    return haversine_km(target.location.lat, target.location.lon, mention.lat, mention.lon)


def _attach(mention: DisasterMention, target: Toponym, stats: LinkStats) -> None:
    """Attach one mention to one place, if it is really about that place."""
    distance = _distance_to(mention, target)
    if distance is not None and distance > MAX_LINK_KM:
        stats.too_far += 1
        return
    if len(target.disaster_records) >= MAX_RECORDS_PER_PLACE:
        return
    if any(
        existing.source_id == mention.record.source_id
        and existing.locator == mention.record.locator
        for existing in target.disaster_records
    ):
        return
    record = mention.record.model_copy(deep=True)
    record.distance_km = round(distance, 2) if distance is not None else None
    if not _compatible(record.hazard_types, target.hazard_types):
        record.relation = "nearby_record"
        stats.demoted_hazard += 1
    target.disaster_records.append(record)
    stats.linked += 1


def link_mentions(
    mentions: list[DisasterMention],
    toponyms: list[Toponym],
    candidates: list[Toponym],
) -> LinkStats:
    """Attach every mention to the place names that carry the same name.

    Args:
        mentions: Places named as hit, read out of monuments and gazetteer text.
        toponyms: Evidence-backed records, updated in place.
        candidates: Spelling-only candidates, updated in place.

    Returns:
        Counters for the run.

    """
    stats = LinkStats(mentions=len(mentions))
    index: dict[tuple[str, str], list[Toponym]] = defaultdict(list)
    for record in (*toponyms, *candidates):
        for key in _keys_of(record):
            index[key].append(record)

    for mention in mentions:
        municipality = comparison_key(mention.municipality or "")
        key = (municipality, comparison_key(mention.place_name))
        targets = index.get(key)
        if not targets:
            stats.unmatched += 1
            continue
        for target in targets:
            _attach(mention, target, stats)

    for record in toponyms:
        if not record.disaster_records:
            continue
        stats.places_with_records += 1
        before = record.evidence_level
        apply_scores(record)
        if record.evidence_level > before:
            stats.raised_to_level_3 += 1
    stats.candidates_with_records = sum(1 for item in candidates if item.disaster_records)
    return stats
