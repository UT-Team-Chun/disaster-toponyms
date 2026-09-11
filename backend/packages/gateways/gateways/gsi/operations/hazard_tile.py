"""Sampling the national hazard map raster tiles at a coordinate."""

from __future__ import annotations

import io
import math
from typing import Final

import httpx
from PIL import Image

from gateways.gsi.models.hazard import HazardSample
from gateways.http.connections import ResourceMissingError, fetch_bytes

TILE_BASE: Final = "https://disaportaldata.gsi.go.jp/raster"

#: Hazard layer name -> tile directory published by the hazard map portal.
HAZARD_LAYERS: Final[dict[str, str]] = {
    "debris_flow_zone": "05_dosekiryukeikaikuiki",
    "steep_slope_zone": "05_kyukeishakeikaikuiki",
    "landslide_zone": "05_jisuberikeikaikuiki",
    "flood_zone": "01_flood_l2_shinsuishin_data",
    "tsunami_zone": "04_tsunami_newlegend_data",
    "storm_surge_zone": "03_hightide_l2_shinsuishin_data",
    "avalanche_risk": "05_nadarekikenkasyo",
}

TILE_SIZE: Final = 256
DEFAULT_ZOOM: Final = 15
ALPHA_THRESHOLD: Final = 16
RGBA_CHANNELS: Final = 4


def lonlat_to_tile_pixel(lat: float, lon: float, zoom: int) -> tuple[int, int, int, int]:
    """Convert a coordinate to a slippy tile index and in-tile pixel offset.

    Args:
        lat: Latitude in degrees (WGS84).
        lon: Longitude in degrees (WGS84).
        zoom: Tile zoom level.

    Returns:
        Tuple of (tile_x, tile_y, pixel_x, pixel_y).

    """
    scale = 2**zoom
    x_fraction = (lon + 180.0) / 360.0
    sin_lat = math.sin(math.radians(lat))
    y_fraction = 0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)
    world_x = x_fraction * scale * TILE_SIZE
    world_y = y_fraction * scale * TILE_SIZE
    tile_x = int(world_x // TILE_SIZE)
    tile_y = int(world_y // TILE_SIZE)
    return tile_x, tile_y, int(world_x) % TILE_SIZE, int(world_y) % TILE_SIZE


def _pixel_is_painted(directory: str, lat: float, lon: float, zoom: int) -> bool | None:
    """Return whether the hazard tile paints the pixel at the given coordinate."""
    tile_x, tile_y, pixel_x, pixel_y = lonlat_to_tile_pixel(lat, lon, zoom)
    url = f"{TILE_BASE}/{directory}/{zoom}/{tile_x}/{tile_y}.png"
    try:
        raw = fetch_bytes(url, suffix=".png")
    except ResourceMissingError:
        # Tiles are published only where a hazard exists, so a missing tile is
        # the service saying "no hazard here".
        return False
    except (httpx.HTTPStatusError, httpx.TransportError):
        return None
    try:
        with Image.open(io.BytesIO(raw)) as image:
            pixel = image.convert("RGBA").getpixel((pixel_x, pixel_y))
    except OSError:
        return None
    if not isinstance(pixel, tuple) or len(pixel) < RGBA_CHANNELS:
        return None
    return bool(float(pixel[3]) > ALPHA_THRESHOLD)


def sample_hazard(
    lat: float,
    lon: float,
    *,
    layers: tuple[str, ...] | None = None,
    zoom: int = DEFAULT_ZOOM,
) -> HazardSample:
    """Sample every configured hazard layer at one coordinate.

    Args:
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        layers: Optional subset of :data:`HAZARD_LAYERS` keys.
        zoom: Tile zoom level to sample (2-17 are published).

    Returns:
        A hazard sample with one flag per layer.

    """
    selected = layers or tuple(HAZARD_LAYERS)
    values: dict[str, bool | None] = {}
    for layer in selected:
        directory = HAZARD_LAYERS.get(layer)
        if directory is None:
            continue
        values[layer] = _pixel_is_painted(directory, lat, lon, zoom)
    return HazardSample(**values)
