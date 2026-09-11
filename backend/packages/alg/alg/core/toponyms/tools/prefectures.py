"""Prefecture code table used for identifiers, filtering and file sharding."""

from typing import Final

PREFECTURES: Final[tuple[tuple[str, str], ...]] = (
    ("01", "北海道"),
    ("02", "青森県"),
    ("03", "岩手県"),
    ("04", "宮城県"),
    ("05", "秋田県"),
    ("06", "山形県"),
    ("07", "福島県"),
    ("08", "茨城県"),
    ("09", "栃木県"),
    ("10", "群馬県"),
    ("11", "埼玉県"),
    ("12", "千葉県"),
    ("13", "東京都"),
    ("14", "神奈川県"),
    ("15", "新潟県"),
    ("16", "富山県"),
    ("17", "石川県"),
    ("18", "福井県"),
    ("19", "山梨県"),
    ("20", "長野県"),
    ("21", "岐阜県"),
    ("22", "静岡県"),
    ("23", "愛知県"),
    ("24", "三重県"),
    ("25", "滋賀県"),
    ("26", "京都府"),
    ("27", "大阪府"),
    ("28", "兵庫県"),
    ("29", "奈良県"),
    ("30", "和歌山県"),
    ("31", "鳥取県"),
    ("32", "島根県"),
    ("33", "岡山県"),
    ("34", "広島県"),
    ("35", "山口県"),
    ("36", "徳島県"),
    ("37", "香川県"),
    ("38", "愛媛県"),
    ("39", "高知県"),
    ("40", "福岡県"),
    ("41", "佐賀県"),
    ("42", "長崎県"),
    ("43", "熊本県"),
    ("44", "大分県"),
    ("45", "宮崎県"),
    ("46", "鹿児島県"),
    ("47", "沖縄県"),
)

PREF_NAME_TO_CODE: Final[dict[str, str]] = {name: code for code, name in PREFECTURES}
PREF_CODE_TO_NAME: Final[dict[str, str]] = dict(PREFECTURES)


def pref_code(name: str | None) -> str | None:
    """Return the two-digit code for a prefecture name.

    Args:
        name: Prefecture name, with or without the 都道府県 suffix.

    Returns:
        Two-digit code, or None when the name is unknown.

    """
    if not name:
        return None
    if name in PREF_NAME_TO_CODE:
        return PREF_NAME_TO_CODE[name]
    for full_name, code in PREF_NAME_TO_CODE.items():
        if full_name.startswith(name) or name.startswith(full_name):
            return code
    return None
