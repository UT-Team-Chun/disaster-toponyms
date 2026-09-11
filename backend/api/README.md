# API Application

FastAPIを使用したバックエンドAPIアプリケーション

> **📖 このREADMEについて**
>
> このファイルには、**backend/api/ のディレクトリ構造**、**セットアップ手順**、**開発コマンド**、**依存関係ルール**、**コード規約**が記載されています。
>
> - **Backend開発の作業手順やベストプラクティス** → [docs/roles/software_engineer.md](../../docs/roles/software_engineer.md) を参照してください
> - **アーキテクチャ設計の詳細** → [backend/docs/architecture.md](../docs/architecture.md) を参照してください
> - **Lintエラーの対処法** → [backend/docs/lint.md](../docs/lint.md) を参照してください

---

## 📂 ディレクトリ構造

```
backend/api/
├── src/
│   ├── app.py             # FastAPIエントリーポイント
│   ├── config/            # 設定読み込みロジック
│   ├── domain/            # 全機能で共有するビジネスデータ・ルール
│   └── features/          # 機能単位のモジュール (Vertical Slices)
│       └── {feature_name}/
│           ├── router.py                    # APIの入口（入力検証のみ）
│           ├── usecase.py                   # ビジネスロジックのオーケストレーション
│           └── request_and_response.py      # リクエスト・レスポンスのスキーマ
│
├── tests/                 # テストコード
├── pyproject.toml         # プロジェクト設定
└── Makefile               # makeコマンド定義
```

---

## ⚙️ セットアップ

### 必要要件

- **Python 3.12以上** (必須)
- uv (高速なPythonパッケージマネージャー)

### uvのインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 依存関係のインストール

```bash
# プロジェクトルートでuvを使用して依存関係をインストール
make install

# または直接uvコマンドで
uv sync
```

---

## ⚙️ 開発コマンド

### 開発サーバーの起動

```bash
make dev
```

サーバーは http://localhost:8000 で起動します。

### コード品質

#### リント（チェック）

```bash
make lint
```

#### フォーマット（自動修正）

```bash
# フォーマット + 自動修正可能なエラーの修正
make fix

# または、フォーマットのみ（エラー確認のみ）
make fmt
```

### テスト

```bash
make test
```

### OpenAPI仕様書生成

API変更時は必ず実行してください：

```bash
make openapi-generate
```

### カバレッジ測定

```bash
# カバレッジ測定
make coverage

# カバレッジ可視化
make vis_coverage
```

---

## 🔗 依存関係ルール

### ✅ 使用可能な依存関係

```
src.features → src.domain
src.features → src.config
src.features → alg.entrypoints
src.features → gateways

alg.entrypoints → alg.core, alg.models
alg.core       → alg.models, gateways.{llm, aws, gsi, web}
gateways.{gsi, web} → gateways.http
```

### ❌ 使用禁止の依存関係

```
❌ src.domain → src.features
❌ src.domain → gateways
❌ src.features → src.features (機能間の直接参照)
❌ alg.core → gateways.rdb (純粋な計算ロジックを保つため)
```

依存関係は `tach check`（`make lint` に含まれる）で機械的に検証されます。

---

## 📖 コード規約

### importルール

#### Backend内のimport

`from src.`から始まる絶対importを使用します。

#### 共有パッケージのimport

`from alg.`や`from gateways.`のようにパッケージ名から始まるimportを使用します。


---

## 🎨 コードスタイル

### Ruff設定

- **line-length**: 99
- **select**: ALL（全ルール有効）
- **主な無視ルール**:
  - COM812: Missing trailing comma (フォーマッタとの競合を回避)
  - D100, D103, D104: docstring関連（公開モジュール/関数/パッケージ）
  - D203, D213: docstring形式の競合ルールを無視
  - TC002: 型チェックブロックへのインポート移動を無視

### mypy設定

- `ignore_missing_imports = true`
- `check_untyped_defs = true`
- Pydanticプラグイン有効

### 命名規則

- クラス: PascalCase
- 関数・変数: snake_case
- 定数: UPPER_SNAKE_CASE
- プライベート: _leading_underscore

### インポート順序 (Ruff I)

1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール

### `__init__.py`の記述ルール

- **なるべく空ファイルにする**: `__init__.py`には文字列やコードを記述しない
- モジュールのエクスポートが必要な場合のみ、最小限のimport文を記述

---

## 🛠️ 技術スタック

- **FastAPI** - Webフレームワーク
- **SQLAlchemy** - ORM
- **Alembic** - マイグレーション
- **httpx** - HTTPクライアント
- **uv** - パッケージマネージャー (Python 3.12以上)
- **OpenAI** - LLM API
- **PyYAML** - YAML設定ファイル読み込み
- **Pydantic** - データバリデーション

### 開発ツール

- **Ruff** - Linter & Formatter (isort, pycodestyle, flake8互換)
- **mypy** - 型チェッカー
- **pytest** - テストフレームワーク
- **coverage** - カバレッジ測定

---

## 📚 参考ドキュメント

- **アーキテクチャ詳細**: [backend/docs/architecture.md](../docs/architecture.md)
- **依存関係図**: [backend/docs/dependencies.mmd](../docs/dependencies.mmd)
- **Lintエラー対処法**: [backend/docs/lint.md](../docs/lint.md)
- **SWE向け作業ガイド**: [docs/roles/software_engineer.md](../../docs/roles/software_engineer.md)
