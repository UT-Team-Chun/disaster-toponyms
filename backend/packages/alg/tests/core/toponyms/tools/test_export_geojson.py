"""Tests for the static output serialisation."""

import json
from pathlib import Path

from alg.core.toponyms.tools.export_geojson import (
    to_feature_collection,
    toponym_feature,
    write_json,
)
from alg.models.toponym import AdminArea, Location, Toponym


def _record(**overrides: object) -> Toponym:
    payload: dict[str, object] = {
        "id": "10-abc",
        "name": "梅ヶ久保",
        "reading": "ウメガクボ",
        "admin": AdminArea(pref="群馬県", pref_code="10", municipality="桐生市"),
        "location": Location(lat=36.467, lon=139.339, precision="oaza"),
        "hazard_types": ["slope_failure"],
        "evidence_level": 2,
    }
    payload.update(overrides)
    return Toponym.model_validate(payload)


def test_feature_has_lon_lat_order():
    feature = toponym_feature(_record())
    assert feature is not None
    assert feature["geometry"]["coordinates"] == [139.339, 36.467]


def test_records_without_a_location_are_skipped():
    assert toponym_feature(_record(location=None)) is None
    collection = to_feature_collection([_record(), _record(location=None)])
    assert len(collection["features"]) == 1


def test_properties_carry_what_the_map_needs():
    feature = toponym_feature(_record())
    assert feature is not None
    properties = feature["properties"]
    assert properties["id"] == "10-abc"
    assert properties["evidenceLevel"] == 2
    assert properties["precision"] == "oaza"
    assert properties["disputed"] is False


def test_write_json_is_utf8_and_unescaped(tmp_path: Path):
    path = tmp_path / "nested" / "out.json"
    size = write_json(path, {"name": "梅ヶ久保"})
    text = path.read_text(encoding="utf-8")
    assert "梅ヶ久保" in text
    assert size == len(text)
    assert json.loads(text)["name"] == "梅ヶ久保"
