"""Tests for turning a municipal place-name study into toponym records."""

import pytest

from alg.core.toponyms.pipelines.ingest_local_history import build_from_gazetteer
from alg.models.element import ElementDictionary, ToponymElement

SAMPLE = """                          名 久 木 村（ナグキムラ）
          （川内町５丁目分）
      字         小         字     地 名 語 源
ｳﾞﾒ    ｶﾞ    ｸﾎﾞ

梅     ヶ 久 保                   梅は埋の替字で山腹の崩壊で埋まって傾斜地の出来たくぼ。
ﾔｸ    ｼ    ﾄﾞｳ

薬     師 堂                     薬師如来を安置した薬師堂を作ったため付近の地名となった。
"""


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
        ],
    )


def test_only_names_with_a_stated_origin_become_records(dictionary: ElementDictionary):
    records = build_from_gazetteer(SAMPLE, dictionary)
    assert [record.name for record in records] == ["梅ヶ久保"]


def test_record_carries_a_verified_quote_and_citation(dictionary: ElementDictionary):
    (record,) = build_from_gazetteer(SAMPLE, dictionary)
    assert record.evidence_level == 2
    citation = record.evidence[0]
    assert citation.source_id == "kiryu_timeikou_2000"
    assert citation.quote_verified
    assert citation.quote is not None
    assert "梅は埋の替字" in citation.quote
    assert "『桐生市地名考』" in citation.claim


def test_record_carries_administrative_context(dictionary: ElementDictionary):
    (record,) = build_from_gazetteer(SAMPLE, dictionary)
    assert record.admin.pref == "群馬県"
    assert record.admin.pref_code == "10"
    assert record.admin.municipality == "桐生市"
    assert record.admin.oaza == "川内町五丁目"
    assert record.admin.historical_village == "名久木村"
    assert record.admin.koaza == "梅ヶ久保"


def test_matched_elements_are_attached(dictionary: ElementDictionary):
    (record,) = build_from_gazetteer(SAMPLE, dictionary)
    assert [ref.element_id for ref in record.elements] == ["ume"]
    assert "slope_failure" in record.hazard_types
