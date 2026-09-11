"""Read the national gazetteer and keep what it says about place-name origins.

This is what takes the dataset off one municipality and onto the whole country.
Yoshida Tōgo's 大日本地名辞書 covers every province, is out of copyright, and
explains the origin of a large share of the names it lists. The scanned text is
split into entries, each entry is located through the historical place-name
dataset, and a model is asked only to organise what the entry states — every
excerpt it returns is then matched against that entry's own text.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from gateways.llm.operations.llm_operations import LLMOperations
from gateways.ndl.models.page import NdlPage
from gateways.nihu.models.place import GAZETTEER_SOURCE, HistoricalPlace
from openai.types.chat import ChatCompletionMessageParam

from alg.core.toponyms.parsers.dainihon_chimei import (
    GazetteerEntry,
    ParseStats,
    parse_pages,
)
from alg.core.toponyms.tools import llm_cache
from alg.core.toponyms.tools.claims import verify_quote
from alg.core.toponyms.tools.disaster_records import (
    RECORD_SCHEMA,
    DisasterMention,
    RecordContext,
    build_records,
)
from alg.core.toponyms.tools.element_matcher import match_elements
from alg.core.toponyms.tools.geocode import get_geolonia_index
from alg.core.toponyms.tools.historical_index import UNREADABLE, HistoricalIndex
from alg.core.toponyms.tools.ids import make_toponym_id
from alg.core.toponyms.tools.origin_vocabulary import level_for
from alg.core.toponyms.tools.prefectures import pref_code
from alg.core.toponyms.tools.scoring import apply_scores
from alg.models.element import ElementDictionary
from alg.models.hazard import HAZARD_LABELS_JA
from alg.models.toponym import (
    AdminArea,
    Evidence,
    Location,
    LocationPrecision,
    Toponym,
)

PROMPT_PATH: Final = Path(__file__).parent.parent / "prompts" / "extract_gazetteer_entry_ja.md"

#: Volumes of the second edition, held by the National Diet Library.
GAZETTEER_VOLUMES: Final[tuple[tuple[str, str], ...]] = (
    ("2937057", "上巻（上方・中国四国・西国）"),
    ("2937058", "中巻（北陸・東国・坂東）"),
    ("2937059", "下巻（奥羽ほか）"),
    ("2937060", "続編（北海道・琉球ほか）"),
)

#: Bibliography entry every citation from this book points at.
SOURCE_ID: Final = "yoshida_dainihon_chimei_1907"

#: How precisely a coordinate locates each kind of entry.
PRECISION_BY_ATTRIBUTE: Final[dict[str, LocationPrecision]] = {
    "字": "koaza",
    "町": "oaza",
    "村": "village",
    "郷・里": "village",
    "荘園・新田": "village",
    "郡": "municipality",
    "市": "municipality",
    "区": "municipality",
    "県": "prefecture",
    "国": "prefecture",
    "地方": "prefecture",
}

#: Categories that are not place names and carry no warning.
EXCLUDED_CATEGORIES: Final[frozenset[str]] = frozenset({"建物", "地名以外", "判別不能"})

#: Kinds that name a monument or an event site rather than an inhabited place.
#: A waterfall or a hot spring is a landform and stays.
EXCLUDED_ATTRIBUTES: Final[frozenset[str]] = frozenset(
    {
        "旧跡",
        "名所・名勝",
        "墓地",
        "その他（名所旧跡）",
        "人名",
        "産業名",
        # A province, district or city is far too large for a point on a hazard
        # map to say anything useful about.
        "国",
        "郡",
        "県",
        "市",
        "区",
        "地方",
    },
)


_MIN_QUOTE_CHARS: Final = 8
#: An entry with almost no text cannot support a citation.
MIN_BODY_CHARS: Final = 30
#: Requests in flight at once. The extraction is network-bound, not CPU-bound.
DEFAULT_WORKERS: Final = 12

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
                    "place_name",
                    "origin_kind",
                    "origin_quote",
                    "claim",
                    "summary",
                    "hazard_types",
                    "disputed",
                    "disaster_records",
                ],
                "properties": {
                    "place_name": {"type": "string"},
                    "origin_kind": {
                        "type": "string",
                        "enum": ["terrain", "disaster", "substitution"],
                    },
                    "origin_quote": {"type": "string"},
                    "claim": {"type": "string"},
                    "summary": {"type": "string"},
                    "hazard_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(HAZARD_LABELS_JA)},
                    },
                    "disputed": {"type": "boolean"},
                    "disaster_records": RECORD_SCHEMA,
                },
            },
        },
    },
}


@dataclass
class GazetteerStats:
    """Counters describing one gazetteer ingest."""

    parse: ParseStats = field(default_factory=ParseStats)
    entries: int = 0
    screened_out: int = 0
    excluded_kind: int = 0
    requested: int = 0
    cached: int = 0
    findings: int = 0
    unknown_place: int = 0
    disputed_only: int = 0
    origin_found: int = 0
    quote_rejected: int = 0
    located: int = 0
    unlocated: int = 0
    records: int = 0
    mentions: int = 0


@dataclass
class _RecordBuildContext:
    """Everything building one entry's records needs beyond the entry itself."""

    index: HistoricalIndex
    dictionary: ElementDictionary
    model_name: str
    stats: GazetteerStats


