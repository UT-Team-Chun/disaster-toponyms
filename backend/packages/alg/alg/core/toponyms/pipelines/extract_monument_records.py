"""Read which places a disaster monument says were hit.

The Geospatial Information Authority publishes 2,469 monuments with a short
account of the disaster each one commemorates, and those accounts name the
hamlets that were destroyed. A monument stands where it was erected, which is
not always where the damage was, so the place names in the text are read out
separately and resolved on their own rather than taking the monument's own
coordinate as the answer.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from gateways.gsi.models.monument import DisasterMonument
from gateways.llm.operations.llm_operations import LLMOperations
from openai.types.chat import ChatCompletionMessageParam

from alg.core.toponyms.tools import llm_cache
from alg.core.toponyms.tools.claims import verify_quote
from alg.core.toponyms.tools.disaster_records import DisasterMention
from alg.core.toponyms.tools.hazard_text import hazard_types_from_text
from alg.models.toponym import DisasterRecord

PROMPT_PATH: Final = Path(__file__).parent.parent / "prompts" / "extract_monument_places_ja.md"

#: Bibliography entry every monument citation points at.
SOURCE_ID: Final = "gsi_denshouhi"

#: Only the places the text says were hit can corroborate a place name.
AFFECTED_ROLE: Final = "affected"

_MIN_QUOTE_CHARS: Final = 8
_MAX_NAME_CHARS: Final = 12
DEFAULT_WORKERS: Final = 12

#: The dataset writes the date inside the disaster label, e.g. 西日本水害(1953年6月28日).
_DATE_IN_NAME = re.compile(r"[(（]([^)）]*\d{3,4}年[^)）]*)[)）]")
_ADDRESS = re.compile(
    r"^(?P<pref>.{2,4}?[都道府県])(?P<municipality>.+?[市区町村])",
)

EXTRACTION_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["places"],
    "properties": {
        "places": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "role", "quote"],
                "properties": {
                    "name": {"type": "string"},
                    "role": {
                        "type": "string",
                        "enum": ["affected", "monument_site", "evacuation", "other"],
                    },
                    "quote": {"type": "string"},
                },
            },
        },
    },
}


@dataclass
class MonumentSetup:
    """How one monument reading run talks to the model."""

    stats: MonumentStats = field(default_factory=lambda: MonumentStats())
    llm: LLMOperations | None = None
    model_name: str = "unknown"
    effort: str | None = None
    workers: int = DEFAULT_WORKERS

    def signature(self) -> str:
        """Return the identity of this extraction setup, for the cache key."""
        return f"{self.model_name}|{self.effort or 'default'}"


@dataclass
class MonumentStats:
    """Counters describing one monument reading run."""

    monuments: int = 0
    skipped_no_lore: int = 0
    requested: int = 0
    cached: int = 0
    places_found: int = 0
    quote_rejected: int = 0
    affected: int = 0


def split_address(address: str | None) -> tuple[str | None, str | None]:
    """Split a monument address into prefecture and municipality."""
    match = _ADDRESS.match(address or "")
    if not match:
        return None, None
    return match.group("pref"), match.group("municipality")


def disaster_date(monument: DisasterMonument) -> str | None:
    """Return the date printed inside the disaster label, when there is one."""
    match = _DATE_IN_NAME.search(monument.disaster_name or "")
    return match.group(1) if match else None


def build_prompt(monument: DisasterMonument) -> str:
    """Render the extraction prompt for one monument."""
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return (
        template.replace("{monument_name}", monument.name)
        .replace("{address}", monument.address or "（記載なし）")
        .replace("{disaster_name}", monument.disaster_name or "（記載なし）")
        .replace("{disaster_kind}", monument.disaster_kind or "（記載なし）")
        .replace("{lore}", monument.lore or "")
    )


def _messages(prompt: str) -> list[ChatCompletionMessageParam]:
    """Wrap the prompt into the chat message list."""
    return [
        {
            "role": "system",
            "content": "あなたは碑文の記述に忠実な資料整理担当です。推測を一切加えません。",
        },
        {"role": "user", "content": prompt},
    ]


def _extract_monument(
    monument: DisasterMonument,
    setup: MonumentSetup,
) -> dict[str, Any] | None:
    """Return the places one monument names, using the cache when possible."""
    stats = setup.stats
    llm = setup.llm
    prompt = build_prompt(monument)
    key = llm_cache.cache_key(SOURCE_ID, setup.signature(), prompt)
    cached = llm_cache.load(key)
    if cached is not None:
        stats.cached += 1
        return cached
    if llm is None:
        return None
    payload = llm.generate_json(
        _messages(prompt), EXTRACTION_SCHEMA, schema_name="monument_places"
    )
    llm_cache.store(key, payload)
    stats.requested += 1
    return payload


def _mentions_of(
    monument: DisasterMonument,
    payload: dict[str, Any],
    model_name: str,
    stats: MonumentStats,
) -> list[DisasterMention]:
    """Build the mentions of one monument, dropping unverifiable excerpts."""
    lore = monument.lore or ""
    pref, municipality = split_address(monument.address)
    hazard_types = hazard_types_from_text(
        f"{monument.disaster_kind or ''} {monument.disaster_name or ''}",
    )
    date_text = disaster_date(monument)
    seen: set[str] = set()
    mentions: list[DisasterMention] = []
    for item in payload.get("places") or []:
        if not isinstance(item, dict):
            continue
        stats.places_found += 1
        name = str(item.get("name") or "").strip()
        quote = str(item.get("quote") or "").strip()
        if item.get("role") != AFFECTED_ROLE:
            continue
        if not name or len(name) > _MAX_NAME_CHARS or len(quote) < _MIN_QUOTE_CHARS:
            stats.quote_rejected += 1
            continue
        if not verify_quote(quote, lore):
            stats.quote_rejected += 1
            continue
        if name in seen:
            continue
        seen.add(name)
        stats.affected += 1
        mentions.append(
            DisasterMention(
                place_name=name,
                record=DisasterRecord(
                    relation="same_place_record",
                    name=monument.disaster_name or monument.name,
                    date_text=date_text,
                    hazard_types=hazard_types,
                    source_id=SOURCE_ID,
                    locator=monument.monument_id,
                    quote=quote,
                    quote_verified=True,
                    match_method="monument_place_name",
                    extracted_by=f"llm:{model_name}",
                ),
                pref=pref,
                municipality=municipality,
                lat=monument.lat,
                lon=monument.lon,
            ),
        )
    return mentions


def extract_monument_mentions(
    monuments: list[DisasterMonument],
    setup: MonumentSetup,
) -> tuple[list[DisasterMention], MonumentStats]:
    """Read every monument and return the places it says were hit.

    Args:
        monuments: The monument dataset.
        setup: Model, identifier, concurrency and counters for the run.

    Returns:
        The mentions and the counters for the run.

    """
    stats = setup.stats
    usable = [monument for monument in monuments if monument.lore]
    stats.monuments = len(monuments)
    stats.skipped_no_lore = len(monuments) - len(usable)

    if setup.llm is None or setup.workers <= 1:
        payloads = [_extract_monument(item, setup) for item in usable]
    else:
        with ThreadPoolExecutor(max_workers=setup.workers) as pool:
            payloads = list(pool.map(lambda item: _extract_monument(item, setup), usable))

    mentions: list[DisasterMention] = []
    for monument, payload in zip(usable, payloads, strict=True):
        if payload is None:
            continue
        mentions.extend(_mentions_of(monument, payload, setup.model_name, stats))
    return mentions, stats
