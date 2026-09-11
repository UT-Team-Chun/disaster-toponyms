"""Extract evidence-backed toponyms from prose documents with an LLM.

Municipal disaster guides, prefectural pages and encyclopaedia articles state
place-name origins in running prose rather than in a table, so the structure has
to be recovered by a model. Every excerpt the model returns is then matched
character-for-character against the source text, and anything that fails is
discarded: the model is allowed to locate and organise claims, never to author
them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from gateways.llm.operations.llm_operations import LLMOperations
from openai.types.chat import ChatCompletionMessageParam

from alg.core.toponyms.tools import llm_cache
from alg.core.toponyms.tools.claims import verify_quote
from alg.core.toponyms.tools.disaster_records import (
    RECORD_SCHEMA,
    RecordContext,
    build_records,
)
from alg.core.toponyms.tools.element_matcher import match_elements
from alg.core.toponyms.tools.ids import make_toponym_id
from alg.core.toponyms.tools.prefectures import pref_code
from alg.core.toponyms.tools.scoring import MAX_ORIGIN_LEVEL, apply_scores
from alg.models.element import ElementDictionary
from alg.models.hazard import HAZARD_LABELS_JA
from alg.models.toponym import AdminArea, Evidence, Toponym

PROMPT_PATH: Final = Path(__file__).parent.parent / "prompts" / "extract_toponyms_ja.md"
#: Characters per request; municipal guides and articles fit in one or two chunks.
CHUNK_CHARS: Final = 9000
CHUNK_OVERLAP: Final = 400
_MIN_QUOTE_CHARS = 8
_MAX_NAME_CHARS = 12

HAZARD_ENUM: Final[list[str]] = list(HAZARD_LABELS_JA)

EXTRACTION_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["findings"],
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "name",
                    "reading",
                    "prefecture",
                    "municipality",
                    "area",
                    "hazard_types",
                    "evidence_level",
                    "stance",
                    "quote",
                    "claim",
                    "summary",
                    "disaster_records",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "reading": {"type": ["string", "null"]},
                    "prefecture": {"type": ["string", "null"]},
                    "municipality": {"type": ["string", "null"]},
                    "area": {"type": ["string", "null"]},
                    "hazard_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": HAZARD_ENUM},
                    },
                    "evidence_level": {"type": "integer", "enum": [1, 2]},
                    "stance": {"type": "string", "enum": ["supports", "disputes"]},
                    "quote": {"type": "string"},
                    "claim": {"type": "string"},
                    "summary": {"type": "string"},
                    "disaster_records": RECORD_SCHEMA,
                },
            },
        },
    },
}


@dataclass(frozen=True)
class ProseDocument:
    """A prose source to mine for place-name evidence."""

    doc_id: str
    source_id: str
    source_title: str
    text: str
    evidence_kind: str = "official"
    pref_hint: str | None = None
    municipality_hint: str | None = None
    locator: str | None = None

    def location_hint(self) -> str:
        """Describe the default location so the model does not have to guess."""
        parts = [part for part in (self.pref_hint, self.municipality_hint) if part]
        if not parts:
            return "所在地の既定値: なし（資料の記述に従うこと）"
        return f"所在地の既定値: {''.join(parts)}（資料が別の地名を示す場合はそれに従うこと）"


@dataclass
class ExtractionStats:
    """Counters describing one extraction run."""

    findings: int = 0
    accepted: int = 0
    quote_rejected: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    cached_chunks: int = 0
    live_chunks: int = 0


def chunk_text(text: str, *, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split a document into overlapping chunks that fit one request.

    Args:
        text: Full document text.
        size: Maximum characters per chunk.
        overlap: Characters repeated between neighbouring chunks.

    Returns:
        Chunks in document order.

    """
    if len(text) <= size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - overlap
    return chunks


def build_prompt(document: ProseDocument, chunk: str) -> str:
    """Render the extraction prompt for one chunk."""
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return (
        template.replace("{source_title}", document.source_title)
        .replace("{location_hint}", document.location_hint())
        .replace("{document}", chunk)
    )


def _messages(prompt: str) -> list[ChatCompletionMessageParam]:
    """Wrap the prompt into the chat message list."""
    return [
        {
            "role": "system",
            "content": "あなたは資料に忠実な地理学の資料整理担当です。推測を一切加えません。",
        },
        {"role": "user", "content": prompt},
    ]


