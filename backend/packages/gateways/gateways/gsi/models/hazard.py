"""Models describing GSI hazard tile lookups."""

from pydantic import BaseModel


class HazardSample(BaseModel):
    """Result of sampling the hazard raster tiles at one coordinate."""

    debris_flow_zone: bool | None = None
    steep_slope_zone: bool | None = None
    landslide_zone: bool | None = None
    flood_zone: bool | None = None
    tsunami_zone: bool | None = None
    storm_surge_zone: bool | None = None
    avalanche_risk: bool | None = None

    def any_zone(self) -> bool:
        """Return True when the point falls inside at least one hazard zone."""
        return any(
            value is True
            for value in (
                self.debris_flow_zone,
                self.steep_slope_zone,
                self.landslide_zone,
                self.flood_zone,
                self.tsunami_zone,
                self.storm_surge_zone,
                self.avalanche_risk,
            )
        )
