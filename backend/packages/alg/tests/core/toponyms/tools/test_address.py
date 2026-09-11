"""Tests for reading present-day address components out of municipal studies."""

import pytest

from alg.core.toponyms.tools.address import first_oaza, kanji_chome, strip_qualifier


@pytest.mark.parametrize(
    ("number", "expected"),
    [("1", "一"), ("５", "五"), ("10", "十"), ("12", "十二"), ("7", "七")],
)
def test_kanji_chome(number: str, expected: str):
    assert kanji_chome(number) == expected


def test_strip_qualifier_removes_partial_wording():
    assert strip_qualifier("元宿町の大部分") == "元宿町"
    assert strip_qualifier("梅田町の一部") == "梅田町"
    assert strip_qualifier("広沢町間ノ島") == "広沢町間ノ島"


@pytest.mark.parametrize(
    ("area", "expected"),
    [
        ("広沢町５丁目分", "広沢町五丁目"),
        ("梅田町１丁目、平井町", "梅田町一丁目"),
        ("川内町５丁目第１町会", "川内町五丁目"),
        ("新宿１～３丁目、浜松町１丁目", "新宿一丁目"),
        ("元宿町の大部分、巴町１丁目の一部", "元宿町"),
        ("広沢町間ノ島、琴平町の一部", "広沢町間ノ島"),
        ("境野町１～７丁目、広沢町間ノ島", "境野町一丁目"),
        ("菱町", "菱町"),
        (None, None),
        ("", None),
    ],
)
def test_first_oaza(area: str | None, expected: str | None):
    assert first_oaza(area) == expected
