"""Tests for reading a vertically typeset page out of its OCR blocks."""

from gateways.ndl.models.page import NdlPage, TextBlock

from alg.core.toponyms.tools.ndl_layout import classify_blocks, glyph_ratio, reading_beside


def _block(text: str, x: float, y: float, width: float, height: float) -> TextBlock:
    return TextBlock(text=text, x=x, y=y, width=width, height=height)


# A column of the gazetteer: the running head in the margin, the reading in its
# own narrow column, the heading in larger type, then the body.
PAGE = NdlPage(
    pid="2937057",
    frame=802,
    contents="肥前西彼杵郡アクノウラ飽之浦稻佐の南にして、",
    blocks=[
        _block("肥前", 6015, 794, 63, 150),
        _block("西彼杵郡", 6015, 1163, 70, 326),
        _block("アクノウラ", 5951, 448, 41, 160),
        _block("飽之浦", 5895, 450, 64, 184),
        _block("稻佐の南にして、", 5907, 667, 52, 326),
        _block("今淵村に屬す、", 5910, 1006, 53, 285),
    ],
)


def test_the_margin_holds_the_running_head():
    roles = {item.text: item.role for item in classify_blocks(PAGE)}
    assert roles["肥前"] == "running"
    assert roles["西彼杵郡"] == "running"


def test_small_katakana_is_read_as_a_reading():
    roles = {item.text: item.role for item in classify_blocks(PAGE)}
    assert roles["アクノウラ"] == "ruby"


def test_larger_type_is_read_as_a_heading():
    roles = {item.text: item.role for item in classify_blocks(PAGE)}
    assert roles["飽之浦"] == "heading"
    assert roles["稻佐の南にして、"] == "body"


def test_a_page_whose_outer_column_carries_text_has_no_running_head():
    page = NdlPage(
        pid="2937057",
        frame=696,
        contents="",
        blocks=[
            _block("日出", 5675, 462, 82, 150),
            _block("別府灣に臨む。", 5668, 700, 52, 290),
        ],
    )
    roles = {item.text: item.role for item in classify_blocks(page)}
    assert roles["日出"] == "heading"
    assert roles["別府灣に臨む。"] == "body"


def test_a_page_without_geometry_is_all_body():
    page = NdlPage(pid="1", frame=1, contents="text", blocks=[])
    assert classify_blocks(page) == []


def test_the_reading_beside_a_heading_is_the_ruby_at_the_same_rows():
    roled = classify_blocks(PAGE)
    heading = next(item.block for item in roled if item.role == "heading")
    rubies = [item.block for item in roled if item.role == "ruby"]
    assert reading_beside(heading, rubies) == "アクノウラ"


def test_a_ruby_in_a_different_row_is_not_the_reading():
    heading = _block("飽之浦", 5895, 450, 64, 184)
    far = _block("フチ", 5955, 1051, 41, 72)
    assert reading_beside(heading, [far]) == ""


def test_glyph_ratio_reports_the_type_size():
    assert glyph_ratio(_block("飽之浦", 0, 0, 64, 184)) > glyph_ratio(
        _block("稻佐の南にして、", 0, 0, 52, 326),
    )
