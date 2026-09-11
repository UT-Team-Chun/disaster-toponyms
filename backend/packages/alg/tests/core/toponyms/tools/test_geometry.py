"""Tests for reducing polygon detail before publishing it."""

from alg.core.toponyms.tools.geometry import (
    count_points,
    ring_area,
    round_ring,
    simplify_ring,
    simplify_rings,
)

# A square with many redundant points along its edges.
SQUARE_WITH_NOISE = [
    (139.0, 36.0),
    (139.25, 36.0),
    (139.5, 36.0),
    (139.75, 36.0),
    (140.0, 36.0),
    (140.0, 36.5),
    (140.0, 37.0),
    (139.5, 37.0),
    (139.0, 37.0),
    (139.0, 36.5),
    (139.0, 36.0),
]


def test_collinear_points_are_dropped():
    simplified = simplify_ring(SQUARE_WITH_NOISE, tolerance=0.001)
    assert len(simplified) < len(SQUARE_WITH_NOISE)
    # The four corners have to survive.
    for corner in [(139.0, 36.0), (140.0, 36.0), (140.0, 37.0), (139.0, 37.0)]:
        assert corner in simplified


def test_simplified_ring_stays_closed():
    simplified = simplify_ring(SQUARE_WITH_NOISE, tolerance=0.001)
    assert simplified[0] == simplified[-1]


def test_tiny_rings_are_returned_unchanged():
    triangle = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (0.0, 0.0)]
    assert simplify_ring(triangle) == triangle


def test_a_large_tolerance_never_destroys_the_ring():
    simplified = simplify_ring(SQUARE_WITH_NOISE, tolerance=100.0)
    assert len(simplified) >= 4
    assert simplified[0] == simplified[-1]


def test_rounding_removes_points_that_collapse_together():
    ring = [
        (139.000001, 36.000001),
        (139.000002, 36.000002),
        (140.0, 36.0),
        (140.0, 37.0),
        (139.000001, 36.000001),
    ]
    rounded = round_ring(ring, digits=5)
    assert rounded[0] == (139.0, 36.0)
    assert len(rounded) < len(ring)
    assert rounded[0] == rounded[-1]


def test_degenerate_rings_are_dropped():
    good = SQUARE_WITH_NOISE
    degenerate = [(139.0, 36.0), (139.0, 36.0), (139.0, 36.0), (139.0, 36.0)]
    kept = simplify_rings([good, degenerate], tolerance=0.001)
    assert len(kept) == 1


def test_count_points_sums_every_ring():
    assert count_points([[(0.0, 0.0)] * 3, [(1.0, 1.0)] * 4]) == 7


def test_ring_area_orders_rings_by_size():
    small = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]
    large = [(0.0, 0.0), (3.0, 0.0), (3.0, 3.0), (0.0, 3.0), (0.0, 0.0)]
    assert ring_area(large) > ring_area(small)


def test_simplification_actually_shrinks_a_dense_ring():
    dense = [(139.0 + index * 0.00001, 36.0) for index in range(200)]
    dense += [(140.0, 37.0), (139.0, 36.0)]
    simplified = simplify_rings([dense], tolerance=0.0001)
    assert count_points(simplified) < len(dense) / 2
