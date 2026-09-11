"""Access to the GSI natural disaster monument dataset (自然災害伝承碑)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Final

from gateways.gsi.models.monument import DisasterMonument
from gateways.http.connections import fetch_bytes

#: Published archive of the monument dataset in GeoJSON form.
MONUMENT_GEOJSON_ZIP: Final = "https://www.gsi.go.jp/common/000250767.zip"
MONUMENT_INFO_URL: Final = "https://www.gsi.go.jp/bousaichiri/denshouhi_download.html"


def download_monuments(destination: Path, *, force: bool = False) -> Path:
    """Download and extract the monument GeoJSON archive.

    Args:
        destination: Directory that receives the extracted files.
        force: Re-download even when a cached copy exists.

    Returns:
        Path to the extracted ``.geojson`` file.

    Raises:
        FileNotFoundError: If the archive contains no GeoJSON payload.

    """
    raw = fetch_bytes(MONUMENT_GEOJSON_ZIP, suffix=".zip", force=force)
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / "denshouhi_geojson.zip"
    archive_path.write_bytes(raw)

    # Extract only the payload we need, and only under the destination, so that
    # a crafted archive cannot write outside it.
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.namelist():
            if not member.lower().endswith(".geojson"):
                continue
            target = destination / Path(member).name
            with archive.open(member) as source:
                target.write_bytes(source.read())
            return target
    msg = f"No .geojson file found inside {MONUMENT_GEOJSON_ZIP}"
    raise FileNotFoundError(msg)


def load_monuments(geojson_path: Path) -> list[DisasterMonument]:
    """Parse a monument GeoJSON file into typed records.

    Args:
        geojson_path: Path to the extracted GeoJSON file.

    Returns:
        Every monument carrying usable coordinates.

    """
    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    monuments: list[DisasterMonument] = []
    for feature in payload.get("features", []):
        properties = feature.get("properties") or {}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []
        expected_length = 2
        if len(coordinates) < expected_length:
            continue
        monuments.append(
            DisasterMonument(
                monument_id=str(properties.get("ID", "")),
                name=str(properties.get("碑名", "")).strip(),
                erected_year=(str(properties.get("建立年", "")).strip() or None),
                address=(str(properties.get("所在地", "")).strip() or None),
                disaster_name=(str(properties.get("災害名", "")).strip() or None),
                disaster_kind=(str(properties.get("災害種別", "")).strip() or None),
                lore=(str(properties.get("伝承内容", "")).strip() or None),
                lon=float(coordinates[0]),
                lat=float(coordinates[1]),
            ),
        )
    return monuments
