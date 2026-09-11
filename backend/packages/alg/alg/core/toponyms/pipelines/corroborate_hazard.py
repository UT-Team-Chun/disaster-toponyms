"""Check evidence-backed toponyms against present-day hazard designations.

This says what the current hazard maps show at a place, which is a different
question from what historical sources say about its name. The two are reported
side by side so a reader can see when the old warning and the modern zoning
agree, and when they do not.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from gateways.gsi.models.monument import DisasterMonument
from gateways.gsi.operations.hazard_tile import sample_hazard

from alg.models.toponym import Toponym

#: Monuments within this distance are treated as commemorating the same place.
MONUMENT_RADIUS_KM = 3.0
EARTH_RADIUS_KM = 6371.0
_MAX_MONUMENTS = 5


@dataclass
class CorroborationStats:
    """Counters describing one corroboration run."""

    sampled: int = 0
    in_any_zone: int = 0
    with_monument: int = 0
    skipped_no_location: int = 0
    failures: list[str] = field(default_factory=list)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance between two coordinates in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = phi2 - phi1
    delta_lambda = math.radians(lon2 - lon1)
    inner = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(inner))


def nearby_monuments(
    toponym: Toponym,
    monuments: list[DisasterMonument],
    *,
    radius_km: float = MONUMENT_RADIUS_KM,
) -> list[DisasterMonument]:
    """Find the disaster monuments standing near a toponym.

    Args:
        toponym: Record with a resolved location.
        monuments: All monuments in the dataset.
        radius_km: Search radius.

    Returns:
        The closest monuments inside the radius, nearest first.

    """
    if toponym.location is None:
        return []
    origin = (toponym.location.lat, toponym.location.lon)
    scored: list[tuple[float, DisasterMonument]] = []
    for monument in monuments:
        distance = haversine_km(origin[0], origin[1], monument.lat, monument.lon)
        if distance <= radius_km:
            scored.append((distance, monument))
    scored.sort(key=lambda pair: pair[0])
    return [monument for _, monument in scored[:_MAX_MONUMENTS]]


def corroborate(
    toponyms: list[Toponym],
    monuments: list[DisasterMonument],
    *,
    sample_zones: bool = True,
    sampled_at: str | None = None,
) -> CorroborationStats:
    """Attach hazard-zone flags and nearby monuments to every record in place.

    Args:
        toponyms: Records to annotate.
        monuments: Monument dataset used for the proximity check.
        sample_zones: Whether to query the hazard tile service.
        sampled_at: Timestamp recorded on each sample.

    Returns:
        Counters for the run.

    """
    stats = CorroborationStats()
    for toponym in toponyms:
        if toponym.location is None:
            stats.skipped_no_location += 1
            continue

        found = nearby_monuments(toponym, monuments)
        if found:
            stats.with_monument += 1
            toponym.hazard_corroboration.nearest_monument_ids = [
                monument.monument_id for monument in found
            ]

        if not sample_zones:
            continue
        try:
            sample = sample_hazard(toponym.location.lat, toponym.location.lon)
        except (OSError, ValueError) as error:  # pragma: no cover - network dependent
            stats.failures.append(f"{toponym.id}: {error}")
            continue

        corroboration = toponym.hazard_corroboration
        corroboration.debris_flow_zone = sample.debris_flow_zone
        corroboration.steep_slope_zone = sample.steep_slope_zone
        corroboration.landslide_zone = sample.landslide_zone
        corroboration.flood_zone = sample.flood_zone
        corroboration.tsunami_zone = sample.tsunami_zone
        corroboration.storm_surge_zone = sample.storm_surge_zone
        corroboration.avalanche_risk = sample.avalanche_risk
        corroboration.sampled_at = sampled_at
        stats.sampled += 1
        if sample.any_zone():
            stats.in_any_zone += 1
    return stats
