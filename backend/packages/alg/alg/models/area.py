"""The administrative area a place name covers."""

from pydantic import BaseModel, Field

#: A polygon ring as GeoJSON orders it: [[lon, lat], ...].
Ring = list[tuple[float, float]]


class MatchedArea(BaseModel):
    """A census 町丁・字等 polygon together with the records it covers.

    Small-section (小字) boundaries are not published nationwide, so this is the
    finest extent a name can honestly be drawn with. Each record keeps its own
    location precision, which is what the viewer labels the polygon by.
    """

    key_code: str = Field(description="e-Stat KEY_CODE, unique nationwide")
    pref_code: str
    pref_name: str
    municipality_name: str
    name: str
    area_m2: float | None = None
    population: int | None = None
    rings: list[Ring] = Field(default_factory=list)
    toponym_ids: list[str] = Field(default_factory=list)