def build_prompt(entry: GazetteerEntry, children: list[HistoricalPlace]) -> str:
    """Render the extraction prompt for one entry.

    Args:
        entry: The entry to read.
        children: Places the source describes inside this entry, which the model
            may also attribute an origin to.

    Returns:
        The rendered prompt.

    """
    template = PROMPT_PATH.read_text(encoding="utf-8")
    listed = "、".join(place.name for place in children) or "（なし）"
    return (
        template.replace("{heading}", entry.heading)
        .replace("{reading}", entry.reading or "（読み不明）")
        .replace("{province}", entry.province)
        .replace("{district}", entry.district or "")
        .replace("{children}", listed)
        .replace("{body}", entry.text)
    )


def _messages(prompt: str) -> list[ChatCompletionMessageParam]:
    """Wrap the prompt into the chat message list."""
    return [
        {
            "role": "system",
            "content": "あなたは明治期の地誌に忠実な資料整理担当です。推測を一切加えません。",
        },
        {"role": "user", "content": prompt},
    ]


def is_place_entry(place: HistoricalPlace) -> bool:
    """Return True when the entry names a place rather than a building or a site."""
    return (place.category or "") not in EXCLUDED_CATEGORIES and (
        place.attribute or ""
    ) not in EXCLUDED_ATTRIBUTES


def screen(entries: list[GazetteerEntry], stats: GazetteerStats) -> list[GazetteerEntry]:
    """Keep the entries that name a place and carry text to read.

    Screening on period vocabulary was tried and dropped: measured against the
    model's own reading, entries without an origin marker turned out to state an
    origin as often as entries with one, so the filter only lost records.
    """
    kept: list[GazetteerEntry] = []
    for entry in entries:
        stats.entries += 1
        if not is_place_entry(entry.place):
            stats.excluded_kind += 1
            continue
        if len(entry.text) < MIN_BODY_CHARS:
            stats.screened_out += 1
            continue
        kept.append(entry)
    return kept


def _extract_entry(
    entry: GazetteerEntry,
    index: HistoricalIndex,
    setup: ExtractionSetup,
) -> dict[str, Any] | None:
    """Return the structured reading of one entry, using the cache when possible."""
    stats = setup.stats
    llm = setup.llm
    prompt = build_prompt(entry, index.children_of(entry.place))
    key = llm_cache.cache_key(SOURCE_ID, setup.signature(), prompt)
    cached = llm_cache.load(key)
    if cached is not None:
        stats.cached += 1
        return cached
    if llm is None:
        return None
    payload = llm.generate_json(
        _messages(prompt),
        EXTRACTION_SCHEMA,
        schema_name="gazetteer_entry",
    )
    llm_cache.store(key, payload)
    stats.requested += 1
    return payload


def _admin_for(place: HistoricalPlace) -> AdminArea:
    """Build the administrative context of a historical entry."""
    admin = AdminArea(
        province=place.province,
        district=place.district,
        historical_village=place.name if place.attribute in {"村", "郷・里"} else None,
    )
    if place.lat is None or place.lon is None:
        return admin
    nearest = get_geolonia_index().nearest_address(place.lat, place.lon)
    if nearest is not None:
        admin.pref = nearest.pref
        admin.pref_code = pref_code(nearest.pref)
        admin.municipality = nearest.municipality
        admin.municipality_code = nearest.municipality_code
        admin.oaza = nearest.oaza
    return admin


