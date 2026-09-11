"""Screen the nationwide address table for names that match the element dictionary.

These records are level-0: the spelling matches a known element and nothing
more. They are kept separate from the evidence-backed dataset and are hidden by
default in the viewer, because a hollow called 久保 is not a warning until a
source says so. Only elements specific enough to be worth showing are used.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from alg.core.toponyms.tools.element_matcher import match_elements, max_specificity
from alg.core.toponyms.tools.geocode import in_japan
from alg.core.toponyms.tools.ids import make_toponym_id
from alg.core.toponyms.tools.normalize import comparison_key
from alg.models.element import ElementDictionary
from alg.models.hazard import HazardType
from alg.models.toponym import AdminArea, ElementRef, Evidence, Location, Toponym

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
    """One address-table row that matched the element dictionary."""

    name: str
    reading: str | None
    admin: AdminArea
    location: Location
    elements: list[ElementRef]
    hazards: list[HazardType]


def _candidate_record(row: CandidateRow) -> Toponym:
    """Build one level-0 candidate record."""
    element_labels = "・".join(ref.element_id for ref in row.elements[:3])
    return Toponym(
        id=make_toponym_id(row.name, row.admin, salt="candidate"),
        name=row.name,
        reading=row.reading,
        status="current",
        admin=row.admin,
        hazard_types=row.hazards,
        elements=row.elements,
        etymology_summary=f"要素辞書に一致（{element_labels}）。出典による裏づけは未確認。",
        evidence=[
            Evidence(
                kind="pattern",
                source_id="geolonia_addresses",
                locator=None,
                quote=None,
                claim="全国住所データの表記が要素辞書に一致する（字面のみの候補）",
                level=0,
                extracted_by="human",
                quote_verified=False,
            ),
        ],
        evidence_level=0,
        location=row.location,
        dataset="candidates",
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
