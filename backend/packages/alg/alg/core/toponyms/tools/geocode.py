"""Resolve representative coordinates for place names.

Small-section names (小字) are not served by the GSI geocoder, so the resolver
walks a fallback chain and always records how precise the answer is.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Final

from gateways.gsi.operations.address_search import search_address

from alg.core.toponyms.tools.normalize import comparison_key
from alg.core.toponyms.tools.paths import get_paths
from alg.models.toponym import AdminArea, Location, LocationPrecision

#: Suffixes that mark a natural feature the national geocoder actually knows.
#: Small-section names are absent from it, so querying them one by one only
#: costs time and returns the enclosing town under a misleading precision.
NATURAL_FEATURE_SUFFIXES: Final[tuple[str, ...]] = (
    "沢",
    "澤",
    "山",
    "川",
    "谷",
    "峠",
    "池",
    "滝",
    "岳",
    "峰",
    "島",
    "岬",
    "浜",
    "湖",
    "沼",
)

# Rough bounding box of the Japanese archipelago, used to reject bad geocodes.
LAT_MIN, LAT_MAX = 20.0, 46.5
LON_MIN, LON_MAX = 122.0, 154.0


def in_japan(lat: float, lon: float) -> bool:
    """Return True when the coordinate falls inside the Japanese bounding box."""
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


@dataclass
class GeoloniaIndex:
    """Lookup tables built from the Geolonia nationwide address table."""

    by_oaza: dict[tuple[str, str, str], tuple[float, float]] = field(default_factory=dict)
    by_koaza: dict[tuple[str, str, str], tuple[float, float]] = field(default_factory=dict)
    by_municipality: dict[tuple[str, str], tuple[float, float]] = field(default_factory=dict)
    municipality_codes: dict[tuple[str, str], str] = field(default_factory=dict)

    def _exact(
        self,
        table: dict[tuple[str, str, str], tuple[float, float]],
        pref: str,
        municipality: str,
        names: tuple[str | None, ...],
    ) -> tuple[float, float] | None:
        """Look one name up in a section table, trying each spelling in turn."""
        for name in names:
            if not name:
                continue
            hit = table.get((pref, municipality, comparison_key(name)))
            if hit:
                return hit
        return None

    def _contained(
        self,
        pref: str,
        municipality: str,
        name_key: str,
    ) -> tuple[float, float] | None:
        """Match a record that spells the name as "<oaza><koaza>" in one string."""
        for (index_pref, index_muni, index_name), coordinate in self.by_oaza.items():
            if index_pref == pref and index_muni == municipality and index_name in name_key:
                return coordinate
        return None

    def lookup(
        self,
        admin: AdminArea,
        name: str,
    ) -> tuple[tuple[float, float], LocationPrecision] | None:
        """Find the most precise coordinate available for a record.

        Args:
            admin: Administrative context of the record.
            name: Place-name spelling to resolve.

        Returns:
            Tuple of (coordinate, precision) or None when nothing matched.

        """
        if not admin.pref or not admin.municipality:
            return None
        pref = comparison_key(admin.pref)
        municipality = comparison_key(admin.municipality)

        koaza_hit = self._exact(self.by_koaza, pref, municipality, (admin.koaza, name))
        if koaza_hit:
            return koaza_hit, "koaza"

        oaza_hit = self._exact(self.by_oaza, pref, municipality, (admin.oaza, name))
        if oaza_hit:
            return oaza_hit, "oaza"

        contained = self._contained(pref, municipality, comparison_key(name))
        if contained:
            return contained, "oaza"

        municipality_hit = self.by_municipality.get((pref, municipality))
        if municipality_hit:
            return municipality_hit, "municipality"
        return None


def _load_index(csv_path: Path) -> GeoloniaIndex:
    """Build the lookup tables from the Geolonia CSV."""
    index = GeoloniaIndex()
    sums: dict[tuple[str, str], tuple[float, float, int]] = {}
    with csv_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            try:
                lat = float(row["緯度"])
                lon = float(row["経度"])
            except (TypeError, ValueError):
                continue
            if not in_japan(lat, lon):
                continue
            pref = comparison_key(row["都道府県名"])
            municipality = comparison_key(row["市区町村名"])
            oaza = row["大字町丁目名"]
            koaza = row["小字・通称名"]

            index.municipality_codes.setdefault((pref, municipality), row["市区町村コード"])
            if oaza:
                index.by_oaza.setdefault((pref, municipality, comparison_key(oaza)), (lat, lon))
            if koaza:
                index.by_koaza.setdefault((pref, municipality, comparison_key(koaza)), (lat, lon))
            total_lat, total_lon, count = sums.get((pref, municipality), (0.0, 0.0, 0))
            sums[(pref, municipality)] = (total_lat + lat, total_lon + lon, count + 1)

    for key, (total_lat, total_lon, count) in sums.items():
        index.by_municipality[key] = (total_lat / count, total_lon / count)
    return index


@lru_cache(maxsize=1)
def get_geolonia_index() -> GeoloniaIndex:
    """Return the cached Geolonia index, or an empty index when the CSV is absent."""
    csv_path = get_paths().geolonia_csv
    if not csv_path.exists():
        return GeoloniaIndex()
    return _load_index(csv_path)


def geocode_via_gsi(query: str, *, require: str | None = None) -> Location | None:
    """Geocode a free-form place name through the GSI endpoint.

    The endpoint falls back to the enclosing town when a small-section name is
    unknown, so ``require`` lets the caller reject answers whose title does not
    actually contain the requested name.

    Args:
        query: Query string, ideally ``<pref><municipality><name>``.
        require: Name that must appear in the matched title.

    Returns:
        A location with ``point`` precision, or None when nothing matched.

    """
    required_key = comparison_key(require) if require else None
    for hit in search_address(query):
        if not in_japan(hit.lat, hit.lon):
            continue
        if required_key and required_key not in comparison_key(hit.title):
            continue
        return Location(
            lat=hit.lat,
            lon=hit.lon,
            precision="point",
            geocode_source=f"gsi:{hit.title}",
        )
    return None


def resolve_location(admin: AdminArea, name: str, *, use_network: bool = True) -> Location | None:
    """Resolve the best available coordinate for a place name.

    The chain is: the Geolonia small-section table, then an exact GSI match for
    names that look like a natural feature (蛇抜沢, 野毛山), then the Geolonia
    large-section table, then the municipality centroid. Small-section names the
    geocoder does not know fall back to the enclosing town, which is why the
    precision of the answer is always recorded alongside it.

    Args:
        admin: Administrative context.
        name: Place-name spelling.
        use_network: Allow the GSI network lookup.

    Returns:
        The best location found, or None.

    """
    index = get_geolonia_index()
    local = index.lookup(admin, name)
    if local is not None and local[1] == "koaza":
        (lat, lon), precision = local
        return Location(lat=lat, lon=lon, precision=precision, geocode_source="geolonia")

    if use_network and name.endswith(NATURAL_FEATURE_SUFFIXES):
        prefix = f"{admin.pref or ''}{admin.municipality or ''}"
        for query in (f"{prefix}{name}", name):
            if not query.strip():
                continue
            located = geocode_via_gsi(query, require=name)
            if located is not None:
                return located

    if local is not None:
        (lat, lon), precision = local
        return Location(lat=lat, lon=lon, precision=precision, geocode_source="geolonia")

    if use_network and admin.pref:
        # Last resort. A prefecture centroid is not a location for a place name,
        # so it is labelled as such and the viewer can filter it out.
        fallback = geocode_via_gsi(f"{admin.pref}{admin.municipality or ''}")
        if fallback is not None:
            fallback.precision = "municipality" if admin.municipality else "prefecture"
            return fallback
    return None
