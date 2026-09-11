"""Tests for slippy tile maths used to sample hazard rasters."""

import pytest

from gateways.gsi.operations.hazard_tile import (
    HAZARD_LAYERS,
    TILE_SIZE,
    lonlat_to_tile_pixel,
)


def test_origin_of_the_world_is_the_top_left_tile():
    tile_x, tile_y, pixel_x, pixel_y = lonlat_to_tile_pixel(85.0511, -180.0, 0)
    assert (tile_x, tile_y) == (0, 0)
    assert (pixel_x, pixel_y) == (0, 0)


def test_null_island_is_the_centre_of_the_world():
    tile_x, tile_y, pixel_x, pixel_y = lonlat_to_tile_pixel(0.0, 0.0, 1)
    assert (tile_x, tile_y) == (1, 1)
    assert (pixel_x, pixel_y) == (0, 0)


@pytest.mark.parametrize("zoom", [8, 12, 15])
def test_japanese_coordinates_stay_inside_the_tile_grid(zoom: int):
    tile_x, tile_y, pixel_x, pixel_y = lonlat_to_tile_pixel(36.467, 139.339, zoom)
    assert 0 <= tile_x < 2**zoom
    assert 0 <= tile_y < 2**zoom
    assert 0 <= pixel_x < TILE_SIZE
    assert 0 <= pixel_y < TILE_SIZE


def test_zooming_in_quadruples_the_tile_index():
    low_x, low_y, _, _ = lonlat_to_tile_pixel(36.467, 139.339, 10)
    high_x, high_y, _, _ = lonlat_to_tile_pixel(36.467, 139.339, 11)
    assert high_x // 2 == low_x
    assert high_y // 2 == low_y


def test_every_hazard_layer_names_a_published_directory():
    assert set(HAZARD_LAYERS) == {
        "debris_flow_zone",
        "steep_slope_zone",
        "landslide_zone",
        "flood_zone",
        "tsunami_zone",
        "storm_surge_zone",
        "avalanche_risk",
    }
    assert all(directory for directory in HAZARD_LAYERS.values())
