"""Serialise toponyms and monuments into the static files the frontend loads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gateways.gsi.models.monument import DisasterMonument

from alg.models.area import MatchedArea
from alg.models.toponym import Toponym


def toponym_feature(toponym: Toponym) -> dict[str, Any] | None:
    """Convert a toponym into a slim GeoJSON feature.

    Only the fields needed for map styling and filtering are inlined; the full
    evidence list is served separately from ``details/<id>.json``.

    Args:
        toponym: Record with a resolved location.

    Returns:
        A GeoJSON feature, or None when the record has no coordinate.

    """
    if toponym.location is None:
        return None
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                round(toponym.location.lon, 6),
                round(toponym.location.lat, 6),
            ],
        },
        "properties": {
            "id": toponym.id,
            "name": toponym.name,
            "reading": toponym.reading,
            "pref": toponym.admin.pref,
            "prefCode": toponym.admin.pref_code,
            "municipality": toponym.admin.municipality,
            "hazardTypes": list(toponym.hazard_types),
            "evidenceLevel": toponym.evidence_level,
            "originLevel": toponym.origin_level,
            "hasRecord": toponym.has_disaster_record(),
            "recordRelation": toponym.record_relation(),
            "status": toponym.status,
            "disputed": toponym.disputed,
            "precision": toponym.location.precision,
            "areaKey": toponym.area_key,
            "elements": [ref.element_id for ref in toponym.elements],
            "summary": toponym.etymology_summary,
            "zones": toponym.hazard_corroboration.designated_zones(),
            "dataset": toponym.dataset,
        },
    }


def to_feature_collection(toponyms: list[Toponym]) -> dict[str, Any]:
    """Build a GeoJSON FeatureCollection from toponyms that have coordinates."""
    features = [feature for feature in map(toponym_feature, toponyms) if feature is not None]
    return {"type": "FeatureCollection", "features": features}


def monument_feature(monument: DisasterMonument) -> dict[str, Any]:
    """Convert a disaster monument into a GeoJSON feature."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [round(monument.lon, 6), round(monument.lat, 6)],
        },
        "properties": {
            "id": monument.monument_id,
            "name": monument.name,
            "erectedYear": monument.erected_year,
            "address": monument.address,
            "disasterName": monument.disaster_name,
            "disasterKind": monument.disaster_kind,
            "lore": monument.lore,
        },
    }


def monuments_feature_collection(monuments: list[DisasterMonument]) -> dict[str, Any]:
    """Build a GeoJSON FeatureCollection of disaster monuments."""
    return {
        "type": "FeatureCollection",
        "features": [monument_feature(monument) for monument in monuments],
    }


def write_json(path: Path, payload: Any) -> int:  # noqa: ANN401
    """Write a JSON payload with stable formatting.

    Args:
        path: Destination file; parent directories are created.
        payload: Any JSON-serialisable object.

    Returns:
        Number of bytes written.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    path.write_text(text + "\n", encoding="utf-8")
    return len(text) + 1


def area_feature(area: MatchedArea) -> dict[str, Any]:
    """Convert a matched census area into a GeoJSON polygon feature.

    Args:
        area: A matched census area.

    Returns:
        A GeoJSON feature whose properties name the records it covers.

    """
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[list(point) for point in ring] for ring in area.rings],
        },
        "properties": {
            "key": area.key_code,
            "name": area.name,
            "pref": area.pref_name,
            "prefCode": area.pref_code,
            "municipality": area.municipality_name,
            "areaM2": area.area_m2,
            "population": area.population,
            "toponymIds": area.toponym_ids,
        },
    }


def areas_feature_collection(areas: list[MatchedArea]) -> dict[str, Any]:
    """Build a GeoJSON FeatureCollection of census areas."""
    return {
        "type": "FeatureCollection",
        "features": [area_feature(area) for area in areas],
    }
