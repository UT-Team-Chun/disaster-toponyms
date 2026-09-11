"""Public entry point for building the disaster-toponym dataset.

One call runs the whole chain: curated seeds, the deterministic municipal
gazetteer ingest, the model-assisted prose extraction, the nationwide spelling
sweep, hazard corroboration and the static output files. Every stage can be
switched off so that a rebuild works offline from the caches alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from gateways.gsi.models.monument import DisasterMonument
from gateways.gsi.operations.monuments import load_monuments
from gateways.llm.config import LLMConfig
from gateways.llm.operations.llm_operations import LLMOperations

from alg.core.toponyms.parsers.layout import strip_running_numbers
from alg.core.toponyms.pipelines.attach_areas import attach_areas
from alg.core.toponyms.pipelines.build_outputs import DatasetBundle, write_outputs
from alg.core.toponyms.pipelines.corroborate_hazard import corroborate
from alg.core.toponyms.pipelines.extract_prose_evidence import (
    ProseDocument,
    extract_from_document,
)
from alg.core.toponyms.pipelines.generate_candidates import screen_address_table
from alg.core.toponyms.pipelines.ingest_local_history import KIRYU, build_from_gazetteer
from alg.core.toponyms.tools.curated import (
    load_curated_toponyms,
    load_elements,
    load_sources,
)
from alg.core.toponyms.tools.geocode import resolve_location
from alg.core.toponyms.tools.paths import ToponymPaths, get_paths
from alg.models.area import MatchedArea
from alg.models.build_report import BuildReport, StageReport
from alg.models.element import ElementDictionary
from alg.models.toponym import Toponym

#: Prose documents mined with the model. Each names its bibliography entry.
#: Pages that only list name *types* without locations (the Nagano prefecture
#: pages, for example) are not listed here: their content belongs in the
#: element dictionary, which cites them directly.
PROSE_DOCUMENTS: tuple[tuple[str, ProseDocument], ...] = (
    (
        "local_history/toyokawa_koaza.txt",
        ProseDocument(
            doc_id="toyokawa_koaza",
            source_id="toyokawa_koaza_bousai",
            source_title="自然災害に気をつけたい地名（豊川市）",
            text="",
            evidence_kind="official",
            pref_hint="愛知県",
            municipality_hint="豊川市",
            locator="https://www.city.toyokawa.lg.jp/material/files/group/2/4.pdf",
        ),
    ),
    (
        "local_history/toyokawa_villages.txt",
        ProseDocument(
            doc_id="toyokawa_villages",
            source_id="toyokawa_village_origins",
            source_title="豊川市域の旧村名の由来一覧",
            text="",
            evidence_kind="official",
            pref_hint="愛知県",
            municipality_hint="豊川市",
            locator="https://www.city.toyokawa.lg.jp/material/files/group/2/sankou1.pdf",
        ),
    ),
    (
        "local_history/takahashi_saigai_chimei.txt",
        ProseDocument(
            doc_id="takahashi_saigai_chimei",
            source_id="takahashi_saigai_chimei",
            source_title="地名をあるく 96. 災害と地名（高梁市）",
            text="",
            evidence_kind="official",
            pref_hint="岡山県",
            municipality_hint="高梁市",
            locator="https://www.city.takahashi.lg.jp/site/koho/saigaitochimei.html",
        ),
    ),
)


@dataclass
class BuildOptions:
    """Switches controlling which stages of the build run."""

    use_llm: bool = True
    use_network_geocoding: bool = True
    sample_hazard_zones: bool = True
    include_candidates: bool = True
    attach_area_polygons: bool = True
    #: Polygon simplification tolerance in degrees; larger means smaller files.
    area_tolerance: float = 0.0001
    #: Lowest element specificity kept when screening the address table.
    candidate_threshold: float = 0.35
    write_files: bool = True
    pref_codes: frozenset[str] | None = None
    candidate_limit: int | None = None
    paths: ToponymPaths = field(default_factory=get_paths)


def _monuments(options: BuildOptions) -> list[DisasterMonument]:
    """Load the monument dataset from the extracted download, if present."""
    for path in sorted(options.paths.monument_dir.rglob("*.geojson")):
        return load_monuments(path)
    return []


def _llm_operations(options: BuildOptions) -> tuple[LLMOperations | None, str]:
    """Build the LLM client when a key is configured and extraction is enabled."""
    config = LLMConfig()
    if not options.use_llm or not config.openai_api_key:
        return None, config.llm_model
    return (
        LLMOperations(api_key=config.openai_api_key, model=config.llm_model),
        config.llm_model,
    )


def _ingest_curated(
    options: BuildOptions,
    dictionary: ElementDictionary,
    report: BuildReport,
) -> list[Toponym]:
    """Load the hand-maintained nationwide seeds."""
    records, warnings = load_curated_toponyms(
        options.paths.curated_dir / "toponyms",
        dictionary,
        raw_dir=options.paths.raw_dir,
    )
    report.warnings.extend(warnings)
    report.add_stage(StageReport(stage="curated", produced=len(records)))
    return records


def _ingest_gazetteers(
    options: BuildOptions,
    dictionary: ElementDictionary,
    report: BuildReport,
) -> list[Toponym]:
    """Run the deterministic municipal place-name study ingest."""
    path = options.paths.local_history_dir / "kiryu_timeikou.txt"
    if not path.exists():
        report.add_stage(
            StageReport(
                stage="local_history",
                messages=[f"未取得: {path.name}（make download-data を実行してください）"],
            ),
        )
        return []
    text = strip_running_numbers(path.read_text(encoding="utf-8"))
    records = build_from_gazetteer(text, dictionary, source=KIRYU)
    report.add_stage(StageReport(stage="local_history", produced=len(records)))
    return records


def _ingest_prose(
    options: BuildOptions,
    dictionary: ElementDictionary,
    report: BuildReport,
) -> list[Toponym]:
    """Mine the prose sources for evidence-backed records."""
    llm, model_name = _llm_operations(options)
    records: list[Toponym] = []
    messages: list[str] = []
    produced = 0
    skipped = 0
    for relative_path, template in PROSE_DOCUMENTS:
        path = options.paths.raw_dir / relative_path
        if not path.exists():
            messages.append(f"未取得: {relative_path}")
            continue
        document = ProseDocument(
            doc_id=template.doc_id,
            source_id=template.source_id,
            source_title=template.source_title,
            text=strip_running_numbers(path.read_text(encoding="utf-8")),
            evidence_kind=template.evidence_kind,
            pref_hint=template.pref_hint,
            municipality_hint=template.municipality_hint,
            locator=template.locator,
        )
        found, stats = extract_from_document(
            document,
            dictionary,
            llm=llm,
            model_name=model_name,
        )
        records.extend(found)
        produced += len(found)
        skipped += stats.quote_rejected
        messages.append(
            f"{document.doc_id}: 採用{len(found)} 引用不一致{stats.quote_rejected} "
            f"キャッシュ{stats.cached_chunks} 実行{stats.live_chunks}",
        )
    report.add_stage(
        StageReport(stage="prose", produced=produced, skipped=skipped, messages=messages),
    )
    return records


def _deduplicate(records: list[Toponym]) -> list[Toponym]:
    """Merge records that describe the same place, keeping the strongest claim."""
    best: dict[str, Toponym] = {}
    for record in records:
        key = record.id
        previous = best.get(key)
        if previous is None:
            best[key] = record
            continue
        if record.evidence_level > previous.evidence_level:
            record.evidence = [*record.evidence, *previous.evidence]
            best[key] = record
        else:
            previous.evidence = [*previous.evidence, *record.evidence]
    return list(best.values())


def _resolve_missing_locations(
    records: list[Toponym],
    options: BuildOptions,
    report: BuildReport,
) -> None:
    """Geocode records that arrived without coordinates."""
    resolved = 0
    unresolved = 0
    for record in records:
        if record.location is not None:
            continue
        location = resolve_location(
            record.admin,
            record.name,
            use_network=options.use_network_geocoding,
        )
        if location is None:
            unresolved += 1
            continue
        record.location = location
        resolved += 1
    report.add_stage(StageReport(stage="geocode", produced=resolved, skipped=unresolved))


def build_toponym_dataset(options: BuildOptions | None = None) -> BuildReport:
    """Build the whole dataset and write the static files.

    Args:
        options: Stage switches; defaults to a full online build.

    Returns:
        A report describing every stage, the totals and any warnings.

    """
    settings = options or BuildOptions()
    built_at = datetime.now(tz=UTC).isoformat(timespec="seconds")
    report = BuildReport(built_at=built_at)

    dictionary = load_elements(settings.paths.curated_dir / "elements.yaml")
    sources = load_sources(settings.paths.curated_dir / "sources.yaml")

    records = [
        *_ingest_curated(settings, dictionary, report),
        *_ingest_gazetteers(settings, dictionary, report),
        *_ingest_prose(settings, dictionary, report),
    ]
    if settings.pref_codes is not None:
        records = [
            record for record in records if (record.admin.pref_code or "00") in settings.pref_codes
        ]
    records = _deduplicate(records)
    _resolve_missing_locations(records, settings, report)
    records = [record for record in records if record.location is not None]

    monuments = _monuments(settings)
    report.monuments_total = len(monuments)

    corroboration = corroborate(
        records,
        monuments,
        sample_zones=settings.sample_hazard_zones,
        sampled_at=built_at,
    )
    report.add_stage(
        StageReport(
            stage="hazard",
            produced=corroboration.sampled,
            skipped=corroboration.skipped_no_location,
            messages=[
                f"区域内 {corroboration.in_any_zone} 件 / 伝承碑近接 "
                f"{corroboration.with_monument} 件",
                *corroboration.failures[:5],
            ],
        ),
    )

    candidates: list[Toponym] = []
    if settings.include_candidates:
        candidates, candidate_stats = screen_address_table(
            settings.paths.geolonia_csv,
            dictionary,
            threshold=settings.candidate_threshold,
            pref_codes=settings.pref_codes,
            limit=settings.candidate_limit,
        )
        report.add_stage(
            StageReport(
                stage="candidates",
                produced=candidate_stats.kept,
                skipped=candidate_stats.matched - candidate_stats.kept,
                messages=[f"住所データ {candidate_stats.rows} 行を走査"],
            ),
        )

    areas: list[MatchedArea] = []
    if settings.attach_area_polygons:
        areas, area_stats = attach_areas(
            [*records, *candidates],
            cache_dir=settings.paths.boundary_dir,
            tolerance=settings.area_tolerance,
            use_network=settings.use_network_geocoding,
        )
        report.add_stage(
            StageReport(
                stage="areas",
                produced=area_stats.areas_kept,
                skipped=area_stats.unmatched_records,
                messages=[
                    f"{area_stats.prefectures} 都道府県 / "
                    f"小地域 {area_stats.areas_read} 件を読み込み",
                    f"地名 {area_stats.matched_records} 件に範囲を対応づけ",
                    f"頂点 {area_stats.points_before} -> {area_stats.points_after}",
                    *area_stats.messages[:5],
                ],
            ),
        )

    report.toponyms_total = len(records)
    report.candidates_total = len(candidates)
    for record in records:
        key = str(record.evidence_level)
        report.toponyms_by_level[key] = report.toponyms_by_level.get(key, 0) + 1

    if settings.write_files:
        outputs = write_outputs(
            settings.paths.output_dir,
            DatasetBundle(
                toponyms=records,
                candidates=candidates,
                areas=areas,
                monuments=monuments,
                elements=dictionary,
                sources=sources,
                built_at=built_at,
            ),
        )
        report.outputs = outputs.files
        report.warnings.extend(outputs.warnings)
        report.add_stage(
            StageReport(
                stage="outputs",
                produced=len(outputs.files),
                messages=[f"{outputs.bytes_written} バイト"],
            ),
        )
    return report
