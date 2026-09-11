"""Tests for reading the NIHU historical place-name archive."""

import csv
import io
import zipfile
from pathlib import Path

import pytest

from gateways.nihu.operations.gazetteer import load_historical_places

PLACES = [
    ["ID", "地名", "属性", "形状", "緯度", "経度", "緯度2", "経度2", "出典", "出典詳細", "備考"],
    [
        "10000001",
        "守江",
        "5",
        "1",
        "33.4222",
        "131.6636",
        "",
        "",
        "大日本地名辞書",
        "4巻 20頁",
        "",
    ],
    [
        "10000002",
        "小熊",
        "8",
        "1",
        "33.4",
        "131.6",
        "",
        "",
        "大日本地名辞書",
        "4巻 20頁 (守江 )",
        "",
    ],
    [
        "40000001",
        "下北",
        "8",
        "1",
        "41.3",
        "141.1",
        "",
        "",
        "旧5万分の1地形図",
        "泊 (1915/06/30)",
        "",
    ],
]
PARENTS = [
    ["ID", "地名ID", "地名", "上位地名ID", "上位地名", "階層種別", "備考"],
    ["1", "10000001", "守江", "9", "豊後", "国", ""],
    ["2", "10000001", "守江", "9", "速見郡", "郡", ""],
    ["3", "40000001", "下北", "71", "青森県", "都道府県名", ""],
]
ALIASES = [
    ["ID", "地名ID", "地名", "別名", "種別", "備考"],
    ["1", "10000001", "守江", "モリエ", "ヨミ", ""],
    ["2", "10000001", "守江", "守江", "旧字原記載", ""],
]
ATTRIBUTES = [
    ["番号", "区分", "属性", "上位属性"],
    ["5", "行政地名", "村", "1"],
    ["8", "行政地名", "字", "1"],
]


def _csv(rows: list[list[str]]) -> bytes:
    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


@pytest.fixture
def archive(tmp_path: Path) -> Path:
    path = tmp_path / "nihu.zip"
    with zipfile.ZipFile(path, "w") as handle:
        # Member names are stored in CP932 without the UTF-8 flag, exactly as the
        # published archive does, so the reader has to recover them.
        for name, rows in (
            ("地名.txt", PLACES),
            ("地名_上位地名.txt", PARENTS),
            ("地名_別名.txt", ALIASES),
            ("地名_属性.txt", ATTRIBUTES),
        ):
            handle.writestr(name.encode("cp932").decode("cp437"), _csv(rows))
    return path


def test_every_entry_is_read_with_its_hierarchy(archive: Path):
    places = {place.place_id: place for place in load_historical_places(archive)}
    assert len(places) == 3
    moriye = places["10000001"]
    assert moriye.province == "豊後"
    assert moriye.district == "速見郡"
    assert moriye.attribute == "村"
    assert moriye.category == "行政地名"
    assert moriye.readings == ["モリエ"]
    assert moriye.volume == 4
    assert moriye.page == 20
    assert moriye.has_location()


def test_an_entry_described_under_another_names_its_heading(archive: Path):
    places = {place.place_id: place for place in load_historical_places(archive)}
    assert places["10000002"].parent_entry == "守江"


def test_the_source_filter_keeps_only_one_half(archive: Path):
    places = load_historical_places(archive, sources=frozenset({"大日本地名辞書"}))
    assert {place.place_id for place in places} == {"10000001", "10000002"}


def test_a_prefecture_is_read_from_the_map_half(archive: Path):
    places = {place.place_id: place for place in load_historical_places(archive)}
    assert places["40000001"].prefecture == "青森県"


def test_an_archive_without_the_expected_members_is_rejected(tmp_path: Path):
    path = tmp_path / "empty.zip"
    with zipfile.ZipFile(path, "w") as handle:
        handle.writestr("readme.txt", b"nothing here")
    with pytest.raises(FileNotFoundError):
        load_historical_places(path)
