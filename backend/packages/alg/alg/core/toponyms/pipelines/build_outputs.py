"""Write the static files the viewer loads.

The viewer is a static page, so the build emits one small file for the map, one
file per record for the evidence, and per-prefecture files for the level-0
candidates that are only fetched when the reader zooms in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gateways.gsi.models.monument import DisasterMonument

from alg.core.toponyms.tools.export_geojson import (
    areas_feature_collection,
    monuments_feature_collection,
    to_feature_collection,
    write_json,
)
from alg.models.area import MatchedArea
from alg.models.element import ElementDictionary
from alg.models.hazard import HAZARD_LABELS_JA
from alg.models.source import Source
from alg.models.toponym import EVIDENCE_LEVEL_LABELS_JA, Toponym

#: Upper bound for the file the map loads on first paint.
MAX_MAIN_GEOJSON_BYTES = 8 * 1024 * 1024
#: Level at or above which a record counts as documented rather than inferred.
DOCUMENTED_LEVEL = 2
#: Level meaning a documented origin is matched by a recorded disaster.
LEVEL_3 = 3


#: Directories written one file per record, which have to be pruned when a
#: record disappears. Without this, a place dropped by a stricter rule would
#: keep serving its old evidence page.
PER_RECORD_DIRS = ("details", "candidates", "areas")


@dataclass
class OutputReport:
    """Files written by one build, with their sizes."""

    files: list[str] = field(default_factory=list)
    bytes_written: int = 0
    removed: int = 0
    warnings: list[str] = field(default_factory=list)

    def record(self, path: Path, output_dir: Path, size: int) -> None:
        """Note one written file."""
        self.files.append(str(path.relative_to(output_dir)))
        self.bytes_written += size


def _prune_stale(output_dir: Path, report: OutputReport) -> None:
    """Delete per-record files this build did not write."""
    written = set(report.files)
    for name in PER_RECORD_DIRS:
        directory = output_dir / name
        if not directory.is_dir():
            continue
        for path in directory.iterdir():
            if path.is_file() and str(path.relative_to(output_dir)) not in written:
                path.unlink()
                report.removed += 1


def _detail_payload(toponym: Toponym) -> dict[str, Any]:
    """Serialise the full record served from ``details/<id>.json``."""
    payload = toponym.model_dump(mode="json", exclude_none=False)
    payload["evidenceLevelLabel"] = EVIDENCE_LEVEL_LABELS_JA.get(toponym.evidence_level, "")
    payload["hazardLabels"] = [
        HAZARD_LABELS_JA.get(hazard, hazard) for hazard in toponym.hazard_types
    ]
    return payload


def _stats_payload(
    toponyms: list[Toponym],
    candidates: list[Toponym],
    monuments: list[DisasterMonument],
    areas: list[MatchedArea],
) -> dict[str, Any]:
    """Aggregate the counts shown in the viewer's summary bar."""
    by_level: dict[str, int] = {}
    by_hazard: dict[str, int] = {}
    by_pref: dict[str, dict[str, int]] = {}
    by_element: dict[str, int] = {}
    by_relation: dict[str, int] = {}
    for toponym in toponyms:
        level = str(toponym.evidence_level)
        by_level[level] = by_level.get(level, 0) + 1
        for hazard in toponym.hazard_types:
            by_hazard[hazard] = by_hazard.get(hazard, 0) + 1
        for ref in toponym.elements:
            by_element[ref.element_id] = by_element.get(ref.element_id, 0) + 1
        relation = toponym.record_relation()
        if relation:
            by_relation[relation] = by_relation.get(relation, 0) + 1
        code = toponym.admin.pref_code or "00"
        bucket = by_pref.setdefault(code, {"total": 0, "documented": 0, "level3": 0})
        bucket["total"] += 1
        if toponym.evidence_level >= DOCUMENTED_LEVEL:
            bucket["documented"] += 1
        if toponym.evidence_level >= LEVEL_3:
            bucket["level3"] += 1

    candidates_by_pref: dict[str, int] = {}
    for candidate in candidates:
        code = candidate.admin.pref_code or "00"
        candidates_by_pref[code] = candidates_by_pref.get(code, 0) + 1

    areas_by_pref: dict[str, int] = {}
    for area in areas:
        code = area.pref_code or "00"
        areas_by_pref[code] = areas_by_pref.get(code, 0) + 1

    return {
        "toponymsTotal": len(toponyms),
        "candidatesTotal": len(candidates),
        "monumentsTotal": len(monuments),
        "disputedTotal": sum(1 for toponym in toponyms if toponym.disputed),
        "byLevel": by_level,
        "byHazard": by_hazard,
        "byPrefecture": by_pref,
        "byElement": by_element,
        "candidatesByPrefecture": candidates_by_pref,
        "areasTotal": len(areas),
        "areasByPrefecture": areas_by_pref,
        "withAreaTotal": sum(1 for toponym in toponyms if toponym.area_key),
        "withDisasterRecord": sum(1 for toponym in toponyms if toponym.has_disaster_record()),
        "candidatesWithRecord": sum(
            1 for candidate in candidates if candidate.has_disaster_record()
        ),
        "l3ByRelation": by_relation,
    }


