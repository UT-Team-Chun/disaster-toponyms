"""Download and read the census small-area boundaries published by e-Stat.

A place name is an area, not a dot. The 町丁・字等 boundaries from the census are
the finest administrative geometry published for the whole country, so they are
what the extent of a name can be drawn as. One archive is published per
prefecture; each holds a shapefile in WGS84 longitude and latitude.
"""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Final

import shapefile

from gateways.estat.models.boundary import SmallAreaBoundary
from gateways.http.connections import fetch_bytes

#: 2020 census, 町丁・字等 boundaries, shapefile in WGS84 longitude/latitude.
BOUNDARY_URL: Final = "https://www.e-stat.go.jp/gis/statmap-search/data"
SURVEY_ID: Final = "A002005212020"
#: The shapefile attribute table is encoded in CP932.
DBF_ENCODING: Final = "cp932"
#: e-Stat marks water-only polygons with this HCODE; they hold no residents.
WATER_HCODE: Final = "8154"


def _to_int(value: Any) -> int | None:  # noqa: ANN401
    """Read an integer attribute, tolerating blanks and floats."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:  # noqa: ANN401
    """Read a float attribute, tolerating blanks."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def download_prefecture(pref_code: str, destination: Path, *, force: bool = False) -> Path:
    """Download and extract one prefecture's boundary archive.

    Args:
        pref_code: Two-digit prefecture code, for example ``10`` for Gunma.
        destination: Directory that receives the extracted shapefile.
        force: Re-download even when a cached copy exists.

    Returns:
        Path to the extracted ``.shp`` file.

    Raises:
        FileNotFoundError: If the archive holds no shapefile.

    """
    raw = fetch_bytes(
        BOUNDARY_URL,
        params={
            "dlserveyId": SURVEY_ID,
            "code": pref_code,
            "coordSys": "1",
            "format": "shape",
            "downloadType": "5",
        },
        suffix=".zip",
        force=force,
    )
    directory = destination / pref_code
    directory.mkdir(parents=True, exist_ok=True)
    archive_path = directory / f"r2ka{pref_code}.zip"
    archive_path.write_bytes(raw)

    shp_path: Path | None = None
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.namelist():
            suffix = Path(member).suffix.lower()
            if suffix not in {".shp", ".shx", ".dbf", ".prj"}:
                continue
            target = directory / Path(member).name
            with archive.open(member) as source:
                target.write_bytes(source.read())
            if suffix == ".shp":
                shp_path = target
    if shp_path is None:
        msg = f"No shapefile found in the e-Stat archive for prefecture {pref_code}"
        raise FileNotFoundError(msg)
    return shp_path


def read_boundaries(shp_path: Path) -> list[SmallAreaBoundary]:
    """Read every small area from an extracted shapefile.

    Args:
        shp_path: Path to the ``.shp`` file.

    Returns:
        Areas that carry both a name and geometry, water polygons excluded.

    """
    reader = shapefile.Reader(str(shp_path), encoding=DBF_ENCODING)
    boundaries: list[SmallAreaBoundary] = []
    for record, shape in zip(reader.iterRecords(), reader.iterShapes(), strict=False):
        attributes = record.as_dict()
        name = str(attributes.get("S_NAME") or "").strip()
        if not name or str(attributes.get("HCODE") or "") == WATER_HCODE:
            continue

        points = [(float(x), float(y)) for x, y in shape.points]
        if not points:
            continue
        starts = list(shape.parts) or [0]
        bounds = [*starts, len(points)]
        rings = [points[bounds[i] : bounds[i + 1]] for i in range(len(starts))]
        rings = [ring for ring in rings if len(ring) >= 4]  # noqa: PLR2004
        if not rings:
            continue

        boundaries.append(
            SmallAreaBoundary(
                key_code=str(attributes.get("KEY_CODE") or "").strip(),
                pref_code=str(attributes.get("PREF") or "").strip(),
                pref_name=str(attributes.get("PREF_NAME") or "").strip(),
                municipality_code=str(attributes.get("CITY") or "").strip(),
                municipality_name=str(attributes.get("CITY_NAME") or "").strip(),
                name=name,
                area_m2=_to_float(attributes.get("AREA")),
                population=_to_int(attributes.get("JINKO")),
                households=_to_int(attributes.get("SETAI")),
                rings=rings,
            ),
        )
    return boundaries
