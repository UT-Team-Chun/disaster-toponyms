"""Turn a municipal place-name study into evidence-backed toponym records.

This pipeline is deterministic: the level, the hazard types and the quoted
excerpt all come from the wording printed in the book, so a rebuild produces the
same dataset without calling any model.
"""

from __future__ import annotations

from dataclasses import dataclass

from alg.core.toponyms.parsers.kiryu_timeikou import GazetteerEntry, parse_kiryu_text
from alg.core.toponyms.tools.address import first_oaza
from alg.core.toponyms.tools.claims import classify_description, verify_quote
from alg.core.toponyms.tools.element_matcher import match_elements
from alg.core.toponyms.tools.ids import make_toponym_id
from alg.core.toponyms.tools.prefectures import pref_code
from alg.core.toponyms.tools.scoring import apply_scores
from alg.models.element import ElementDictionary
from alg.models.hazard import HAZARD_LABELS_JA
from alg.models.toponym import AdminArea, Evidence, Toponym

#: Evidence levels used when phrasing the claim sentence.
_LEVEL_DATED_DISASTER = 3
_LEVEL_STATED_DISASTER = 2


@dataclass(frozen=True)
class LocalHistorySource:
    """Bibliographic context needed to cite a municipal study."""

    source_id: str
    title: str
    pref: str
    municipality: str
    dataset: str


KIRYU = LocalHistorySource(
    source_id="kiryu_timeikou_2000",
    title="桐生市地名考",
    pref="群馬県",
    municipality="桐生市",
    dataset="kiryu_timeikou",
)


def _claim_sentence(source_title: str, name: str, level: int, markers: tuple[str, ...]) -> str:
    """Compose the one-line statement of what the citation establishes."""
    marker_text = "・".join(markers[:3])
    if level >= _LEVEL_DATED_DISASTER:
        return f"『{source_title}』が{name}について、年号を伴う災害の記録を示す（{marker_text}）"
    if level == _LEVEL_STATED_DISASTER:
        return f"『{source_title}』が{name}を災害由来の地名と明記する（{marker_text}）"
    return f"『{source_title}』が{name}を地形由来と説明する（{marker_text}）"


def _admin_for(entry: GazetteerEntry, source: LocalHistorySource) -> AdminArea:
    """Build the administrative context of one entry."""
    return AdminArea(
        pref=source.pref,
        pref_code=pref_code(source.pref),
        municipality=source.municipality,
        oaza=first_oaza(entry.modern_area),
        koaza=entry.name,
        historical_village=entry.village,
    )


def _summary_for(entry: GazetteerEntry, hazards: tuple[str, ...]) -> str:
    """Build the short etymology shown on the map."""
    labels = "・".join(HAZARD_LABELS_JA.get(hazard, hazard) for hazard in hazards[:2])
    if labels:
        return f"{entry.name}：{labels}に関わる地名。"
    return f"{entry.name}の由来。"


def build_from_gazetteer(
    text: str,
    dictionary: ElementDictionary,
    *,
    source: LocalHistorySource = KIRYU,
) -> list[Toponym]:
    """Build toponym records from the text of a municipal place-name study.

    Args:
        text: Layout-preserving text of the whole book.
        dictionary: Element dictionary used to tag the names.
        source: Bibliographic context of the book.

    Returns:
        One record per entry whose explanation states a disaster or terrain
        origin, keeping the strongest claim when a name repeats.

    """
    best: dict[str, Toponym] = {}
    for entry in parse_kiryu_text(text):
        claim = classify_description(entry.description, name=entry.name)
        if claim is None or not claim.is_evidence():
            continue

        if not verify_quote(claim.quote, text):
            # The excerpt was stitched together across printed columns, so it
            # cannot be cited; dropping it is safer than weakening the claim.
            continue

        admin = _admin_for(entry, source)
        identifier = make_toponym_id(entry.name, admin, salt=entry.village or "")
        matches = match_elements(entry.name, entry.reading, dictionary)
        evidence = Evidence(
            kind="local_history",
            source_id=source.source_id,
            locator=f"p.{entry.page}" if entry.page else None,
            quote=claim.quote,
            claim=_claim_sentence(source.title, entry.name, claim.level, claim.markers),
            level=claim.level,
            extracted_by="human",
            quote_verified=True,
        )
        record = apply_scores(
            Toponym(
                id=identifier,
                name=entry.name,
                reading=entry.reading,
                status="historical" if entry.level == "koaza" else "current",
                admin=admin,
                hazard_types=list(claim.hazard_types),
                elements=[match.to_ref() for match in matches],
                etymology_summary=claim.summary or _summary_for(entry, claim.hazard_types),
                evidence=[evidence],
                dataset=source.dataset,
            ),
        )
        previous = best.get(identifier)
        if previous is None or record.evidence_level > previous.evidence_level:
            best[identifier] = record
    return list(best.values())
