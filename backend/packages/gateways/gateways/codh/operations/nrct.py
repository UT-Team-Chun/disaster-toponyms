"""Read the CODH index of historical place names.

『日本歴史地名大系』の地名項目データセット gives the name, reading, present-day
address and a coordinate for 80,502 historical place names, under CC BY 4.0.
The explanatory text of the encyclopaedia itself is not redistributable, so only
the index is used: to tell which modern municipality an old name belongs to.

Source: 『日本歴史地名大系』地名項目データセット（CODH作成）doi:10.20676/00000448
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Final

from gateways.codh.models.entry import HistoricalEntry
from gateways.http.connections import fetch_bytes

DATASET_URL: Final = "https://geoshape.ex.nii.ac.jp/nrct/dataset/nrct-20250719.csv"


def download_dataset(destination: Path, *, force: bool = False) -> Path:
    """Download the index CSV.

    Args:
        destination: Directory that receives the file.
        force: Re-download even when a cached copy exists.

    Returns:
        Path to the downloaded CSV.

    """
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "nrct.csv"
    if path.exists() and not force:
        return path
    path.write_bytes(fetch_bytes(DATASET_URL, suffix=".csv", force=force))
    return path


def _to_float(value: str) -> float | None:
    """Read a coordinate, tolerating blanks."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_entries(csv_path: Path) -> list[HistoricalEntry]:
    """Read the index.

    Args:
        csv_path: File downloaded with :func:`download_dataset`.

    Returns:
        Every entry in the index.

    """
    text = csv_path.read_text(encoding="utf-8-sig")
    return [
        HistoricalEntry(
            entry_id=row["id"],
            pref_code=row["都道府県コード"],
            name=row["名称"],
            reading=row["読み"] or None,
            municipality=row["上位地名"] or None,
            modern_address=row["出典住所"] or None,
            lat=_to_float(row["緯度"]),
            lon=_to_float(row["経度"]),
            method=row["推定手法"] or None,
            nihu_place_id=row["歴史地名ID"] or None,
        )
        for row in csv.DictReader(io.StringIO(text))
    ]
