"""Turn model-extracted disaster mentions into verifiable records.

A source that explains a place name and a source that records a disaster there
are answering different questions, so the two are stored separately. Every
record keeps the excerpt it came from, and the excerpt is matched against the
source text before the record is kept.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from alg.core.toponyms.tools.claims import verify_quote
from alg.core.toponyms.tools.origin_vocabulary import is_natural_disaster
from alg.models.hazard import HAZARD_LABELS_JA
from alg.models.toponym import DisasterRecord, QuoteMedium, RecordMatchMethod

#: Relations a model may assign. Proximity is never one of them: it is measured.
EXTRACTED_RELATIONS: Final[tuple[str, ...]] = ("named_after", "same_place_record")

#: Shortest excerpt that can still identify a passage.
MIN_QUOTE_CHARS: Final = 8

#: JSON Schema fragment describing one recorded disaster, shared by the prompts.
RECORD_SCHEMA: Final[dict[str, Any]] = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["relation", "name", "date_text", "quote"],
        "properties": {
            "relation": {"type": "string", "enum": list(EXTRACTED_RELATIONS)},
            "name": {"type": "string"},
            "date_text": {"type": ["string", "null"]},
            "quote": {"type": "string"},
        },
    },
}


@dataclass(frozen=True)
class RecordContext:
    """Where a set of extracted disaster records comes from."""

    #: Text the quotes must appear in verbatim.
    source_text: str
    #: Bibliography entry the records cite.
    source_id: str
    #: Page or address a reader can open.
    locator: str | None = None
    #: Hazard types already established for the place.
    hazard_types: tuple[str, ...] = ()
    #: Model identifier recorded on each record.
    model_name: str = "unknown"
    #: How the place in the record was tied to the toponym.
    match_method: RecordMatchMethod = "entry_text"
    #: Whether the source text is a transcription or OCR output.
    quote_medium: QuoteMedium = "text"


def build_records(
    payload: Any,  # noqa: ANN401
    context: RecordContext,
) -> tuple[list[DisasterRecord], int]:
    """Build the disaster records of one finding, dropping unverifiable ones.

    Args:
        payload: The ``disaster_records`` array returned by the model.
        context: Where the records come from and how they are to be labelled.

    Returns:
        The accepted records and the number of rejected ones.

    """
    records: list[DisasterRecord] = []
    rejected = 0
    for item in payload or []:
        if not isinstance(item, dict):
            rejected += 1
            continue
        relation = str(item.get("relation") or "")
        name = str(item.get("name") or "").strip()
        quote = str(item.get("quote") or "").strip()
        if relation not in EXTRACTED_RELATIONS or not name or len(quote) < MIN_QUOTE_CHARS:
            rejected += 1
            continue
        if not verify_quote(quote, context.source_text):
            rejected += 1
            continue
        if context.match_method == "entry_text" and not is_natural_disaster(
            quote,
            context.hazard_types,
        ):
            rejected += 1
            continue
        date_text = item.get("date_text")
        records.append(
            DisasterRecord(
                relation=relation,  # type: ignore[arg-type]
                name=name,
                date_text=str(date_text).strip() if date_text else None,
                hazard_types=[
                    hazard  # type: ignore[misc]
                    for hazard in context.hazard_types
                    if hazard in HAZARD_LABELS_JA
                ],
                source_id=context.source_id,
                locator=context.locator,
                quote=quote,
                quote_verified=True,
                quote_medium=context.quote_medium,
                match_method=context.match_method,
                extracted_by=f"llm:{context.model_name}",
            ),
        )
    return records, rejected


@dataclass(frozen=True)
class DisasterMention:
    """A place a source names as having been hit by a disaster.

    The place a record names is not always the place the source is filed under:
    a monument stands where it was erected, and a gazetteer entry for a district
    can recount a flood in one of its villages. Resolving the named place is a
    separate step, so the mention travels with its own name and coordinate.
    """

    place_name: str
    record: DisasterRecord
    pref: str | None = None
    municipality: str | None = None
    lat: float | None = None
    lon: float | None = None
