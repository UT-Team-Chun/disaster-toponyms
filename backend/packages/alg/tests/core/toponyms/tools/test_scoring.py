"""Tests for deriving the evidence level of a record."""

from alg.core.toponyms.tools.scoring import apply_scores, evidence_level
from alg.models.toponym import Evidence, Toponym


def _evidence(level: int, stance: str = "supports") -> Evidence:
    return Evidence(
        kind="local_history",
        stance=stance,  # type: ignore[arg-type]
        source_id="src",
        claim="なにかの主張",
        level=level,
    )


def test_level_is_the_strongest_supporting_citation():
    assert evidence_level([_evidence(1), _evidence(3), _evidence(2)]) == 3


def test_no_evidence_means_level_zero():
    assert evidence_level([]) == 0


def test_disputing_citations_never_raise_the_level():
    assert evidence_level([_evidence(1), _evidence(3, stance="disputes")]) == 1


def test_apply_scores_marks_a_record_as_disputed():
    record = Toponym(
        id="34-abc",
        name="蛇落地悪谷",
        evidence=[_evidence(2), _evidence(0, stance="disputes")],
    )
    apply_scores(record)
    assert record.evidence_level == 2
    assert record.disputed


def test_apply_scores_leaves_undisputed_records_alone():
    record = Toponym(id="10-abc", name="梅ヶ久保", evidence=[_evidence(2)])
    apply_scores(record)
    assert record.evidence_level == 2
    assert not record.disputed
