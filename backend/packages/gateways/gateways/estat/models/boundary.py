"""Models for the small-area boundary dataset published by e-Stat."""

from pydantic import BaseModel, Field


class SmallAreaBoundary(BaseModel):
    """One 町丁・字等 polygon from the census small-area boundaries.

    These are the smallest administrative areas published nationwide with
    geometry, so they are what a place name's extent can honestly be drawn as.
    """

    key_code: str = Field(description="e-Stat KEY_CODE, unique nationwide")
    pref_code: str
    pref_name: str
    municipality_code: str
    municipality_name: str
    name: str = Field(description="S_NAME, the 町丁・字等 name")
    area_m2: float | None = None
    population: int | None = None
    households: int | None = None
    #: Polygon rings in GeoJSON order: [[[lon, lat], ...], ...]
    rings: list[list[tuple[float, float]]] = Field(default_factory=list)

    def bbox(self) -> tuple[float, float, float, float] | None:
        """Return (west, south, east, north), or None when there is no geometry."""
        points = [point for ring in self.rings for point in ring]
        if not points:
            return None
        lons = [point[0] for point in points]
        lats = [point[1] for point in points]
        return min(lons), min(lats), max(lons), max(lats)