@dataclass
class DatasetBundle:
    """Everything one build produces, ready to be written out."""

    toponyms: list[Toponym] = field(default_factory=list)
    candidates: list[Toponym] = field(default_factory=list)
    areas: list[MatchedArea] = field(default_factory=list)
    monuments: list[DisasterMonument] = field(default_factory=list)
    elements: ElementDictionary = field(default_factory=ElementDictionary)
    sources: list[Source] = field(default_factory=list)
    built_at: str = ""


def write_outputs(output_dir: Path, bundle: DatasetBundle) -> OutputReport:
    """Write every static file the viewer needs.

    Args:
        output_dir: Directory served by the frontend, usually ``public/data``.
        bundle: The records, dictionary, bibliography and build timestamp.

    Returns:
        The list of files written, with the total size.

    """
    toponyms = bundle.toponyms
    candidates = bundle.candidates
    areas = bundle.areas
    monuments = bundle.monuments
    elements = bundle.elements
    sources = bundle.sources
    built_at = bundle.built_at
    report = OutputReport()
    output_dir.mkdir(parents=True, exist_ok=True)

    main_path = output_dir / "toponyms.geojson"
    size = write_json(main_path, to_feature_collection(toponyms))
    report.record(main_path, output_dir, size)
    if size > MAX_MAIN_GEOJSON_BYTES:
        report.warnings.append(
            f"toponyms.geojson が {size} バイトで上限 {MAX_MAIN_GEOJSON_BYTES} を超えています",
        )

    monuments_path = output_dir / "monuments.geojson"
    size = write_json(monuments_path, monuments_feature_collection(monuments))
    report.record(monuments_path, output_dir, size)

    by_pref: dict[str, list[Toponym]] = {}
    for candidate in candidates:
        by_pref.setdefault(candidate.admin.pref_code or "00", []).append(candidate)
    for code, group in sorted(by_pref.items()):
        path = output_dir / "candidates" / f"{code}.geojson"
        size = write_json(path, to_feature_collection(group))
        report.record(path, output_dir, size)

    areas_by_pref: dict[str, list[MatchedArea]] = {}
    for area in areas:
        areas_by_pref.setdefault(area.pref_code or "00", []).append(area)
    for code, area_group in sorted(areas_by_pref.items()):
        path = output_dir / "areas" / f"{code}.geojson"
        size = write_json(path, areas_feature_collection(area_group))
        report.record(path, output_dir, size)

    # Candidates normally carry no evidence page, but one that a disaster record
    # was matched to has something to show, so it gets a detail file too.
    detailed = [*toponyms, *(item for item in candidates if item.has_disaster_record())]
    for toponym in detailed:
        path = output_dir / "details" / f"{toponym.id}.json"
        size = write_json(path, _detail_payload(toponym))
        report.record(path, output_dir, size)

    elements_path = output_dir / "elements.json"
    size = write_json(
        elements_path,
        {
            "elements": [element.model_dump(mode="json") for element in elements.elements],
            "hazardLabels": HAZARD_LABELS_JA,
            "evidenceLevelLabels": EVIDENCE_LEVEL_LABELS_JA,
        },
    )
    report.record(elements_path, output_dir, size)

    sources_path = output_dir / "sources.json"
    size = write_json(
        sources_path,
        {"sources": [source.model_dump(mode="json") for source in sources]},
    )
    report.record(sources_path, output_dir, size)

    stats_path = output_dir / "stats.json"
    size = write_json(stats_path, _stats_payload(toponyms, candidates, monuments, areas))
    report.record(stats_path, output_dir, size)

    meta_path = output_dir / "meta.json"
    size = write_json(
        meta_path,
        {
            "builtAt": built_at,
            "datasets": sorted({toponym.dataset for toponym in toponyms}),
            "attribution": [
                "地理院タイル（国土地理院）",
                "重ねるハザードマップ（国土交通省・国土地理院）",
                "自然災害伝承碑（国土地理院）",
                "Geolonia 住所データ（CC BY 4.0）",
                "歴史地名データ（人間文化研究機構・H-GIS研究会）",
                "吉田東伍『大日本地名辞書』二版（国立国会図書館デジタルコレクション）",
                "次世代デジタルライブラリー（国立国会図書館）",
            ],
        },
    )
    report.record(meta_path, output_dir, size)

    _prune_stale(output_dir, report)
    return report
