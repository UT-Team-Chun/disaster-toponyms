"""Tests for attaching recorded disasters to the place names they name."""

from alg.core.toponyms.pipelines.link_disaster_records import link_mentions
from alg.core.toponyms.tools.disaster_records import DisasterMention
from alg.core.toponyms.tools.scoring import apply_scores
from alg.models.toponym import AdminArea, DisasterRecord, Evidence, Location, Toponym


def _toponym(
    name: str,
    *,
    municipality: str = "うきは市",
    level: int = 1,
    hazard: list[str] | None = None,
    lat: float = 33.33,
    lon: float = 130.75,
) -> Toponym:
    return apply_scores(
        Toponym(
            id=f"id-{name}-{municipality}",
            name=name,
            admin=AdminArea(pref="福岡県", pref_code="40", municipality=municipality),
            location=Location(lat=lat, lon=lon, precision="oaza"),
            hazard_types=hazard or [],  # type: ignore[arg-type]
            evidence=(
                [
                    Evidence(
                        kind="gazetteer",
                        source_id="src",
                        claim="地形由来",
                        level=level,
                    ),
                ]
                if level
                else []
            ),
        ),
    )


def _mention(
    name: str,
    *,
    municipality: str = "うきは市",
    hazard: list[str] | None = None,
    lat: float = 33.33,
    lon: float = 130.75,
) -> DisasterMention:
    return DisasterMention(
        place_name=name,
        record=DisasterRecord(
            relation="same_place_record",
            name="享保5年の土砂災害",
            hazard_types=hazard or [],  # type: ignore[arg-type]
            source_id="gsi_denshouhi",
            locator="mon-1",
            match_method="monument_place_name",
        ),
        pref="福岡県",
        municipality=municipality,
        lat=lat,
        lon=lon,
    )


def test_a_record_at_the_same_place_raises_a_documented_origin():
    place = _toponym("大村")
    stats = link_mentions([_mention("大村")], [place], [])
    assert stats.linked == 1
    assert place.evidence_level == 3
    assert stats.raised_to_level_3 == 1


def test_a_record_does_not_reach_a_place_in_another_municipality():
    place = _toponym("大村", municipality="久留米市")
    stats = link_mentions([_mention("大村")], [place], [])
    assert stats.linked == 0
    assert stats.unmatched == 1
    assert place.evidence_level == 1


def test_a_record_far_from_the_place_is_not_attached():
    place = _toponym("大村", lat=33.33, lon=130.75)
    stats = link_mentions([_mention("大村", lat=34.0, lon=131.5)], [place], [])
    assert stats.linked == 0
    assert stats.too_far == 1


def test_a_disaster_of_another_kind_is_kept_only_as_context():
    place = _toponym("大村", hazard=["tsunami"])
    stats = link_mentions([_mention("大村", hazard=["debris_flow"])], [place], [])
    assert stats.demoted_hazard == 1
    assert place.disaster_records[0].relation == "nearby_record"
    assert place.evidence_level == 1


def test_a_candidate_keeps_the_record_without_gaining_a_level():
    candidate = _toponym("大村", level=0)
    stats = link_mentions([_mention("大村")], [], [candidate])
    assert stats.candidates_with_records == 1
    assert candidate.has_disaster_record()
    assert candidate.evidence_level == 0


def test_the_same_record_is_not_attached_twice():
    place = _toponym("大村")
    stats = link_mentions([_mention("大村"), _mention("大村")], [place], [])
    assert stats.linked == 1
    assert len(place.disaster_records) == 1
