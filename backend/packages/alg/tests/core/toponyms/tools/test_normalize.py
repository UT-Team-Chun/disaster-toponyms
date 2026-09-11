"""Tests for place-name spelling and reading normalisation."""

from alg.core.toponyms.tools.normalize import (
    collapse_folded_japanese,
    collapse_folded_prose,
    comparison_key,
    display_width,
    normalize_name,
    normalize_reading,
    strip_spaces,
)


def test_strip_spaces_removes_ideographic_space():
    assert strip_spaces("梅ヶ　久保 ") == "梅ヶ久保"


def test_normalize_reading_folds_halfwidth_katakana():
    assert normalize_reading("ｳﾒ ｶﾞ ｸﾎﾞ") == "ウメガクボ"


def test_normalize_reading_folds_hiragana():
    assert normalize_reading("うめがくぼ") == "ウメガクボ"


def test_normalize_name_unifies_prewar_kanji():
    assert normalize_name("蛇 抜 澤") == "蛇抜沢"


def test_comparison_key_unifies_connectives():
    assert comparison_key("梅ヶ久保") == comparison_key("梅ケ久保")
    assert comparison_key("梅ヶ久保") == comparison_key("梅が久保")
    assert comparison_key("磯ノ入") == comparison_key("磯之入")


def test_comparison_key_keeps_distinct_names_apart():
    assert comparison_key("梅ヶ久保") != comparison_key("梅ノ木久保")


def test_display_width_counts_wide_characters_as_two():
    assert display_width("蛇崩") == 4
    assert display_width("ab") == 2
    assert display_width("蛇 崩") == 5


def test_collapse_folded_japanese_joins_wrapped_sentence():
    folded = "山腹の崩壊で埋まって 出来た傾斜地。"
    assert collapse_folded_japanese(folded) == "山腹の崩壊で埋まって出来た傾斜地。"


def test_collapse_folded_japanese_keeps_spaces_around_digits():
    assert collapse_folded_japanese("平成 12 年") == "平成 12 年"


def test_collapse_folded_prose_also_joins_across_digits():
    assert collapse_folded_prose("伝わり、 1953年の災害") == "伝わり、1953年の災害"


def test_collapse_folded_prose_keeps_latin_words_separated():
    assert collapse_folded_prose("CC BY 4.0") == "CC BY 4.0"
