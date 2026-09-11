"""Load the hand-maintained YAML seeds under ``data/curated``.

Curated records carry the nationwide cases that no single machine-readable
source covers: renamed places, oral tradition, and cases where a widely
repeated story is contradicted by the archives. Each citation may name a local
copy of its source so that the quote is checked character-for-character during
the build, exactly like a model-extracted one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from alg.core.toponyms.tools.claims import verify_quote
from alg.core.toponyms.tools.element_matcher import match_elements
from alg.core.toponyms.tools.ids import make_toponym_id
from alg.core.toponyms.tools.normalize import (
    collapse_folded_japanese,
    collapse_folded_prose,
)
from alg.core.toponyms.tools.prefectures import pref_code
from alg.core.toponyms.tools.scoring import apply_scores
from alg.models.element import ElementDictionary, ToponymElement
from alg.models.source import Source
from alg.models.toponym import AdminArea, Toponym

#: Fields whose YAML folding artefacts must be removed before display.
_PROSE_FIELDS = ("etymology_summary", "dispute_note")


def _read_yaml(path: Path) -> Any:  # noqa: ANN401
    """Parse a YAML document, returning None for an empty file."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _entries(payload: Any, key: str) -> list[dict[str, Any]]:  # noqa: ANN401
    """Pull a list of records out of either a mapping or a bare sequence."""
    if isinstance(payload, dict):
        return list(payload.get(key) or [])
    return list(payload or [])


def load_sources(path: Path) -> list[Source]:
    """Load the source bibliography.

    Args:
        path: Path to ``sources.yaml``.

    Returns:
        Every declared source; an empty list when the file is missing.

    """
    if not path.exists():
        return []
    return [Source.model_validate(entry) for entry in _entries(_read_yaml(path) or {}, "sources")]


def load_elements(path: Path) -> ElementDictionary:
    """Load the place-name element dictionary.

    Args:
        path: Path to ``elements.yaml``.

    Returns:
        The element dictionary; empty when the file is missing.

    """
    if not path.exists():
        return ElementDictionary()
    return ElementDictionary(
        elements=[
            ToponymElement.model_validate(entry)
            for entry in _entries(_read_yaml(path) or {}, "elements")
        ],
    )


def _clean_prose(record: dict[str, Any]) -> None:
    """Strip YAML folding spaces from the prose fields of a record."""
    for field in _PROSE_FIELDS:
        value = record.get(field)
        if isinstance(value, str):
            record[field] = collapse_folded_prose(value).strip()
    review = record.get("review")
    if isinstance(review, dict) and isinstance(review.get("note"), str):
        review["note"] = collapse_folded_prose(review["note"]).strip()


def _resolve_evidence(
    record: dict[str, Any],
    raw_dir: Path,
    warnings: list[str],
) -> None:
    """Verify every quote against its local source copy."""
    name = record.get("name", "?")
    for item in record.get("evidence") or []:
        if not isinstance(item, dict):
            continue
        claim = item.get("claim")
        if isinstance(claim, str):
            item["claim"] = collapse_folded_prose(claim).strip()
        quote = item.get("quote")
        if isinstance(quote, str):
            # Quotes keep their original spacing; only the newline folding
            # introduced by YAML between two Japanese characters is removed.
            item["quote"] = collapse_folded_japanese(quote).strip()

        target = item.pop("verify_against", None)
        quote = item.get("quote")
        if not target or not isinstance(quote, str) or not quote:
            item.setdefault("quote_verified", False)
            continue

        source_path = raw_dir / str(target)
        if not source_path.exists():
            warnings.append(f"{name}: 検証用資料が見つかりません ({target})")
            item["quote_verified"] = False
            continue

        verified = verify_quote(quote, source_path.read_text(encoding="utf-8"))
        item["quote_verified"] = verified
        if not verified:
            warnings.append(f"{name}: 引用が資料と一致しません ({target})")


def _prepare_record(
    raw: dict[str, Any],
    dictionary: ElementDictionary,
    *,
    dataset: str,
    raw_dir: Path,
    warnings: list[str],
) -> Toponym:
    """Normalise one YAML record into a :class:`Toponym`."""
    record = dict(raw)
    _clean_prose(record)
    _resolve_evidence(record, raw_dir, warnings)

    admin_payload = dict(record.get("admin") or {})
    if not admin_payload.get("pref_code"):
        code = pref_code(admin_payload.get("pref"))
        if code:
            admin_payload["pref_code"] = code
    record["admin"] = admin_payload
    record.setdefault("dataset", dataset)

    admin = AdminArea.model_validate(admin_payload)
    name = str(record.get("name", ""))
    if not record.get("id"):
        record["id"] = make_toponym_id(name, admin)
    if not record.get("elements"):
        matches = match_elements(name, record.get("reading"), dictionary)
        record["elements"] = [match.to_ref().model_dump() for match in matches]

    return apply_scores(Toponym.model_validate(record))


def load_curated_toponyms(
    directory: Path,
    dictionary: ElementDictionary,
    *,
    raw_dir: Path,
) -> tuple[list[Toponym], list[str]]:
    """Load every curated toponym file in a directory.

    Args:
        directory: Directory holding ``*.yaml`` files, each a list of records.
        dictionary: Element dictionary used to tag names that declare none.
        raw_dir: Root of the downloaded sources used for quote verification.

    Returns:
        The records, and any warnings raised while verifying quotes.

    """
    if not directory.exists():
        return [], []
    records: list[Toponym] = []
    warnings: list[str] = []
    for path in sorted(directory.glob("*.yaml")):
        payload = _read_yaml(path)
        if not payload:
            continue
        records.extend(
            _prepare_record(
                entry,
                dictionary,
                dataset=path.stem,
                raw_dir=raw_dir,
                warnings=warnings,
            )
            for entry in _entries(payload, "toponyms")
        )
    return records, warnings
