"""Hazard vocabulary shared by toponyms, elements and monuments."""

from typing import Final, Literal

HazardType = Literal[
    "landslide",
    "debris_flow",
    "rockfall",
    "slope_failure",
    "flood",
    "inundation",
    "tsunami",
    "storm_surge",
    "soft_ground",
    "avalanche",
    "erosion",
    "volcanic",
    "earthquake",
    "wind",
    "other",
]

#: Japanese labels used in the UI and in curated YAML files.
HAZARD_LABELS_JA: Final[dict[str, str]] = {
    "landslide": "地すべり",
    "debris_flow": "土石流",
    "rockfall": "落石",
    "slope_failure": "崖崩れ・斜面崩壊",
    "flood": "洪水・河川氾濫",
    "inundation": "浸水・内水・低湿",
    "tsunami": "津波",
    "storm_surge": "高潮",
    "soft_ground": "軟弱地盤・液状化",
    "avalanche": "雪崩",
    "erosion": "侵食",
    "volcanic": "火山",
    "earthquake": "地震",
    "wind": "強風",
    "other": "その他",
}

#: Keyword -> hazard type, used when reading free-text disaster labels.
HAZARD_KEYWORDS_JA: Final[tuple[tuple[str, HazardType], ...]] = (
    ("土石流", "debris_flow"),
    ("地すべり", "landslide"),
    ("地滑り", "landslide"),
    ("山崩れ", "slope_failure"),
    ("崖崩れ", "slope_failure"),
    ("崩壊", "slope_failure"),
    ("崩れ", "slope_failure"),
    ("落石", "rockfall"),
    ("土砂", "debris_flow"),
    ("津波", "tsunami"),
    ("高潮", "storm_surge"),
    ("洪水", "flood"),
    ("氾濫", "flood"),
    ("水害", "flood"),
    ("浸水", "inundation"),
    ("内水", "inundation"),
    ("湿地", "soft_ground"),
    ("軟弱", "soft_ground"),
    ("液状化", "soft_ground"),
    ("雪崩", "avalanche"),
    ("侵食", "erosion"),
    ("浸食", "erosion"),
    ("噴火", "volcanic"),
    ("火山", "volcanic"),
    ("地震", "earthquake"),
    ("強風", "wind"),
    ("竜巻", "wind"),
)
