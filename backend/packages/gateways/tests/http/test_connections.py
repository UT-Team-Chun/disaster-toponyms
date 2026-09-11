"""Tests for the cache path layout of the shared HTTP client."""

from gateways.http.connections import cache_path_for


def test_cache_path_is_grouped_by_host():
    path = cache_path_for("https://example.jp/a/b.png", None, ".png")
    assert path.parent.name == "example.jp"
    assert path.suffix == ".png"


def test_query_parameters_change_the_cache_entry():
    first = cache_path_for("https://example.jp/s", {"q": "蛇抜"}, ".json")
    second = cache_path_for("https://example.jp/s", {"q": "梅ヶ久保"}, ".json")
    assert first != second


def test_parameter_order_does_not_change_the_cache_entry():
    first = cache_path_for("https://example.jp/s", {"a": "1", "b": "2"}, ".json")
    second = cache_path_for("https://example.jp/s", {"b": "2", "a": "1"}, ".json")
    assert first == second
