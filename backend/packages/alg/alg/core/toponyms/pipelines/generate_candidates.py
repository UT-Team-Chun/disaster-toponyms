"""Screen place-name tables for names that match the element dictionary.

These records are level-0: the spelling matches a known element and nothing
more. They are kept separate from the evidence-backed dataset, because a hollow
called 久保 is not a warning until a source says so. Only elements specific
enough to be worth showing are used.

Two tables are screened. The nationwide address table covers the names in use
today. The place names read off the old 1:50,000 maps cover the ones that are
not: small sections absorbed by post-war mergers, whose warning disappeared from
the address system along with the name.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from gateways.nihu.models.place import OLD_MAP_SOURCE, HistoricalPlace

from alg.core.toponyms.tools.element_matcher import match_elements, max_specificity
from alg.core.toponyms.tools.geocode import get_geolonia_index, in_japan
from alg.core.toponyms.tools.ids import make_toponym_id
from alg.core.toponyms.tools.normalize import comparison_key
from alg.core.toponyms.tools.prefectures import pref_code as pref_code_of
from alg.models.element import ElementDictionary
from alg.models.hazard import HazardType
from alg.models.toponym import (
    AdminArea,
    ElementRef,
    Evidence,
    Location,
    LocationPrecision,
    Toponym,
)

#: Lowest element specificity worth listing as a candidate.
DEFAULT_SPECIFICITY_THRESHOLD = 0.55


@dataclass
class CandidateStats:
    """Counters describing one screening run."""

    rows: int = 0
    matched: int = 0
    kept: int = 0
    by_pref: dict[str, int] = field(default_factory=dict)
    by_element: dict[str, int] = field(default_factory=dict)


_CHOME_SUFFIX = re.compile(
    r"(?:[一二三四五六七八九十〇\d]+丁目|[北南東西][一二三四五六七八九十〇\d]+条)+$"
)


def _series_key(admin: AdminArea, name: str) -> str:
    """Collapse a numbered block series into one candidate.

    A single district such as 厚別北一条一丁目 appears in the address table once
    per block, which would otherwise flood the map with dozens of identical
    candidates.

    Args:
        admin: Administrative context of the row.
        name: Place-name spelling of the row.

    Returns:
        Key shared by every block of the same district.

    """
    base = _CHOME_SUFFIX.sub("", comparison_key(name)) or comparison_key(name)
    return f"{admin.pref_code}|{admin.municipality_code}|{base}"


@dataclass(frozen=True)
class CandidateRow:
    """One row of a place-name table that matched the element dictionary."""

    name: str
    reading: str | None
    admin: AdminArea
    location: Location
    elements: list[ElementRef]
    hazards: list[HazardType]
    status: str = "current"
    source_id: str = "geolonia_addresses"
    claim: str = "全国住所データの表記が要素辞書に一致する（字面のみの候補）"
    dataset: str = "candidates"
    salt: str = "candidate"


def _candidate_record(row: CandidateRow) -> Toponym:
    """Build one level-0 candidate record."""
    element_labels = "・".join(ref.element_id for ref in row.elements[:3])
    return Toponym(
        id=make_toponym_id(row.name, row.admin, salt=row.salt),
        name=row.name,
        reading=row.reading,
        status=row.status,  # type: ignore[arg-type]
        admin=row.admin,
        hazard_types=row.hazards,
        elements=row.elements,
        etymology_summary=f"要素辞書に一致（{element_labels}）。出典による裏づけは未確認。",
        evidence=[
            Evidence(
                kind="pattern",
                source_id=row.source_id,
                locator=None,
                quote=None,
                claim=row.claim,
                level=0,
                extracted_by="human",
                quote_verified=False,
            ),
        ],
        evidence_level=0,
        location=row.location,
        dataset=row.dataset,
    )


def _row_to_candidate(
    row: dict[str, str],
    dictionary: ElementDictionary,
    threshold: float,
) -> CandidateRow | None:
    """Turn one CSV row into a candidate, or None when it does not qualify."""
    koaza = row["小字・通称名"].strip()
    oaza = row["大字町丁目名"].strip()
    name = koaza or oaza
    if not name:
        return None

    matches = match_elements(name, None, dictionary, surface_only=True)
    if not matches or max_specificity(matches) < threshold:
        return None

    try:
        lat = float(row["緯度"])
        lon = float(row["経度"])
    except (TypeError, ValueError):
        return None
    if not in_japan(lat, lon):
        return None

    hazards: list[HazardType] = []
    for match in matches:
        hazards.extend(hazard for hazard in match.element.hazard_types if hazard not in hazards)
    return CandidateRow(
        name=name,
        reading=None if koaza else (row["大字町丁目名カナ"].strip() or None),
        admin=AdminArea(
            pref=row["都道府県名"],
            pref_code=row["都道府県コード"],
            municipality=row["市区町村名"],
            municipality_code=row["市区町村コード"],
            oaza=oaza or None,
            koaza=koaza or None,
        ),
        location=Location(
            lat=lat,
            lon=lon,
            precision="koaza" if koaza else "oaza",
            geocode_source="geolonia",
        ),
        elements=[match.to_ref() for match in matches],
        hazards=hazards,
    )


def screen_address_table(
    csv_path: Path,
    dictionary: ElementDictionary,
    *,
    threshold: float = DEFAULT_SPECIFICITY_THRESHOLD,
    pref_codes: frozenset[str] | None = None,
    limit: int | None = None,
) -> tuple[list[Toponym], CandidateStats]:
    """Find address-table entries whose spelling matches a specific element.

    Args:
        csv_path: Path to the Geolonia nationwide address CSV.
        dictionary: Element dictionary to match against.
        threshold: Minimum element specificity required to keep a row.
        pref_codes: Restrict the sweep to these prefecture codes.
        limit: Stop after this many kept candidates.

    Returns:
        The candidate records and the counters for the run.

    """
    stats = CandidateStats()
    records: dict[str, Toponym] = {}
    seen_series: set[str] = set()
    if not csv_path.exists():
        return [], stats

    with csv_path.open(encoding="utf-8", newline="") as handle:
        for csv_row in csv.DictReader(handle):
            stats.rows += 1
            pref_code = csv_row["都道府県コード"]
            if pref_codes is not None and pref_code not in pref_codes:
                continue

            candidate = _row_to_candidate(csv_row, dictionary, threshold)
            if candidate is None:
                continue
            stats.matched += 1

            series = _series_key(candidate.admin, candidate.name)
            if series in seen_series:
                continue
            seen_series.add(series)

            record = _candidate_record(candidate)
            records[record.id] = record
            stats.kept += 1
            stats.by_pref[pref_code] = stats.by_pref.get(pref_code, 0) + 1
            for ref in record.elements:
                stats.by_element[ref.element_id] = stats.by_element.get(ref.element_id, 0) + 1
            if limit is not None and stats.kept >= limit:
                break

    return list(records.values()), stats


#: How precisely the old maps locate each kind of name.
OLD_MAP_PRECISION: Final[dict[str, LocationPrecision]] = {
    "字": "koaza",
    "町": "oaza",
    "村": "village",
    "郷・里": "village",
    "荘園・新田": "village",
}

#: Kinds read off the old maps that are worth screening. A shrine or a castle
#: named after a hollow warns nobody; an absorbed small section does.
OLD_MAP_ATTRIBUTES: Final[frozenset[str]] = frozenset(
    {"字", "村", "町", "郷・里", "荘園・新田", "その他（行政地名）", "谷", "浜", "坂"},
)

OLD_MAP_SOURCE_ID: Final = "nihu_rekishi_chimei"
OLD_MAP_CLAIM: Final = "旧5万分の1地形図の地名表記が要素辞書に一致する（字面のみの候補）"


def _old_map_candidate(
    place: HistoricalPlace,
    dictionary: ElementDictionary,
    threshold: float,
) -> CandidateRow | None:
    """Turn one old-map place name into a candidate, or None when it does not qualify."""
    if place.attribute not in OLD_MAP_ATTRIBUTES:
        return None
    if place.lat is None or place.lon is None or not in_japan(place.lat, place.lon):
        return None

    reading = place.readings[0] if place.readings else None
    matches = match_elements(place.name, None, dictionary, surface_only=True)
    if not matches or max_specificity(matches) < threshold:
        return None

    index = get_geolonia_index()
    nearest = index.nearest_address(place.lat, place.lon)
    if nearest is None:
        return None
    # A name the address table still carries is already a candidate; keeping it
    # twice would double-count it on the map.
    if index.has_name(nearest.pref, nearest.municipality, place.name):
        return None

    hazards: list[HazardType] = []
    for match in matches:
        hazards.extend(hazard for hazard in match.element.hazard_types if hazard not in hazards)
    return CandidateRow(
        name=place.name,
        reading=reading,
        admin=AdminArea(
            pref=nearest.pref,
            pref_code=pref_code_of(nearest.pref),
            municipality=nearest.municipality,
            municipality_code=nearest.municipality_code,
            oaza=nearest.oaza,
            koaza=place.name,
            province=place.province,
            district=place.district,
        ),
        location=Location(
            lat=place.lat,
            lon=place.lon,
            precision=OLD_MAP_PRECISION.get(place.attribute or "", "feature"),
            geocode_source="nihu:旧5万分の1地形図",
        ),
        elements=[match.to_ref() for match in matches],
        hazards=hazards,
        status="historical",
        source_id=OLD_MAP_SOURCE_ID,
        claim=OLD_MAP_CLAIM,
        dataset="old_maps",
        salt="old_map",
    )


def screen_old_maps(
    places: list[HistoricalPlace],
    dictionary: ElementDictionary,
    *,
    threshold: float = DEFAULT_SPECIFICITY_THRESHOLD,
    pref_codes: frozenset[str] | None = None,
) -> tuple[list[Toponym], CandidateStats]:
    """Find vanished small-section names whose spelling matches a specific element.

    Args:
        places: Historical place names, normally the old-map half of the dataset.
        dictionary: Element dictionary to match against.
        threshold: Minimum element specificity required to keep a name.
        pref_codes: Restrict the sweep to these prefecture codes.

    Returns:
        The candidate records and the counters for the run.

    """
    stats = CandidateStats()
    records: dict[str, Toponym] = {}
    seen: set[tuple[str, str, str]] = set()
    for place in places:
        if place.source != OLD_MAP_SOURCE:
            continue
        stats.rows += 1
        candidate = _old_map_candidate(place, dictionary, threshold)
        if candidate is None:
            continue
        stats.matched += 1
        code = candidate.admin.pref_code or "00"
        if pref_codes is not None and code not in pref_codes:
            continue
        # The same hamlet is read off more than one map sheet, so a name is kept
        # once per municipality rather than once per sheet.
        key = (
            code,
            comparison_key(candidate.admin.municipality or ""),
            comparison_key(candidate.name),
        )
        if key in seen:
            continue
        seen.add(key)
        record = _candidate_record(candidate)
        if record.id in records:
            continue
        records[record.id] = record
        stats.kept += 1
        stats.by_pref[code] = stats.by_pref.get(code, 0) + 1
        for ref in record.elements:
            stats.by_element[ref.element_id] = stats.by_element.get(ref.element_id, 0) + 1
    return list(records.values()), stats