def _location_for(place: HistoricalPlace) -> Location | None:
    """Build the location of a historical entry, with an honest precision."""
    if place.lat is None or place.lon is None:
        return None
    return Location(
        lat=place.lat,
        lon=place.lon,
        precision=PRECISION_BY_ATTRIBUTE.get(place.attribute or "", "feature"),
        geocode_source="nihu:歴史地名データ",
    )


def _status(place: HistoricalPlace, admin: AdminArea) -> str:
    """Say whether the name is still in use where the entry places it."""
    if not admin.pref or not admin.municipality:
        return "historical"
    if get_geolonia_index().has_name(admin.pref, admin.municipality, place.name):
        return "current"
    return "historical"


def _resolve_place(
    name: str,
    entry: GazetteerEntry,
    index: HistoricalIndex,
) -> HistoricalPlace | None:
    """Find the located place a finding names.

    A finding may only be about the entry's own heading or about a place the
    source describes inside that entry. Anything else would attach an excerpt to
    a place the entry is not actually about.

    Args:
        name: Place name the model returned.
        entry: The entry the excerpt came from.
        index: Index of located historical place names.

    Returns:
        The located place, or None when the name is not one of the two.

    """
    folded = index.modernise(name).replace(UNREADABLE, "")
    if not folded:
        return None
    if folded in {
        index.modernise(entry.place.name),
        index.modernise(entry.heading).replace(UNREADABLE, ""),
    }:
        return entry.place
    for child in index.children_of(entry.place):
        if index.modernise(child.name) == folded:
            return child
    return None


def _build_record(
    finding: dict[str, Any],
    place: HistoricalPlace,
    entry: GazetteerEntry,
    context: _RecordBuildContext,
) -> tuple[Toponym | None, list[DisasterMention]]:
    """Turn one finding into a toponym and any records it cannot support."""
    stats = context.stats
    admin = _admin_for(place)
    locator = entry.viewer_url()
    hazard_types = list(finding.get("hazard_types") or [])
    records, rejected = build_records(
        finding.get("disaster_records"),
        RecordContext(
            source_text=entry.text,
            source_id=SOURCE_ID,
            locator=locator,
            hazard_types=tuple(hazard_types),
            model_name=context.model_name,
            quote_medium="ocr",
        ),
    )
    stats.quote_rejected += rejected
    stats.records += len(records)

    quote = str(finding.get("origin_quote") or "").strip()
    summary = str(finding.get("summary") or "").strip()
    # The level follows the words the cited passage actually contains, not the
    # label the model put on it.
    level = level_for(str(finding.get("origin_kind") or ""), f"{quote}{summary}")
    if level is None or len(quote) < _MIN_QUOTE_CHARS or not verify_quote(quote, entry.text):
        stats.quote_rejected += 1
        mentions = [
            DisasterMention(
                place_name=place.name,
                record=record,
                pref=admin.pref,
                municipality=admin.municipality,
                lat=place.lat,
                lon=place.lon,
            )
            for record in records
        ]
        stats.mentions += len(mentions)
        return None, mentions

    stats.origin_found += 1
    location = _location_for(place)
    if location is None:
        stats.unlocated += 1
    else:
        stats.located += 1
    variants = [
        form
        for form in (entry.heading, *place.old_forms)
        if form and form != place.name and place is entry.place
    ]
    evidence = Evidence(
        kind="gazetteer",
        stance="disputes" if finding.get("disputed") else "supports",
        source_id=SOURCE_ID,
        locator=locator,
        quote=quote,
        claim=str(finding.get("claim") or "").strip() or f"{place.name}の由来に関する記述",
        level=level,
        extracted_by=f"llm:{context.model_name}",
        quote_verified=True,
        quote_medium="ocr",
    )
    reading = place.readings[0] if place.readings else (entry.reading or None)
    matches = match_elements(place.name, reading, context.dictionary)
    record = Toponym(
        id=make_toponym_id(place.name, admin, salt=f"nihu:{place.place_id}"),
        name=place.name,
        reading=reading,
        variants=sorted(set(variants)),
        status=_status(place, admin),  # type: ignore[arg-type]
        admin=admin,
        location=location,
        hazard_types=hazard_types,
        elements=[match.to_ref() for match in matches],
        etymology_summary=summary,
        evidence=[evidence],
        disaster_records=records,
        dataset="dainihon_chimei",
    )
    apply_scores(record)
    if record.evidence_level == 0:
        # The source only doubts the reading. A doubt with nothing to doubt is
        # not a warning place name, so it is not published as one.
        stats.disputed_only += 1
        return None, []
    return record, []


