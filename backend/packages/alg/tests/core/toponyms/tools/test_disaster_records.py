"""Tests for turning extracted disaster mentions into verifiable records."""

from alg.core.toponyms.tools.disaster_records import RecordContext, build_records

SOURCE = "明治廿二年洪水あり、村落の半ばを流失す。郡衙を日出に置く。"
CONTEXT = RecordContext(
    source_text=SOURCE,
    source_id="yoshida_dainihon_chimei_1907",
    locator="https://dl.ndl.go.jp/pid/2937057/1/695",
    hazard_types=("flood",),
    model_name="gpt-5.6-terra",
    quote_medium="ocr",
)


def test_a_verbatim_excerpt_is_kept():
    records, rejected = build_records(
        [
            {
                "relation": "same_place_record",
                "name": "明治22年の洪水",
                "date_text": "明治廿二年",
                "quote": "明治廿二年洪水あり、村落の半ばを流失す。",
            },
        ],
        CONTEXT,
    )
    assert rejected == 0
    assert records[0].quote_verified
    assert records[0].quote_medium == "ocr"
    assert records[0].hazard_types == ["flood"]


def test_an_excerpt_that_is_not_in_the_source_is_dropped():
    records, rejected = build_records(
        [
            {
                "relation": "same_place_record",
                "name": "大正の洪水",
                "date_text": None,
                "quote": "大正十二年に大洪水あり、全村が流失した。",
            },
        ],
        CONTEXT,
    )
    assert records == []
    assert rejected == 1


def test_proximity_is_never_a_relation_a_model_may_assign():
    records, rejected = build_records(
        [
            {
                "relation": "nearby_record",
                "name": "何かの災害",
                "date_text": None,
                "quote": "明治廿二年洪水あり、村落の半ばを流失す。",
            },
        ],
        CONTEXT,
    )
    assert records == []
    assert rejected == 1


def test_an_empty_payload_yields_nothing():
    assert build_records(None, CONTEXT) == ([], 0)
