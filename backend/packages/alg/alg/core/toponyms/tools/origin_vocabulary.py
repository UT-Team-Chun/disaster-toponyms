"""Check that a cited passage really talks about ground or about disaster.

A model asked to classify the origin of a place name will occasionally label a
perfectly ordinary explanation — a landholder called Shirō, a shrine, a poem —
as a disaster origin. The passage it cites is verbatim, so the citation is real;
what is wrong is the label. Reading the level off the words the passage actually
contains, rather than off the label, keeps that mistake out of the dataset.
"""

from __future__ import annotations

import re
from typing import Final

#: Words that describe the ground: the terrain half of a place-name origin.
#:
#: Single characters that turn up in any address — 川, 山, 岩, 池, 岡 — are
#: deliberately absent. They were tried and let entries through on the strength
#: of a word in the address rather than in the explanation:
#: 「今北由布村大字川上の小字にして、鑛泉あるを以て此稱あり」 was read as a
#: terrain origin because of the 川 in 川上, when the name is really from a spring.
TERRAIN_WORDS: Final[tuple[str, ...]] = (
    "崖",
    "岸",
    "窪",
    "窪地",
    "久保",
    "凹",
    "谷",
    "谷地",
    "谷戸",
    "谿",
    "渓",
    "澤",
    "沢",
    "洲",
    "渚",
    "浦",
    "灣",
    "湾",
    "潟",
    "河原",
    "川原",
    "磧",
    "州崎",
    "砂洲",
    "砂丘",
    "沼",
    "濕地",
    "湿地",
    "泥",
    "沮洳",
    "深田",
    "泥田",
    "低地",
    "低濕",
    "低湿",
    "窊",
    "傾斜",
    "斜面",
    "段丘",
    "山腹",
    "山麓",
    "扇狀地",
    "扇状地",
    "三角洲",
    "河口",
    "淵",
    "土砂",
    "水邊",
    "水辺",
    "急峻",
    "峻嶮",
    "險岨",
    "険阻",
    "岩石",
    "巖石",
    # Ground that behaves badly, as the sources describe it.
    "低き",
    "低く",
    "低し",
    "くぼ",
    "クボ",
    "湫",
    "萢",
    "潦",
    "汀",
    "砂地",
    "沙地",
    "廢川",
    "廃川",
    "河身",
    "河道",
    "堤",
    "堤防",
    "水底",
    "遊水",
    "溜池",
    "湛",
)

#: Words that name a disaster, in the vocabulary the sources actually use.
#: The bare character 崩 is deliberately absent: in a Meiji-era work it usually
#: reports the death of an emperor, not a hillside giving way.
DISASTER_WORDS: Final[tuple[str, ...]] = (
    "崩壞",
    "崩壊",
    "崩落",
    "崩れ",
    "崩地",
    "崩潰",
    "山崩",
    "崖崩",
    "山抜",
    "山津浪",
    "土石流",
    "地すべり",
    "地滑り",
    "落石",
    "雪崩",
    "洪水",
    "水害",
    "出水",
    "氾濫",
    "汎濫",
    "決潰",
    "決壞",
    "決壊",
    "流失",
    "押出",
    "押流",
    "欠崩",
    "浸水",
    "冠水",
    "水沒",
    "水没",
    "津浪",
    "津波",
    "海嘯",
    "高潮",
    "地震",
    "噴火",
    "泥流",
    "埋沒",
    "埋没",
    "埋り",
    "埋まっ",
    "埋め",
    "埋立",
    "埋",
    "陷沒",
    "陥没",
    "陷落",
    "陥落",
    "沈下",
    "溺",
    "水死",
    "溺死",
    "流死",
    "漂流",
    "液狀化",
    "液状化",
)

_TERRAIN = re.compile("|".join(re.escape(word) for word in TERRAIN_WORDS))
_DISASTER = re.compile("|".join(re.escape(word) for word in DISASTER_WORDS))


def describes_terrain(text: str) -> bool:
    """Return True when a passage names a landform."""
    return bool(_TERRAIN.search(text or ""))


def describes_disaster(text: str) -> bool:
    """Return True when a passage names a natural disaster."""
    return bool(_DISASTER.search(text or ""))


def is_natural_disaster(quote: str, hazard_types: list[str] | tuple[str, ...]) -> bool:
    """Say whether an extracted record really names a natural disaster.

    A gazetteer recounts prodigies as readily as floods. Requiring the excerpt
    itself to name a disaster keeps a thunderbolt splitting a rock in the
    Chronicles from being published as a recorded event.

    Args:
        quote: The excerpt the record was read from.
        hazard_types: Hazard types the model assigned.

    Returns:
        True when the excerpt names a disaster, or a specific hazard was given.

    """
    if describes_disaster(quote):
        return True
    return any(hazard != "other" for hazard in hazard_types)


def level_for(origin_kind: str, text: str) -> int | None:
    """Return the evidence level a cited passage can actually support.

    Args:
        origin_kind: What the model said the origin is.
        text: The cited passage together with the summary written from it.

    Returns:
        2 when the passage names a disaster, 1 when it only names a landform,
        and None when it names neither and therefore supports no reading.

    """
    if origin_kind not in {"terrain", "disaster", "substitution"}:
        return None
    if origin_kind in {"disaster", "substitution"} and describes_disaster(text):
        return 2
    if describes_terrain(text) or describes_disaster(text):
        return 1
    return None
