"""Tests for identifiers and the prefecture table."""

from alg.core.toponyms.tools.ids import make_toponym_id
from alg.core.toponyms.tools.prefectures import PREFECTURES, pref_code
from alg.models.toponym import AdminArea

EXPECTED_PREFECTURES = 47


def test_prefecture_table_is_complete():
    assert len(PREFECTURES) == EXPECTED_PREFECTURES


def test_pref_code_accepts_full_and_short_names():
    assert pref_code("群馬県") == "10"
    assert pref_code("広島県") == "34"
    assert pref_code("東京") == "13"
    assert pref_code(None) is None
    assert pref_code("存在しない県") is None


def test_id_is_stable_and_prefixed_by_prefecture():
    admin = AdminArea(pref="群馬県", municipality="桐生市", koaza="梅ヶ久保")
    first = make_toponym_id("梅ヶ久保", admin)
    second = make_toponym_id("梅ヶ久保", admin)
    assert first == second
    assert first.startswith("10-")


def test_id_is_url_safe():
    admin = AdminArea(pref="広島県", municipality="広島市安佐南区")
    identifier = make_toponym_id("蛇落地悪谷", admin)
    assert identifier.replace("-", "").isalnum()
    assert identifier.isascii()


def test_salt_separates_records_that_share_a_name():
    admin = AdminArea(pref="群馬県", municipality="桐生市")
    assert make_toponym_id("大谷戸", admin, salt="下広沢村") != make_toponym_id(
        "大谷戸",
        admin,
        salt="下仁田山村",
    )
