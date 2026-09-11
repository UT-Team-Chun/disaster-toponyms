"""Tests for parsing the natural disaster monument dataset."""

import json
from pathlib import Path
from typing import Any

from gateways.gsi.operations.monuments import load_monuments

FEATURE = {
    "type": "Feature",
    "properties": {
        "ID": "01202-001",
        "碑名": "遭難犠牲者慰霊碑",
        "建立年": "1975",
        "所在地": "北海道函館市川汲町2085番地",
        "災害名": "昭和48年集中豪雨(1973年9月24日)",
        "災害種別": "洪水・土砂災害",
        "伝承内容": "総雨量383mmという記録的な豪雨により河川の氾濫が発生した。",
        "公開日": "2021/3/3",
    },
    "geometry": {"type": "Point", "coordinates": [140.96034, 41.891005]},
}


def _write(tmp_path: Path, features: list[dict[str, Any]]) -> Path:
    path = tmp_path / "monuments.geojson"
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )
    return path


def test_reads_every_field(tmp_path: Path) -> None:
    (monument,) = load_monuments(_write(tmp_path, [FEATURE]))
    assert monument.monument_id == "01202-001"
    assert monument.name == "遭難犠牲者慰霊碑"
    assert monument.disaster_kind == "洪水・土砂災害"
    assert monument.lore is not None
    assert monument.lat == 41.891005
    assert monument.lon == 140.96034


def test_blank_fields_become_none(tmp_path: Path) -> None:
    feature = json.loads(json.dumps(FEATURE))
    feature["properties"]["建立年"] = " "
    (monument,) = load_monuments(_write(tmp_path, [feature]))
    assert monument.erected_year is None


def test_features_without_coordinates_are_skipped(tmp_path: Path) -> None:
    feature = json.loads(json.dumps(FEATURE))
    feature["geometry"] = {"type": "Point", "coordinates": []}
    assert load_monuments(_write(tmp_path, [feature])) == []
