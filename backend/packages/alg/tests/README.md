# Alg Package Tests

`alg` パッケージのユニットテストです。警鐘地名データセットの判断ロジック
（何を根拠と認めるか、引用が原文と一致するか）を中心に検証しています。

## ディレクトリ構成

```
tests/
├── README.md
└── core/
    └── toponyms/
        ├── tools/
        │   ├── test_normalize.py        # 表記・読みの正規化
        │   ├── test_claims.py           # 主張の分類と引用検証
        │   ├── test_element_matcher.py  # 地名要素の照合
        │   ├── test_address.py          # 現町名の抽出
        │   ├── test_scoring.py          # 根拠レベルの決定
        │   ├── test_export_geojson.py   # 静的ファイルの書き出し
        │   └── test_ids_and_prefectures.py
        ├── parsers/
        │   └── test_kiryu_timeikou.py   # 版面パーサ
        └── pipelines/
            └── test_ingest_local_history.py
```

## 重点的に検証していること

| 観点 | テスト |
|---|---|
| 替字（梅＝埋）を含む複合地名の要素照合 | `test_element_matcher.py` |
| 災害由来・地形由来・記述なしの判別 | `test_claims.py::test_states_*` |
| 年号を伴う災害記録をレベル3にすること | `test_claims.py::test_dated_event_is_level_three` |
| 行政上の合併記述を語源として扱わないこと | `test_claims.py::test_administrative_merger_sentences_are_ignored` |
| 版面をまたいで継ぎ合わされた引用を弾くこと | `test_claims.py::test_verify_quote_rejects_text_stitched_from_two_places` |
| 反証が根拠レベルを上げないこと | `test_scoring.py::test_disputing_citations_never_raise_the_level` |
| 版面の列構造から小字・字・解説を復元すること | `test_kiryu_timeikou.py` |
| 出典が語源を述べていない項目を収録しないこと | `test_ingest_local_history.py::test_only_names_with_a_stated_origin_become_records` |

## テストの実行

```bash
cd backend/packages/alg

# すべて
uv run pytest tests -v

# 特定のファイル
uv run pytest tests/core/toponyms/tools/test_claims.py -v

# カバレッジ
uv run coverage run -m pytest && uv run coverage report
```

リポジトリ全体では `cd backend && make test` で api / alg / gateways のテストを
まとめて実行できます。

## テストを追加するときの方針

- **版面のサンプルは実物と同じ空白配置で書く。** 列位置が意味を持つため、
  整形すると parser のテストにならなくなります。
- **判断基準を変える変更には必ずテストを添える。** どの記述をレベル2と認めるかは
  このデータセットの信頼性そのものです。
- 外部サービスに触れるコードは `gateways` 側でテストし、`alg` のテストは
  ネットワークを使わないようにしてください。
