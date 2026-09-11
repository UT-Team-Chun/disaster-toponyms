"""The core toponym record: a place name plus the evidence for its origin."""

from typing import Literal

from pydantic import BaseModel, Field

from alg.models.hazard import HazardType

EvidenceKind = Literal[
    "pattern",
    "gazetteer",
    "local_history",
    "legend",
    "academic",
    "official",
    "news",
    "monument",
    "manual",
]

#: Evidence strength each kind can justify on its own.
EVIDENCE_LEVEL_LABELS_JA: dict[int, str] = {
    0: "字面のみ（候補）",
    1: "地形由来の記載あり",
    2: "災害由来・替字の明記",
    3: "災害記録・伝承との対応",
}

EvidenceStance = Literal["supports", "disputes"]
ToponymStatus = Literal["current", "historical", "renamed"]
LocationPrecision = Literal[
    "point",
    "koaza",
    "oaza",
    "village",
    "feature",
    "municipality",
    "prefecture",
    "unknown",
]
ReviewStatus = Literal["auto", "reviewed", "rejected"]

#: How a quote was obtained. Optical character recognition can misread a glyph,
#: so a quote verified against OCR output is not the same as one verified
#: against a transcription a person checked.
QuoteMedium = Literal["text", "ocr"]

#: How a recorded disaster relates to the place name.
#:
#: ``named_after`` is the strongest: the source says the name itself comes from
#: the event. ``same_place_record`` says the same place is recorded as having
#: been hit, which corroborates a documented origin without explaining it.
#: ``nearby_record`` is proximity only and never raises the evidence level.
DisasterRelation = Literal["named_after", "same_place_record", "nearby_record"]

#: How the place in a disaster record was tied to this toponym.
RecordMatchMethod = Literal["entry_text", "monument_place_name", "distance", "curated"]

#: Evidence kinds that can state where a name comes from.
ORIGIN_EVIDENCE_KINDS: frozenset[str] = frozenset(
    {
        "gazetteer",
        "local_history",
        "legend",
        "academic",
        "official",
        "news",
        "manual",
        "monument",
    },
)


class Evidence(BaseModel):
    """One citation bearing on the disaster reading of a place name.

    A citation may also argue against the reading. Widely repeated stories are
    sometimes unsupported by any document, so counter-evidence is stored beside
    the supporting citations rather than being silently dropped.
    """

    kind: EvidenceKind
    stance: EvidenceStance = "supports"
    source_id: str
    locator: str | None = Field(default=None, description="Page, URL or NDL pid/frame")
    quote: str | None = Field(default=None, description="Verbatim excerpt from the source")
    claim: str = Field(description="What the excerpt establishes, in one sentence")
    level: int = Field(ge=0, le=3, description="Evidence level this citation justifies")
    extracted_by: str = Field(default="human", description="'human' or 'llm:<model>'")
    quote_verified: bool = Field(
        default=False,
        description="True when the quote was matched character-for-character in the source text",
    )
    quote_medium: QuoteMedium = Field(
        default="text",
        description="Whether the quote was checked against a transcription or against OCR output",
    )


class AdminArea(BaseModel):
    """Administrative location of a toponym.

    Historical sources file a place under the old province and district, which
    are what identify it in the source; the prefecture and municipality are what
    a reader can look up today. Both are kept.
    """

    pref_code: str | None = None
    pref: str | None = None
    municipality_code: str | None = None
    municipality: str | None = None
    oaza: str | None = None
    koaza: str | None = None
    province: str | None = Field(default=None, description="Old province, for example 肥後")
    district: str | None = Field(default=None, description="Old district (郡)")
    historical_village: str | None = Field(
        default=None,
        description="Pre-Meiji or pre-merger village the name belonged to",
    )


class Location(BaseModel):
    """Representative coordinate for a toponym."""

    lat: float
    lon: float
    precision: LocationPrecision = "unknown"
    geocode_source: str | None = None


class ElementRef(BaseModel):
    """A matched element of the place name."""

    element_id: str
    surface: str
    reading: str | None = None
    meaning: str | None = None


