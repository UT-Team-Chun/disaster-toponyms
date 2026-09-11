"""Attach the administrative area each place name sits in.

A hazard map is far more useful when it shows the extent a name covered than
when it shows a dot. Small-section (小字) boundaries are not published
nationwide, so the honest unit is the 町丁・字等 area from the census, which is
exactly the large section recorded on each record. The viewer labels the polygon
with the precision it actually represents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from gateways.estat.models.boundary import SmallAreaBoundary
from gateways.estat.operations.boundaries import download_prefecture, read_boundaries

from alg.core.toponyms.tools.geometry import count_points, ring_area, simplify_rings
from alg.core.toponyms.tools.normalize import comparison_key
from alg.models.area import MatchedArea
from alg.models.toponym import Toponym

#: A polygon is only worth drawing if it is not the whole municipality.
MAX_RINGS_PER_AREA = 8


@dataclass
class AreaStats:
    """Counters describing one area-matching run."""

    prefectures: int = 0
    areas_read: int = 0
    matched_records: int = 0
    unmatched_records: int = 0
    areas_kept: int = 0
    points_before: int = 0
    points_after: int = 0
    messages: list[str] = field(default_factory=list)


def _index_by_name(
    boundaries: list[SmallAreaBoundary],
) -> dict[tuple[str, str], SmallAreaBoundary]:
    """Index boundaries by folded municipality and area name."""
    index: dict[tuple[str, str], SmallAreaBoundary] = {}
    for boundary in boundaries:
        key = (comparison_key(boundary.municipality_name), comparison_key(boundary.name))
        index.setdefault(key, boundary)
    return index


def _candidate_names(toponym: Toponym) -> list[str]:
    """Return the names to try against the boundary index, best first."""
    names = [toponym.admin.oaza, toponym.admin.koaza, toponym.name]
    return [name for name in names if name]


def attach_areas(
    toponyms: list[Toponym],
    *,
    cache_dir: Path,
    tolerance: float,
    use_network: bool = True,
) -> tuple[list[MatchedArea], AreaStats]:
    """Find the census area each record belongs to.

    Args:
        toponyms: Records with administrative context.
        cache_dir: Directory holding the downloaded boundary shapefiles.
        tolerance: Polygon simplification tolerance in degrees.
        use_network: Allow downloading boundary archives that are not cached.

    Returns:
        The polygons to publish and the counters for the run.

    """
    stats = AreaStats()
    by_pref: dict[str, list[Toponym]] = {}
    for toponym in toponyms:
        code = toponym.admin.pref_code
        if code:
            by_pref.setdefault(code, []).append(toponym)

    matched: dict[str, MatchedArea] = {}
    for pref_code, records in sorted(by_pref.items()):
        shp_path = next(iter(sorted((cache_dir / pref_code).glob("*.shp"))), None)
        if shp_path is None:
            if not use_network:
                stats.messages.append(f"{pref_code}: 境界データ未取得のため省略")
                continue
            try:
                shp_path = download_prefecture(pref_code, cache_dir)
            except (OSError, ValueError) as error:  # pragma: no cover - network dependent
                stats.messages.append(f"{pref_code}: 境界データを取得できません ({error})")
                continue

        boundaries = read_boundaries(shp_path)
        stats.prefectures += 1
        stats.areas_read += len(boundaries)
        index = _index_by_name(boundaries)

        for record in records:
            boundary = next(
                (
                    index[key]
                    for key in (
                        (comparison_key(record.admin.municipality or ""), comparison_key(name))
                        for name in _candidate_names(record)
                    )
                    if key in index
                ),
                None,
            )
            if boundary is None:
                stats.unmatched_records += 1
                continue

            stats.matched_records += 1
            record.area_key = boundary.key_code
            existing = matched.get(boundary.key_code)
            if existing is None:
                rings = sorted(boundary.rings, key=ring_area, reverse=True)[:MAX_RINGS_PER_AREA]
                stats.points_before += count_points(rings)
                simplified = simplify_rings(rings, tolerance)
                stats.points_after += count_points(simplified)
                existing = MatchedArea(
                    key_code=boundary.key_code,
                    pref_code=boundary.pref_code,
                    pref_name=boundary.pref_name,
                    municipality_name=boundary.municipality_name,
                    name=boundary.name,
                    area_m2=boundary.area_m2,
                    population=boundary.population,
                    rings=simplified,
                )
                matched[boundary.key_code] = existing
            existing.toponym_ids.append(record.id)

    stats.areas_kept = len(matched)
    return list(matched.values()), stats
