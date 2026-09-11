"""Reduce polygon detail so the map can carry thousands of areas.

The census boundaries are surveyed at a precision the browser does not need.
Simplifying the rings and rounding the coordinates cuts the payload by roughly
an order of magnitude while keeping the shape recognisable at the zoom levels
the viewer uses.
"""

from __future__ import annotations

from typing import Final

Point = tuple[float, float]
Ring = list[Point]

#: Roughly 11 m at Japanese latitudes; finer than any useful map zoom here.
DEFAULT_TOLERANCE: Final = 0.0001
#: Five decimals is about one metre, which is well inside the source accuracy.
COORDINATE_DIGITS: Final = 5
#: A ring needs four points to close a triangle.
MIN_RING_POINTS: Final = 4


def _perpendicular_distance(point: Point, start: Point, end: Point) -> float:
    """Return the distance from a point to the line through start and end."""
    (px, py), (sx, sy), (ex, ey) = point, start, end
    dx, dy = ex - sx, ey - sy
    if dx == 0 and dy == 0:
        return ((px - sx) ** 2 + (py - sy) ** 2) ** 0.5
    numerator = abs(dy * px - dx * py + ex * sy - ey * sx)
    return numerator / ((dx * dx + dy * dy) ** 0.5)


def simplify_ring(ring: Ring, tolerance: float = DEFAULT_TOLERANCE) -> Ring:
    """Simplify a ring with the Ramer-Douglas-Peucker algorithm.

    Args:
        ring: Closed ring of longitude/latitude pairs.
        tolerance: Maximum deviation allowed, in degrees.

    Returns:
        A ring with fewer points, still closed.

    """
    if len(ring) <= MIN_RING_POINTS:
        return ring

    keep = [False] * len(ring)
    keep[0] = keep[-1] = True
    stack = [(0, len(ring) - 1)]
    while stack:
        start, end = stack.pop()
        if end <= start + 1:
            continue
        worst_index, worst_distance = start, 0.0
        for index in range(start + 1, end):
            distance = _perpendicular_distance(ring[index], ring[start], ring[end])
            if distance > worst_distance:
                worst_index, worst_distance = index, distance
        if worst_distance > tolerance:
            keep[worst_index] = True
            stack.append((start, worst_index))
            stack.append((worst_index, end))

    simplified = [point for point, keeping in zip(ring, keep, strict=True) if keeping]
    if len(simplified) < MIN_RING_POINTS:
        return ring
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return simplified


def round_ring(ring: Ring, digits: int = COORDINATE_DIGITS) -> Ring:
    """Round coordinates and drop points that collapse onto each other."""
    rounded: Ring = []
    for lon, lat in ring:
        point = (round(lon, digits), round(lat, digits))
        if not rounded or rounded[-1] != point:
            rounded.append(point)
    if len(rounded) >= 2 and rounded[0] != rounded[-1]:  # noqa: PLR2004
        rounded.append(rounded[0])
    return rounded


def simplify_rings(
    rings: list[Ring],
    tolerance: float = DEFAULT_TOLERANCE,
    digits: int = COORDINATE_DIGITS,
) -> list[Ring]:
    """Simplify and round every ring of a polygon, dropping degenerate ones.

    Args:
        rings: Rings as read from the source geometry.
        tolerance: Simplification tolerance in degrees.
        digits: Decimal places to keep.

    Returns:
        Rings that still enclose an area.

    """
    result: list[Ring] = []
    for ring in rings:
        simplified = round_ring(simplify_ring(ring, tolerance), digits)
        if len(simplified) >= MIN_RING_POINTS:
            result.append(simplified)
    return result


def ring_area(ring: Ring) -> float:
    """Return twice the signed area of a ring, used only to order rings by size."""
    total = 0.0
    for index in range(len(ring) - 1):
        x1, y1 = ring[index]
        x2, y2 = ring[index + 1]
        total += x1 * y2 - x2 * y1
    return abs(total)


def count_points(rings: list[Ring]) -> int:
    """Return the total number of points across every ring."""
    return sum(len(ring) for ring in rings)