def _extract_chunk(
    document: ProseDocument,
    chunk: str,
    llm: LLMOperations | None,
    stats: ExtractionStats,
    signature: str,
) -> list[dict[str, Any]]:
    """Return the findings for one chunk, using the cache when possible."""
    prompt = build_prompt(document, chunk)
    key = llm_cache.cache_key(document.source_id, signature, prompt)
    cached = llm_cache.load(key)
    if cached is not None:
        stats.cached_chunks += 1
        return list(cached.get("findings", []))
    if llm is None:
        return []
    payload = llm.generate_json(
        _messages(prompt),
        EXTRACTION_SCHEMA,
        schema_name="toponym_extraction",
    )
    llm_cache.store(key, payload)
    stats.live_chunks += 1
    return list(payload.get("findings", []))


def _admin_from(finding: dict[str, Any], document: ProseDocument) -> AdminArea:
    """Build the administrative context of one finding."""
    pref = finding.get("prefecture") or document.pref_hint
    municipality = finding.get("municipality") or document.municipality_hint
    return AdminArea(
        pref=pref,
        pref_code=pref_code(pref),
        municipality=municipality,
        oaza=finding.get("area"),
        koaza=finding.get("name"),
    )


def _to_record(
    finding: dict[str, Any],
    document: ProseDocument,
    dictionary: ElementDictionary,
    model_name: str,
    stats: ExtractionStats,
) -> Toponym | None:
    """Convert one accepted finding into a toponym record."""
    name = str(finding.get("name") or "").strip()
    quote = str(finding.get("quote") or "").strip()
    if not name or len(name) > _MAX_NAME_CHARS or len(quote) < _MIN_QUOTE_CHARS:
        return None

    admin = _admin_from(finding, document)
    reading = finding.get("reading") or None
    matches = match_elements(name, reading, dictionary)
    stance = "disputes" if finding.get("stance") == "disputes" else "supports"
    hazard_types = list(finding.get("hazard_types") or [])
    evidence = Evidence(
        kind=document.evidence_kind,  # type: ignore[arg-type]
        stance=stance,  # type: ignore[arg-type]
        source_id=document.source_id,
        locator=document.locator,
        quote=quote,
        claim=str(finding.get("claim") or "").strip() or f"{name}に関する記述",
        level=min(int(finding.get("evidence_level") or 1), MAX_ORIGIN_LEVEL),
        extracted_by=f"llm:{model_name}",
        quote_verified=True,
    )
    records, rejected = build_records(
        finding.get("disaster_records"),
        RecordContext(
            source_text=document.text,
            source_id=document.source_id,
            locator=document.locator,
            hazard_types=tuple(hazard_types),
            model_name=model_name,
        ),
    )
    stats.records_accepted += len(records)
    stats.records_rejected += rejected
    return apply_scores(
        Toponym(
            id=make_toponym_id(name, admin, salt=document.doc_id),
            name=name,
            reading=reading,
            status="current",
            admin=admin,
            hazard_types=hazard_types,
            elements=[match.to_ref() for match in matches],
            etymology_summary=str(finding.get("summary") or "").strip(),
            evidence=[evidence],
            disaster_records=records,
            dataset=document.doc_id,
        ),
    )


def extract_from_document(
    document: ProseDocument,
    dictionary: ElementDictionary,
    *,
    llm: LLMOperations | None = None,
    model_name: str = "unknown",
    effort: str | None = None,
) -> tuple[list[Toponym], ExtractionStats]:
    """Mine one prose document for evidence-backed toponyms.

    Args:
        document: Source text and its bibliographic context.
        dictionary: Element dictionary used to tag the names.
        llm: LLM operations, or None to use only cached extractions.
        model_name: Model identifier recorded on each citation.
        effort: Reasoning budget requested, recorded so a change re-reads.

    Returns:
        The accepted records and the counters for the run.

    """
    stats = ExtractionStats()
    records: dict[str, Toponym] = {}
    signature = f"{model_name}|{effort or 'default'}"
    for chunk in chunk_text(document.text):
        for finding in _extract_chunk(document, chunk, llm, stats, signature):
            stats.findings += 1
            quote = str(finding.get("quote") or "")
            if not verify_quote(quote, document.text):
                stats.quote_rejected += 1
                continue
            record = _to_record(finding, document, dictionary, model_name, stats)
            if record is None:
                stats.quote_rejected += 1
                continue
            previous = records.get(record.id)
            if previous is None or record.evidence_level > previous.evidence_level:
                records[record.id] = record
                stats.accepted += 1
    return list(records.values()), stats
