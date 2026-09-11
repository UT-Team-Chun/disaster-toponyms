"""Command line front end for the disaster-toponym dataset build.

Examples:
    uv run python scripts/build_toponym_dataset.py
    uv run python scripts/build_toponym_dataset.py --pref 10 --no-candidates
    uv run python scripts/build_toponym_dataset.py --offline

"""

from __future__ import annotations

import argparse
import sys

from alg.entrypoints.toponym_dataset import BuildOptions, build_toponym_dataset


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="警鐘地名データセットをビルドする")
    parser.add_argument(
        "--pref",
        action="append",
        default=None,
        metavar="CODE",
        help="対象を都道府県コードで絞る（例: --pref 10 --pref 20）",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="LLM抽出を行わず、キャッシュ済みの抽出結果のみ使用する",
    )
    parser.add_argument(
        "--no-candidates",
        action="store_true",
        help="全国住所データからの候補（根拠レベル0）抽出を省略する",
    )
    parser.add_argument(
        "--no-hazard",
        action="store_true",
        help="ハザードタイルの照合を省略する",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="ネットワークを使う処理（LLM・ジオコーディング・タイル照合）をすべて省略する",
    )
    parser.add_argument(
        "--no-areas",
        action="store_true",
        help="地名がカバーする小地域ポリゴンの対応づけを省略する",
    )
    parser.add_argument(
        "--candidate-threshold",
        type=float,
        default=0.35,
        help="候補として残す地名要素の特異度の下限（既定 0.35）",
    )
    parser.add_argument(
        "--candidate-limit",
        type=int,
        default=None,
        help="候補の件数上限（動作確認用）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="静的ファイルを書き出さずに集計のみ表示する",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the build and print the report."""
    args = parse_args(argv)
    options = BuildOptions(
        use_llm=not (args.no_llm or args.offline),
        use_network_geocoding=not args.offline,
        sample_hazard_zones=not (args.no_hazard or args.offline),
        include_candidates=not args.no_candidates,
        attach_area_polygons=not (args.no_areas or args.offline),
        candidate_threshold=args.candidate_threshold,
        write_files=not args.dry_run,
        pref_codes=frozenset(args.pref) if args.pref else None,
        candidate_limit=args.candidate_limit,
    )
    report = build_toponym_dataset(options)

    print(f"built_at: {report.built_at}")
    for stage in report.stages:
        print(f"  [{stage.stage}] produced={stage.produced} skipped={stage.skipped}")
        for message in stage.messages:
            print(f"      {message}")
    print(f"toponyms: {report.toponyms_total}  by level: {report.toponyms_by_level}")
    print(f"candidates: {report.candidates_total}  monuments: {report.monuments_total}")
    print(f"outputs: {len(report.outputs)} files")
    if report.warnings:
        print("warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
