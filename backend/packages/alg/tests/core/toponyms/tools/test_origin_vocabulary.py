"""Tests for reading the evidence level off the passage that was cited."""

from alg.core.toponyms.tools.origin_vocabulary import (
    describes_disaster,
    describes_terrain,
    is_natural_disaster,
    level_for,
)


def test_a_landform_is_recognised():
    assert describes_terrain("兩岬以内の廣灣を內浦と名づく")
    assert describes_terrain("皿状の浅いくぼのある区域で、窪地の意")
    assert not describes_terrain("古者此處有豪族所謂長者名四郞")


def test_a_disaster_is_recognised():
    assert describes_disaster("山崩により生じたる地なり")
    assert describes_disaster("海風沙塵の爲めに一夜にして埋沒し")
    assert not describes_disaster("天皇此に崩御あり")


def test_a_disaster_origin_earns_level_two():
    assert level_for("disaster", "山崩により生じたる地なるを以て崩野と稱す") == 2


def test_a_substitution_that_only_names_the_ground_is_level_one():
    assert level_for("substitution", "間々は崖の轉じたるなり") == 1


def test_a_terrain_origin_earns_level_one():
    assert level_for("terrain", "淺谷の義なり") == 1


def test_an_origin_that_names_neither_supports_nothing():
    assert level_for("disaster", "古者此處有豪族所謂長者名四郞、故以名地") is None
    assert level_for("terrain", "麻の好地をば麻原とも云へるにや") is None


def test_an_unknown_label_supports_nothing():
    assert level_for("none", "山崩により生じたる地なり") is None


def test_a_word_from_the_address_does_not_make_a_terrain_origin():
    # 川 appears in 川上, which is where the place is, not what the name means.
    assert level_for("terrain", "今北由布村大字川上の小字にして、鑛泉あるを以て此稱あり") is None


def test_a_record_must_name_a_disaster_or_a_specific_hazard():
    assert is_natural_disaster("明治廿二年洪水あり", [])
    assert is_natural_disaster("雷のとゝろき落ちて", ["debris_flow"])
    assert not is_natural_disaster("雷のとゝろき落ちて、溝を開きし所なれば", ["other"])
    assert not is_natural_disaster("郡衙を日出に置く", [])
