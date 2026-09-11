"""Tests for the 『桐生市地名考』 layout parser."""

from alg.core.toponyms.parsers.kiryu_timeikou import (
    is_plausible_name,
    parse_kiryu_text,
)
from alg.core.toponyms.parsers.layout import strip_running_numbers

# 版面を再現した最小のサンプル。実際の抽出テキストと同じ構造にしている。
SAMPLE = """                              前書きの文章がここに入る。

                      17
                          今      泉    村（イマイズミムラ）
          （仲町１～３丁目、東１～７丁目、
                          東久方町２･３丁目の一部、   * 町別小字表１参照）

      字         小         字     地 名 語 源（寛文１３年         アザ

                                            （１６７３）の水帳の字による）

ｼﾞｬ        ｸｽﾞﾚ

蛇           崩                   大蛇が山腹から出てくるとき大きい土砂崩れを起こすとい
                               う伝承から、蛇の字は崩壊を表す。
ｳﾞﾒ    ｶﾞ    ｸﾎﾞ

梅     ヶ 久 保                   梅は埋の替字で山腹の崩壊で埋まって傾斜地の出来たくぼ。

                  前         田      明治９年地租改正の時、前田・才ノ神をあわせて前田とし
                                  た区域。
"""


def test_parses_entries_only_inside_the_dictionary_body():
    entries = parse_kiryu_text(SAMPLE)
    names = [entry.name for entry in entries]
    assert names == ["蛇崩", "梅ヶ久保", "前田"]


def test_captures_reading_village_and_modern_area():
    entries = {entry.name: entry for entry in parse_kiryu_text(SAMPLE)}
    jakuzure = entries["蛇崩"]
    assert jakuzure.reading == "ジャクズレ"
    assert jakuzure.village == "今泉村"
    assert jakuzure.page == 17
    assert jakuzure.modern_area is not None
    assert jakuzure.modern_area.startswith("仲町１～３丁目")
    assert "町別小字表" not in jakuzure.modern_area


def test_joins_continuation_lines_into_the_description():
    entries = {entry.name: entry for entry in parse_kiryu_text(SAMPLE)}
    assert entries["蛇崩"].description.endswith("蛇の字は崩壊を表す。")


def test_distinguishes_small_sections_from_sections():
    entries = {entry.name: entry for entry in parse_kiryu_text(SAMPLE)}
    assert entries["蛇崩"].level == "koaza"
    assert entries["前田"].level == "aza"


def test_strip_running_numbers_removes_page_number_lines():
    text = "本文のつづき\n   11\nさらに本文"
    assert strip_running_numbers(text) == "本文のつづき\nさらに本文"


def test_is_plausible_name_rejects_prose_and_accepts_names():
    assert is_plausible_name("梅ヶ久保")
    assert is_plausible_name("とびのす")
    assert not is_plausible_name("蕪は傾くの換字で崖をいう。")
    assert not is_plausible_name("久安年間(1462)新町荒戸新町")
    assert not is_plausible_name("")
