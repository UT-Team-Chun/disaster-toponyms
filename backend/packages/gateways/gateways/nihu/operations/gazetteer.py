"""Read the historical place-name dataset published by NIHU.

Modern geocoders only know present-day addresses, so a village or small section
that was renamed or absorbed a century ago cannot be placed with them. This
dataset carries 53,528 entries read out of Yoshida Tōgo's national gazetteer and
242,544 read off the old 1:50,000 maps, each with a coordinate, the reading and
the spelling as originally printed.

Source: 人間文化研究機構「歴史地名データ」 (DOI 10.57408/nihu.dc.478706)
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path
from typing import Final

from gateways.http.connections import fetch_bytes
from gateways.nihu.models.place import HistoricalPlace

#: Published archive of the whole dataset, several CSV files in one zip.
ARCHIVE_URL: Final = "https://www.bridge.nihu.jp/researchdata/file/20220313_cNxFtc"

#: Member names are stored in CP932 without the UTF-8 flag, so zipfile hands
#: them back decoded as CP437 and they have to be re-encoded to be read.
_LEGACY_ENCODING: Final = "cp437"
_MEMBER_ENCODING: Final = "cp932"

PLACES_MEMBER: Final = "地名.txt"
PARENTS_MEMBER: Final = "地名_上位地名.txt"
ALIASES_MEMBER: Final = "地名_別名.txt"
ATTRIBUTES_MEMBER: Final = "地名_属性.txt"

READING_KIND: Final = "ヨミ"
OLD_FORM_KIND: Final = "旧字原記載"

#: Hierarchy labels used by the two halves of the dataset.
_PROVINCE_LEVELS: Final = ("国", "旧国名")
_DISTRICT_LEVEL: Final = "郡"
_PREFECTURE_LEVEL: Final = "都道府県名"

_VOLUME_PAGE = re.compile(r"(\d+)巻\s*(\d+)頁")
_PARENT_ENTRY = re.compile(r"[(（]\s*([^)）]+?)\s*[)）]")


def download_archive(destination: Path, *, force: bool = False) -> Path:
    """Download the dataset archive.

    Args:
        destination: Directory that receives the archive.
        force: Re-download even when a cached copy exists.

    Returns:
        Path to the downloaded zip file.

    """
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / "nihu_rekishi_chimei.zip"
    if path.exists() and not force:
        return path
    path.write_bytes(fetch_bytes(ARCHIVE_URL, suffix=".zip", force=force))
    return path


def _member_map(archive: zipfile.ZipFile) -> dict[str, str]:
    """Map the readable member name to the name stored in the archive."""
    mapping: dict[str, str] = {}
    for info in archive.infolist():
        try:
            readable = info.filename.encode(_LEGACY_ENCODING).decode(_MEMBER_ENCODING)
        except (UnicodeEncodeError, UnicodeDecodeError):
            readable = info.filename
        mapping[readable] = info.filename
    return mapping


def _read_rows(archive: zipfile.ZipFile, stored_name: str) -> list[dict[str, str]]:
    """Read one CSV member into dictionaries."""
    text = archive.read(stored_name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _to_float(value: str) -> float | None:
    """Read a coordinate, tolerating blanks."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_spelling_pairs(zip_path: Path) -> list[tuple[str, str]]:
    """Read every (printed spelling, modern spelling) pair in the archive.

    Almost all of these pairs come from the entries read off the old maps, so a
    caller that only wants the gazetteer half still has to read the whole file to
    learn how pre-war characters map to modern ones. Reading just these two
    columns keeps that cheap.

    Args:
        zip_path: Archive downloaded with :func:`download_archive`.

    Returns:
        Pairs of the spelling as printed and the modern transcription.

    Raises:
        FileNotFoundError: If the archive lacks the expected members.

    """
    with zipfile.ZipFile(zip_path) as archive:
        members = _member_map(archive)
        missing = [name for name in (PLACES_MEMBER, ALIASES_MEMBER) if name not in members]
        if missing:
            msg = f"{zip_path} is missing {', '.join(missing)}"
            raise FileNotFoundError(msg)
        modern = {row["ID"]: row["地名"] for row in _read_rows(archive, members[PLACES_MEMBER])}
        return [
            (row["別名"], modern[row["地名ID"]])
            for row in _read_rows(archive, members[ALIASES_MEMBER])
            if row["種別"] == OLD_FORM_KIND and row["地名ID"] in modern
        ]


def load_historical_places(
    zip_path: Path,
    *,
    sources: frozenset[str] | None = None,
) -> list[HistoricalPlace]:
    """Read the located historical place names out of the archive.

    Args:
        zip_path: Archive downloaded with :func:`download_archive`.
        sources: Keep only entries from these sources; None keeps every entry.

    Returns:
        The entries, with their readings, old spellings and hierarchy attached.

    Raises:
        FileNotFoundError: If the archive lacks the expected members.

    """
    with zipfile.ZipFile(zip_path) as archive:
        members = _member_map(archive)
        missing = [
            name
            for name in (PLACES_MEMBER, PARENTS_MEMBER, ALIASES_MEMBER, ATTRIBUTES_MEMBER)
            if name not in members
        ]
        if missing:
            msg = f"{zip_path} is missing {', '.join(missing)}"
            raise FileNotFoundError(msg)

        attributes = {
            row["番号"]: (row["区分"], row["属性"])
            for row in _read_rows(archive, members[ATTRIBUTES_MEMBER])
        }
        rows = _read_rows(archive, members[PLACES_MEMBER])
        kept = {row["ID"] for row in rows if sources is None or row["出典"] in sources}
        hierarchy: dict[str, dict[str, str]] = {}
        for row in _read_rows(archive, members[PARENTS_MEMBER]):
            if row["地名ID"] in kept:
                hierarchy.setdefault(row["地名ID"], {})[row["階層種別"]] = row["上位地名"]
        readings: dict[str, list[str]] = {}
        old_forms: dict[str, list[str]] = {}
        for row in _read_rows(archive, members[ALIASES_MEMBER]):
            if row["地名ID"] not in kept:
                continue
            if row["種別"] == READING_KIND:
                readings.setdefault(row["地名ID"], []).append(row["別名"])
            elif row["種別"] == OLD_FORM_KIND:
                old_forms.setdefault(row["地名ID"], []).append(row["別名"])

    places: list[HistoricalPlace] = []
    for row in rows:
        place_id = row["ID"]
        if place_id not in kept:
            continue
        category, attribute = attributes.get(row["属性"], (None, None))
        detail = row["出典詳細"] or None
        volume_page = _VOLUME_PAGE.search(detail) if detail else None
        parent = _PARENT_ENTRY.search(detail) if detail else None
        levels = hierarchy.get(place_id, {})
        province = next((levels[key] for key in _PROVINCE_LEVELS if key in levels), None)
        places.append(
            HistoricalPlace(
                place_id=place_id,
                name=row["地名"],
                attribute=attribute,
                category=category,
                lat=_to_float(row["緯度"]),
                lon=_to_float(row["経度"]),
                source=row["出典"],
                source_detail=detail,
                volume=int(volume_page.group(1)) if volume_page else None,
                page=int(volume_page.group(2)) if volume_page else None,
                parent_entry=parent.group(1) if parent else None,
                province=province,
                district=levels.get(_DISTRICT_LEVEL),
                prefecture=levels.get(_PREFECTURE_LEVEL),
                readings=readings.get(place_id, []),
                old_forms=old_forms.get(place_id, []),
            ),
        )
    return places
