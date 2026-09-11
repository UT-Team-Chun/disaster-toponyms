"""Tests for screening place-name tables against the element dictionary."""

import pytest
from gateways.nihu.models.place import HistoricalPlace

from alg.core.toponyms.pipelines import generate_candidates
from alg.core.toponyms.pipelines.generate_candidates import screen_old_maps
from alg.core.toponyms.tools.geocode import AddressPoint, GeoloniaIndex
from alg.core.toponyms.tools.normalize import comparison_key
from alg.models.element import ElementDictionary, ToponymElement

DICTIONARY = ElementDictionary(
    elements=[
        ToponymElement(
            id="januke",
            label="ジャヌケ（蛇抜）",
            surfaces=["蛇抜"],
            readings=["ジャヌケ"],
            meaning="土石流",
            hazard_types=["debris_flow"],
            specificity=0.95,
        ),
    ],
)

GRID_CELL = (356, 1376)


@pytest.fixture
def address_index(monkeypatch: pytest.MonkeyPatch) -> GeoloniaIndex:
    """Stand in for the nationwide address table with one town and two names."""
    index = GeoloniaIndex()
    index.grid[GRID_CELL] = [
        AddressPoint(
            pref="長野県",
            municipality="木曽郡南木曽町",
            municipality_code="20432",
            oaza="読書",
            lat=35.6,
            lon=137.6,
        ),
    ]
    index.names_by_municipality[(comparison_key("長野県"), comparison_key("木曽郡南木曽町"))] = {
        comparison_key("読書"),
        comparison_key("蛇抜沢"),
    }
    monkeypatch.setattr(generate_candidates, "get_geolonia_index", lambda: index)
    return index


def _place(name: str, attribute: str = "字", source: str = "旧5万分の1地形図") -> HistoricalPlace:
    return HistoricalPlace(
        place_id=f"40-{name}",
        name=name,
        attribute=attribute,
        category="行政地名",
        lat=35.6,
        lon=137.6,
        source=source,
        prefecture="長野県",
    )


def test_only_the_old_map_half_is_screened(address_index: GeoloniaIndex):
    assert address_index.grid
    records, stats = screen_old_maps(
        [_place("蛇抜久保", source="大日本地名辞書")],
        DICTIONARY,
    )
    assert records == []
    assert stats.rows == 0


def test_a_vanished_name_becomes_a_historical_candidate(address_index: GeoloniaIndex):
    assert address_index.grid
    records, stats = screen_old_maps([_place("蛇抜久保")], DICTIONARY)
    assert stats.kept == 1
    record = records[0]
    assert record.status == "historical"
    assert record.evidence_level == 0
    assert record.admin.municipality == "木曽郡南木曽町"
    assert record.location is not None
    assert record.location.precision == "koaza"
    assert record.dataset == "old_maps"


def test_a_name_the_address_table_still_carries_is_not_duplicated(
    address_index: GeoloniaIndex,
):
    assert address_index.grid
    records, _stats = screen_old_maps([_place("蛇抜沢")], DICTIONARY)
    assert records == []


def test_a_shrine_is_not_a_warning(address_index: GeoloniaIndex):
    assert address_index.grid
    records, _stats = screen_old_maps(
        [_place("蛇抜神社", attribute="神社")],
        DICTIONARY,
    )
    assert records == []