class DisasterRecord(BaseModel):
    """A recorded disaster tied to the place, and how the tie was made.

    A name whose origin a source explains, and a place a disaster is recorded at,
    are two different facts. Keeping the relation explicit is what stops the
    second from being reported as the first.
    """

    relation: DisasterRelation
    name: str
    date_text: str | None = Field(default=None, description="Date as printed in the source")
    hazard_types: list[HazardType] = Field(default_factory=list)
    source_id: str | None = None
    locator: str | None = None
    quote: str | None = None
    quote_verified: bool = False
    quote_medium: QuoteMedium = "text"
    match_method: RecordMatchMethod = "curated"
    distance_km: float | None = None
    extracted_by: str = "human"

    def corroborates_origin(self) -> bool:
        """Return True when the record can raise a documented origin to level 3."""
        return self.relation in {"named_after", "same_place_record"}


class HazardCorroboration(BaseModel):
    """Present-day hazard designations sampled at the toponym coordinate.

    This is deliberately kept separate from :class:`Evidence`: it says what the
    modern hazard maps show, not what historical sources say about the name.
    """

    debris_flow_zone: bool | None = None
    steep_slope_zone: bool | None = None
    landslide_zone: bool | None = None
    flood_zone: bool | None = None
    tsunami_zone: bool | None = None
    storm_surge_zone: bool | None = None
    avalanche_risk: bool | None = None
    nearest_monument_ids: list[str] = Field(default_factory=list)
    sampled_at: str | None = None

    def designated_zones(self) -> list[str]:
        """Return the names of every hazard zone the point falls inside."""
        pairs = (
            ("debris_flow_zone", self.debris_flow_zone),
            ("steep_slope_zone", self.steep_slope_zone),
            ("landslide_zone", self.landslide_zone),
            ("flood_zone", self.flood_zone),
            ("tsunami_zone", self.tsunami_zone),
            ("storm_surge_zone", self.storm_surge_zone),
            ("avalanche_risk", self.avalanche_risk),
        )
        return [name for name, value in pairs if value is True]


class Review(BaseModel):
    """Human review state of a record."""

    status: ReviewStatus = "auto"
    reviewer: str | None = None
    note: str | None = None


class Toponym(BaseModel):
    """A place name whose form or documented origin warns of natural disaster."""

    id: str
    name: str
    reading: str | None = None
    reading_estimated: bool = False
    variants: list[str] = Field(default_factory=list)
    status: ToponymStatus = "current"
    renamed_to: str | None = None
    admin: AdminArea = Field(default_factory=AdminArea)
    location: Location | None = None
    area_key: str | None = Field(
        default=None,
        description="e-Stat KEY_CODE of the 町丁・字等 area this name sits in",
    )
    hazard_types: list[HazardType] = Field(default_factory=list)
    elements: list[ElementRef] = Field(default_factory=list)
    etymology_summary: str = ""
    evidence: list[Evidence] = Field(default_factory=list)
    disaster_records: list[DisasterRecord] = Field(default_factory=list)
    origin_level: int = Field(
        default=0,
        ge=0,
        le=2,
        description="What the sources say about the origin of the name alone",
    )
    evidence_level: int = Field(default=0, ge=0, le=3)
    disputed: bool = Field(
        default=False,
        description="True when a source contests the disaster reading of the name",
    )
    dispute_note: str | None = None
    hazard_corroboration: HazardCorroboration = Field(default_factory=HazardCorroboration)
    review: Review = Field(default_factory=Review)
    dataset: str = Field(default="curated", description="Which ingest produced this record")

    def primary_hazard(self) -> HazardType | None:
        """Return the hazard type used for map styling."""
        return self.hazard_types[0] if self.hazard_types else None

    def has_disaster_record(self) -> bool:
        """Return True when any disaster is recorded for this place."""
        return bool(self.disaster_records)

    def record_relation(self) -> DisasterRelation | None:
        """Return the strongest relation any recorded disaster has to the name."""
        order: tuple[DisasterRelation, ...] = (
            "named_after",
            "same_place_record",
            "nearby_record",
        )
        for relation in order:
            if any(record.relation == relation for record in self.disaster_records):
                return relation
        return None
