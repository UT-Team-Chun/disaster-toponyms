"""Download every public source the dataset is built from into ``data/raw``.

Running this makes the build reproducible from a clean clone. The downloaded
files are not committed: they are third-party datasets and scanned documents
whose licences allow use and citation but not necessarily redistribution.

Prerequisite: ``pdftotext`` from poppler, used with ``-layout`` so that the
printed columns of a place-name study survive the text extraction.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

from gateways.codh.operations.nrct import download_dataset
from gateways.gsi.operations.monuments import MONUMENT_GEOJSON_ZIP
from gateways.http.connections import ResourceMissingError, fetch_bytes
from gateways.ndl.operations.fulltext import fetch_book_pages
from gateways.nihu.operations.gazetteer import download_archive
from gateways.web.operations.page_text import fetch_page_text
from gateways.web.operations.wikipedia import fetch_article_text

from alg.core.toponyms.pipelines.ingest_historical_gazetteer import GAZETTEER_VOLUMES
from alg.core.toponyms.tools.paths import get_paths

GEOLONIA_CSV = "https://geolonia.github.io/japanese-addresses/latest.csv"

#: Municipal place-name studies and prefectural pages, as PDF.
PDF_SOURCES: dict[str, str] = {
    "kiryu_timeikou": (
        "https://www.city.kiryu.lg.jp/_res/projects/default_project"
        "/_page_/001/001/127/timeikou.pdf"
    ),
    "toyokawa_koaza": "https://www.city.toyokawa.lg.jp/material/files/group/2/4.pdf",
    "toyokawa_villages": "https://www.city.toyokawa.lg.jp/material/files/group/2/sankou1.pdf",
}

#: Prefectural and university pages read for place-name origins.
HTML_SOURCES: dict[str, str] = {
    "nagano_sabo_general": ("https://www.pref.nagano.lg.jp/sabo/manabu/chizu-yomitoku-2.html"),
    "nagano_sabo_landslide": ("https://www.pref.nagano.lg.jp/sabo/manabu/chizu-yomitoku-4.html"),
    "kagoshima_saigai_chimei": ("https://www.sci.kagoshima-u.ac.jp/oyo/name_r.html"),
}

#: Encyclopaedia articles quoted by the curated seeds.
WIKIPEDIA_TITLES: tuple[str, ...] = (
    "災害地名",
    "浪分神社",
    "南木曽町",
    "田老町",
)

#: News article documenting the dispute over the Yagi place name.
NEWS_SOURCES: dict[str, str] = {
    "yagi_jarakuji": (
        "https://news.yahoo.co.jp/articles/a356615f07c10cd18e85ca1b577dc7277b54986d"
    ),
}


def _extract_pdf_text(pdf_path: Path, text_path: Path) -> None:
    """Convert a PDF to layout-preserving text with poppler."""
    subprocess.run(  # noqa: S603
        ["pdftotext", "-layout", str(pdf_path), str(text_path)],  # noqa: S607
        check=True,
    )


def download_pdfs() -> list[str]:
    """Download the municipal studies and extract their text."""
    directory = get_paths().local_history_dir
    directory.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, url in PDF_SOURCES.items():
        pdf_path = directory / f"{name}.pdf"
        pdf_path.write_bytes(fetch_bytes(url, suffix=".pdf"))
        text_path = directory / f"{name}.txt"
        _extract_pdf_text(pdf_path, text_path)
        written.append(f"{name}: {text_path.stat().st_size} bytes of text")
    return written


def download_html() -> list[str]:
    """Download the prefectural pages as plain text."""
    directory = get_paths().local_history_dir
    directory.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, url in HTML_SOURCES.items():
        text = fetch_page_text(url)
        (directory / f"{name}.txt").write_text(text, encoding="utf-8")
        written.append(f"{name}: {len(text)} chars")
    return written


def download_wikipedia() -> list[str]:
    """Download the encyclopaedia articles used for quote verification."""
    directory = get_paths().raw_dir / "wikipedia"
    directory.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for title in WIKIPEDIA_TITLES:
        text = fetch_article_text(title)
        if text is None:
            written.append(f"{title}: 取得できませんでした")
            continue
        (directory / f"{title}.txt").write_text(text, encoding="utf-8")
        written.append(f"{title}: {len(text)} chars")
    return written


def download_news() -> list[str]:
    """Download the news article backing the disputed Yagi record."""
    directory = get_paths().raw_dir / "news"
    directory.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, url in NEWS_SOURCES.items():
        try:
            text = fetch_page_text(url)
        except ResourceMissingError:
            written.append(f"{name}: 記事が公開終了しています")
            continue
        (directory / f"{name}.txt").write_text(text, encoding="utf-8")
        written.append(f"{name}: {len(text)} chars")
    return written


def download_historical_places() -> list[str]:
    """Download the located historical place names and the modern-address index."""
    paths = get_paths()
    archive = download_archive(paths.nihu_dir)
    index = download_dataset(paths.codh_dir)
    return [
        f"歴史地名データ: {archive.name} ({archive.stat().st_size} bytes)",
        f"歴史地名大系索引: {index.name} ({index.stat().st_size} bytes)",
    ]


def download_gazetteer_text() -> list[str]:
    """Download the scanned text of the national gazetteer, one volume at a time."""
    written: list[str] = []
    for pid, label in GAZETTEER_VOLUMES:
        pages = fetch_book_pages(pid)
        characters = sum(len(page.contents) for page in pages)
        written.append(f"{label}: {len(pages)} コマ / {characters:,} 字 (pid {pid})")
    return written


def download_addresses() -> list[str]:
    """Download the nationwide address table."""
    path = get_paths().geolonia_csv
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(fetch_bytes(GEOLONIA_CSV, suffix=".csv"))
    return [f"geolonia: {path.stat().st_size} bytes"]


def download_monuments() -> list[str]:
    """Download and extract the natural disaster monument dataset."""
    directory = get_paths().monument_dir
    directory.mkdir(parents=True, exist_ok=True)
    archive_path = directory / "denshouhi_geojson.zip"
    archive_path.write_bytes(fetch_bytes(MONUMENT_GEOJSON_ZIP, suffix=".zip"))
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.namelist():
            if not member.lower().endswith(".geojson"):
                continue
            target = directory / Path(member).name
            with archive.open(member) as source:
                target.write_bytes(source.read())
            return [f"monuments: {target.name} ({target.stat().st_size} bytes)"]
    return ["monuments: GeoJSON がアーカイブに見つかりませんでした"]


def main() -> int:
    """Download every source and report what was written."""
    steps = (
        ("住所データ", download_addresses),
        ("歴史地名データ", download_historical_places),
        ("大日本地名辞書の全文", download_gazetteer_text),
        ("自然災害伝承碑", download_monuments),
        ("自治体の地名考 (PDF)", download_pdfs),
        ("都道府県の解説ページ", download_html),
        ("事典記事", download_wikipedia),
        ("報道記事", download_news),
    )
    for label, step in steps:
        print(f"==> {label}")
        for line in step():
            print(f"    {line}")
    print()
    print("完了。次に make build-data を実行してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
