"""Models for the NIHU historical place-name dataset."""

from __future__ import annotations

from pydantic import BaseModel

#: Name of the source whose entries come from Yoshida Tōgo's national gazetteer.
GAZETTEER_SOURCE = "大日本地名辞書"
#: Name of the source whose entries were read off the old 1:50,000 maps.
OLD_MAP_SOURCE = "旧5万分の1地形図"


class HistoricalPlace(BaseModel):
    """A historical place name that has been located on a map.

    The dataset carries the old printed spelling and the reading beside the
    modern transcription, which is what lets an entry in a Meiji-era gazetteer
    be recognised and given a coordinate.
    """

    place_id: str
    name: str
    #: Fine-grained kind, for example 字, 村, 郷・里, 山・岳.
    attribute: str | None = None
    #: Coarse kind, for example 行政地名, 地形, 水部.
    category: str | None = None
    lat: float | None = None
    lon: float | None = None
    source: str
    #: Volume and page of the printed source, or the map sheet it was read from.
    source_detail: str | None = None
    volume: int | None = None
    page: int | None = None
    #: Heading the entry is printed under, when it is not a heading itself.
    parent_entry: str | None = None
    province: str | None = None
    district: str | None = None
    prefecture: str | None = None
    readings: list[str] = []
    old_forms: list[str] = []

    def has_location(self) -> bool:
        """Return True when the entry carries a coordinate."""
        return self.lat is not None and self.lon is not None
