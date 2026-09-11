"""Tests for deriving the evidence level of a record."""

from alg.core.toponyms.tools.scoring import apply_scores, evidence_level, origin_level
from alg.models.toponym import DisasterRecord, Evidence, Toponym


def _evidence(
    level: int,
    stance: str = "supports",
    kind: str = "local_history",
    extracted_by: str = "human",
) -> Evidence:
    return Evidence(
        kind=kind,  # type: ignore[arg-type]
        stance=stance,  # type: ignore[arg-type]
        source_id="src",
        claim="なにかの主張",
        level=level,
        extracted_by=extracted_by,
    )


def _record(relation: str = "same_place_record") -> DisasterRecord:
    return DisasterRecord(
        relation=relation,  # type: ignore[arg-type]
        name="明治二十二年の洪水",
        match_method="entry_text",
    )


def test_origin_level_is_capped_at_two():
    assert origin_level([_evidence(1), _evidence(3)]) == 2


def test_origin_level_ignores_spelling_only_citations():
    assert origin_level([_evidence(2, kind="pattern")]) == 0


def test_no_evidence_means_level_zero():
    assert evidence_level([], []) == 0


def test_disputing_citations_never_raise_the_level():
    assert evidence_level([_evidence(1), _evidence(2, stance="disputes")], []) == 1


def test_a_record_without_a_documented_origin_stays_at_zero():
    assert evidence_level([], [_record()]) == 0


def test_a_record_at_the_same_place_raises_a_documented_origin():
    assert evidence_level([_evidence(1)], [_record()]) == 3


def test_a_nearby_record_alone_does_not_raise_the_level():
    assert evidence_level([_evidence(2)], [_record("nearby_record")]) == 2


def test_a_model_extracted_citation_cannot_claim_level_three():
    extracted = _evidence(3, extracted_by="llm:gpt-5.6-terra")
    assert evidence_level([extracted], []) == 2


def test_a_curator_may_state_level_three_directly():
    assert evidence_level([_evidence(3)], []) == 3


def test_apply_scores_marks_a_record_as_disputed():
    record = Toponym(
        id="34-abc",
        name="蛇落地悪谷",
        evidence=[_evidence(2), _evidence(0, stance="disputes")],
    )
    apply_scores(record)
    assert record.origin_level == 2
    assert record.evidence_level == 2
    assert record.disputed


def test_apply_scores_reports_the_strongest_record_relation():
    record = Toponym(
        id="10-abc",
        name="梅ヶ久保",
        evidence=[_evidence(2)],
        disaster_records=[_record("nearby_record"), _record("named_after")],
    )
    apply_scores(record)
    assert record.evidence_level == 3
    assert record.record_relation() == "named_after"
    assert record.has_disaster_record()
    assert not record.disputed
