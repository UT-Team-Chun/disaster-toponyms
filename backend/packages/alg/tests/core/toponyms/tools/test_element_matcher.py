"""Tests for matching place names against the element dictionary."""

import pytest

from alg.core.toponyms.tools.element_matcher import (
    hazard_types_from_matches,
    match_elements,
    max_specificity,
)
from alg.models.element import ElementDictionary, ToponymElement


@pytest.fixture
def dictionary() -> ElementDictionary:
    return ElementDictionary(
        elements=[
            ToponymElement(
                id="ume",
                label="ウメ（梅・埋）",
                surfaces=["梅", "埋"],
                readings=["ウメ"],
                meaning="埋没地",
                hazard_types=["slope_failure"],
                specificity=0.5,
                substitution_of="埋",
            ),
            ToponymElement(
                id="kubo",
                label="クボ（窪・久保）",
                surfaces=["窪", "久保"],
                readings=["クボ"],
                meaning="窪地",
                hazard_types=["inundation"],
                specificity=0.2,
            ),
            ToponymElement(
                id="januke",
                label="ジャヌケ（蛇抜）",
                surfaces=["蛇抜"],
                readings=["ジャヌケ"],
                meaning="土石流跡",
                hazard_types=["debris_flow"],
                specificity=0.95,
            ),
        ],
    )


def test_matches_both_elements_of_a_compound_name(dictionary: ElementDictionary):
    matches = match_elements("梅ヶ久保", "ウメガクボ", dictionary)
    assert [match.element.id for match in matches] == ["ume", "kubo"]


def test_matches_are_ordered_by_specificity(dictionary: ElementDictionary):
    matches = match_elements("蛇抜久保", None, dictionary)
    assert [match.element.id for match in matches] == ["januke", "kubo"]
    assert max_specificity(matches) == pytest.approx(0.95)


def test_variant_spelling_still_matches(dictionary: ElementDictionary):
    assert match_elements("梅ケ久保", None, dictionary)
    assert match_elements("梅が久保", None, dictionary)


def test_reading_match_is_used_when_the_spelling_hides_the_element(
    dictionary: ElementDictionary,
):
    matches = match_elements("蛇脱沢", "ジャヌケザワ", dictionary)
    assert [match.element.id for match in matches] == ["januke"]
    assert matches[0].matched_on == "reading"


def test_surface_only_mode_ignores_readings(dictionary: ElementDictionary):
    assert match_elements("蛇脱沢", "ジャヌケザワ", dictionary, surface_only=True) == []


def test_hazard_types_are_collected_without_duplicates(dictionary: ElementDictionary):
    matches = match_elements("梅ヶ久保", None, dictionary)
    assert hazard_types_from_matches(matches) == ["slope_failure", "inundation"]


def test_unrelated_name_matches_nothing(dictionary: ElementDictionary):
    assert match_elements("中央一丁目", None, dictionary) == []
    assert max_specificity([]) == 0.0