def _records_for_entry(
    entry: GazetteerEntry,
    payload: dict[str, Any],
    context: _RecordBuildContext,
) -> tuple[list[Toponym], list[DisasterMention]]:
    """Turn the structured reading of one entry into records."""
    records: list[Toponym] = []
    mentions: list[DisasterMention] = []
    for finding in payload.get("findings") or []:
        if not isinstance(finding, dict):
            continue
        stats = context.stats
        stats.findings += 1
        place = _resolve_place(str(finding.get("place_name") or ""), entry, context.index)
        if place is None:
            stats.unknown_place += 1
            continue
        record, loose = _build_record(finding, place, entry, context)
        if record is not None:
            records.append(record)
        mentions.extend(loose)
    return records, mentions


def parse_volume(
    pages: list[NdlPage],
    index: HistoricalIndex,
    pid: str,
    stats: GazetteerStats,
) -> list[GazetteerEntry]:
    """Split one volume into entries and fold its counters into the run."""
    entries, parse_stats = parse_pages(pages, index, book_pid=pid)
    stats.parse.frames += parse_stats.frames
    stats.parse.headings += parse_stats.headings
    stats.parse.matched += parse_stats.matched
    stats.parse.unmatched += parse_stats.unmatched
    stats.parse.ambiguous += parse_stats.ambiguous
    stats.parse.without_province += parse_stats.without_province
    return entries


@dataclass
class ExtractionSetup:
    """How one extraction run talks to the model."""

    #: Counters updated as the run proceeds.
    stats: GazetteerStats = field(default_factory=GazetteerStats)
    #: LLM operations, or None to use only cached extractions.
    llm: LLMOperations | None = None
    #: Model identifier recorded on each citation.
    model_name: str = "unknown"
    #: Reasoning budget requested, recorded so a change invalidates the cache.
    effort: str | None = None
    #: Requests in flight at once.
    workers: int = DEFAULT_WORKERS

    def signature(self) -> str:
        """Return the identity of this extraction setup, for the cache key."""
        return f"{self.model_name}|{self.effort or 'default'}"


def extract_entries(
    entries: list[GazetteerEntry],
    index: HistoricalIndex,
    dictionary: ElementDictionary,
    setup: ExtractionSetup,
) -> tuple[list[Toponym], list[DisasterMention]]:
    """Read every screened entry and build the records it supports.

    Args:
        entries: Entries that passed screening.
        index: Index of located historical place names.
        dictionary: Element dictionary used to tag the names.
        setup: Model, identifier, concurrency and counters for the run.

    Returns:
        The toponyms with a documented origin, and the disaster records that
        belong to places whose origin the book does not explain.

    """
    stats = setup.stats
    payloads: list[dict[str, Any] | None]
    if setup.llm is None or setup.workers <= 1:
        payloads = [_extract_entry(entry, index, setup) for entry in entries]
    else:
        with ThreadPoolExecutor(max_workers=setup.workers) as pool:
            payloads = list(pool.map(lambda entry: _extract_entry(entry, index, setup), entries))

    context = _RecordBuildContext(
        index=index,
        dictionary=dictionary,
        model_name=setup.model_name,
        stats=stats,
    )
    records: list[Toponym] = []
    mentions: list[DisasterMention] = []
    for entry, payload in zip(entries, payloads, strict=True):
        if payload is None:
            continue
        found, loose = _records_for_entry(entry, payload, context)
        records.extend(found)
        mentions.extend(loose)
    return records, mentions


def gazetteer_places(places: list[HistoricalPlace]) -> list[HistoricalPlace]:
    """Return only the entries that come from the national gazetteer."""
    return [place for place in places if place.source == GAZETTEER_SOURCE]
