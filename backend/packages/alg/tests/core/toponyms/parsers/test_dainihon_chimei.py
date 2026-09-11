"""Tests for splitting the scanned national gazetteer into entries."""

from gateways.ndl.models.page import NdlPage, TextBlock
from gateways.nihu.models.place import HistoricalPlace

from alg.core.toponyms.parsers.dainihon_chimei import deduplicate, parse_pages
from alg.core.toponyms.tools.historical_index import build_index


def _block(text: str, x: float, y: float, width: float, height: float) -> TextBlock:
    return TextBlock(text=text, x=x, y=y, width=width, height=height)


def _place(place_id: str, name: str, district: str) -> HistoricalPlace:
    return HistoricalPlace(
        place_id=place_id,
        name=name,
        attribute="村",
        category="行政地名",
        lat=33.4,
        lon=131.6,
        source="大日本地名辞書",
        province="豊後",
        district=district,
    )


# The printed book spells the province 豐後 and the bay 杵築灣; the mapping that
# folds those to modern characters is learned from the dataset's spelling pairs.
INDEX = build_index(
    [
        _place("1", "守江", "速見郡"),
        _place("2", "杵築湾", "速見郡"),
        _place("3", "日出", "速見郡"),
    ],
    pairs=[("豐田", "豊田"), ("豐岡", "豊岡"), ("灣岸", "湾岸"), ("入灣", "入湾")],
)

PAGE = NdlPage(
    pid="2937057",
    frame=695,
    contents="",
    blocks=[
        _block("豐後", 5918, 805, 59, 150),
        _block("速見郡", 5918, 1174, 64, 240),
        _block("モリエ", 5730, 462, 41, 120),
        _block("守江", 5675, 462, 82, 150),
        _block("杵築灣の北側に在り、", 5668, 973, 52, 415),
        _block("杵築灣", 5589, 470, 80, 180),
        _block("八坂川之に注入す。", 5589, 700, 52, 370),
    ],
)


def test_entries_start_at_a_heading_and_keep_the_text_that_follows():
    entries, _stats = parse_pages([PAGE], INDEX, book_pid="2937057")
    assert [entry.heading for entry in entries] == ["守江", "杵築灣"]
    assert entries[0].text == "杵築灣の北側に在り、"
    assert entries[1].text == "八坂川之に注入す。"


def test_the_running_head_sets_the_province_and_district():
    entries, _stats = parse_pages([PAGE], INDEX)
    assert entries[0].province == "豊後"
    assert entries[0].district == "速見郡"


def test_the_reading_printed_beside_a_heading_is_kept():
    entries, _stats = parse_pages([PAGE], INDEX)
    assert entries[0].reading == "モリエ"


def test_the_province_carries_over_to_a_page_whose_margin_was_not_read():
    second = NdlPage(
        pid="2937057",
        frame=696,
        contents="",
        blocks=[
            _block("日出", 5675, 462, 82, 150),
            _block("別府灣に臨む。", 5668, 700, 52, 290),
        ],
    )
    entries, stats = parse_pages([PAGE, second], INDEX)
    assert [entry.heading for entry in entries] == ["守江", "杵築灣", "日出"]
    assert stats.without_province == 0


def test_pages_before_any_province_are_skipped():
    orphan = NdlPage(
        pid="2937057",
        frame=1,
        contents="",
        blocks=[_block("凡例", 5675, 462, 82, 100)],
    )
    entries, stats = parse_pages([orphan], INDEX)
    assert entries == []
    assert stats.without_province == 1


def test_the_citation_points_at_the_frame_a_reader_can_open():
    entries, _stats = parse_pages([PAGE], INDEX, book_pid="2937057")
    assert entries[0].viewer_url() == "https://dl.ndl.go.jp/pid/2937057/1/695"


def test_the_fullest_body_wins_when_a_heading_is_seen_twice():
    entries, _stats = parse_pages([PAGE, PAGE], INDEX)
    unique = list(deduplicate(entries))
    assert len(unique) == 2
