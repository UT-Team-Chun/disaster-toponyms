"""Tests for identifying a heading printed in pre-war characters."""

from gateways.nihu.models.place import HistoricalPlace

from alg.core.toponyms.tools.historical_index import (
    build_index,
    learn_character_mapping,
    spelling_pairs,
)


def _place(
    place_id: str,
    name: str,
    province: str,
    district: str | None = None,
    old_forms: list[str] | None = None,
    parent: str | None = None,
) -> HistoricalPlace:
    return HistoricalPlace(
        place_id=place_id,
        name=name,
        attribute="村",
        category="行政地名",
        lat=33.4,
        lon=131.6,
        source="大日本地名辞書",
        province=province,
        district=district,
        old_forms=old_forms or [],
        parent_entry=parent,
    )


# The mapping is only trusted when the dataset shows it more than once, so the
# fixture spells each old character in two different names, as the real data does.
PLACES = [
    _place("1", "豊田", "豊後", "速見郡", old_forms=["豐田"]),
    _place("7", "豊岡", "豊後", "国東郡", old_forms=["豐岡"]),
    _place("2", "沢田", "豊後", "速見郡", old_forms=["澤田"]),
    _place("8", "沢village".replace("village", "水"), "豊後", "国東郡", old_forms=["澤水"]),
    _place("3", "守江", "豊後", "速見郡"),
    _place("4", "守江", "肥後", "飽田郡"),
    _place("5", "八坂郷", "豊後", "速見郡"),
    _place("6", "小熊", "豊後", "速見郡", parent="守江"),
]


def test_the_character_mapping_is_learned_from_spelling_pairs():
    mapping = learn_character_mapping(spelling_pairs(PLACES))
    assert mapping["豐"] == "豊"
    assert mapping["澤"] == "沢"


def test_a_mapping_seen_once_is_not_trusted():
    assert learn_character_mapping([("龍田", "竜田")]) == {}


def test_pairs_of_different_lengths_are_ignored():
    assert learn_character_mapping([("豐後國", "豊後")] * 3) == {}


def test_a_heading_in_old_characters_is_found():
    index = build_index(PLACES)
    found = index.lookup("豐田", "豊後", "速見郡")
    assert found is not None
    assert found[0].place_id == "1"


def test_the_district_separates_two_places_of_the_same_name():
    index = build_index(PLACES)
    higo = index.lookup("守江", "肥後", "飽田郡")
    bungo = index.lookup("守江", "豊後", "速見郡")
    assert higo is not None
    assert bungo is not None
    assert higo[0].place_id == "4"
    assert bungo[0].place_id == "3"


def test_an_unreadable_character_still_reaches_the_entry():
    index = build_index(PLACES)
    found = index.lookup("八坂〓", "豊後", "速見郡")
    assert found is not None
    assert found[0].name == "八坂郷"


def test_a_heading_is_never_reduced_to_a_single_character():
    index = build_index(
        [_place("9", "山崎", "山城", "乙訓郡")],
        pairs=[("豐田", "豊田"), ("豐岡", "豊岡")],
    )
    assert index.lookup("山城", "山城", "乙訓郡") is None


def test_the_printed_reading_chooses_between_entries_of_the_same_name():
    places = [
        HistoricalPlace(
            place_id="a",
            name="小川",
            source="大日本地名辞書",
            province="豊後",
            district="速見郡",
            readings=["オガワ"],
        ),
        HistoricalPlace(
            place_id="b",
            name="小川",
            source="大日本地名辞書",
            province="豊後",
            district="速見郡",
            readings=["コガワ"],
        ),
    ]
    index = build_index(places, pairs=[("豐田", "豊田"), ("豐岡", "豊岡")])
    found = index.lookup("小川", "豊後", "速見郡", "コガワ")
    assert found is not None
    assert found[0].place_id == "b"
    assert found[1] == 2


def test_a_heading_outside_the_province_is_not_matched():
    index = build_index(PLACES)
    assert index.lookup("守江", "薩摩", None) is None


def test_the_province_of_a_running_head_is_recognised():
    index = build_index(PLACES)
    assert index.province_of("豐後") == "豊後"
    assert index.province_of("速見郡") is None


def test_entries_described_under_a_heading_are_listed():
    index = build_index(PLACES)
    parent = index.lookup("守江", "豊後", "速見郡")
    assert parent is not None
    assert [child.name for child in index.children_of(parent[0])] == ["小熊"]
