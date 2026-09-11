"""Tests for classifying what a source claims about a place name."""

from alg.core.toponyms.tools.claims import classify_description, verify_quote


def test_states_disaster_origin_is_level_two():
    claim = classify_description(
        "梅は埋の替字で山腹の崩壊で埋まって傾斜地の出来たくぼ。梅ノ木窪とも言う。",
    )
    assert claim is not None
    assert claim.level == 2
    assert "崩壊" in claim.quote
    assert "slope_failure" in claim.hazard_types


def test_states_terrain_only_is_level_one():
    claim = classify_description("皿状の浅いくぼのある区域。")
    assert claim is not None
    assert claim.level == 1


def test_dated_event_is_level_three():
    claim = classify_description(
        "渡良瀬川の川原の略でもとは放光原と呼ばれ、元亀２年（１５７１）の洪水で流されて以来川原の区域。",
    )
    assert claim is not None
    assert claim.level == 3
    assert "flood" in claim.hazard_types


def test_no_terrain_or_disaster_wording_is_rejected():
    assert classify_description("薬師如来を安置した薬師堂を作ったため付近の地名となった。") is None


def test_administrative_merger_sentences_are_ignored():
    claim = classify_description(
        "明治９年地租改正の時、間々久保・曲り間々・天神尾根を併せて間々久保とした区域。",
    )
    assert claim is None


def test_quote_is_taken_from_the_informative_sentence():
    claim = classify_description(
        "明治９年地租改正の時、あじろを阿治路に換えた区域。山腹の崩壊で埋まって出来た小傾斜地。",
    )
    assert claim is not None
    assert "地租改正" not in claim.quote
    assert claim.quote.startswith("山腹の崩壊")


def test_verify_quote_ignores_layout_whitespace():
    source = "夏保ノ入の山腹の\n土石流で埋まって   出来た傾斜地。\n"
    assert verify_quote("夏保ノ入の山腹の土石流で埋まって出来た傾斜地。", source)


def test_verify_quote_rejects_text_stitched_from_two_places():
    source = "前半の文です。\n\nまったく別の段落。\n"
    assert not verify_quote("前半の文です。別の段落の続き。", source)


def test_verify_quote_rejects_empty_quote():
    assert not verify_quote("", "なにかの本文")
