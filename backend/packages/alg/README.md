# Algorithm Package

共有アルゴリズム・計算ロジックパッケージ。
バックエンドとジョブアプリケーション間で共有される純粋な計算処理を提供します。

> **📖 このREADMEについて**
>
> このファイルには、**backend/packages/alg/ のディレクトリ構造**、**開発コマンド**、**依存関係ルール**、**コード規約**が記載されています。
>
> - **AlgEの作業手順（PoC検証から本番実装まで）** → [docs/roles/algorithm_engineer.md](../../../docs/roles/algorithm_engineer.md) を参照してください
> - **アーキテクチャ設計の詳細** → [backend/docs/architecture.md](../../docs/architecture.md) を参照してください
> - **依存関係図** → [backend/docs/dependencies.mmd](../../docs/dependencies.mmd) を参照してください

---

## 📂 ディレクトリ構造

```
backend/packages/alg/
├── sandbox/              # 検証用スクリプト（モジュール化前）
│   └── {名前}/           # 実施者ごとのディレクトリ
│       ├── n_*.py        # Jupyter Notebookから変換したコード
│       └── s_*.py        # 通常のPythonスクリプト
│
├── alg/                  # パッケージ本体
│   ├── models/           # データモデル定義 (Pydantic BaseModel)
│   │   └── {model_name}.py
│   │
│   ├── experimental/     # 検証段階のインターフェース (PoC段階でsandboxから利用)
│   │   └── {function_name}.py
│   │
│   ├── entrypoints/      # SWから呼び出す公開インターフェース (SW開発段階でAPIから利用)
│   │   └── {function_name}.py
│   │
│   └── core/             # 内部ロジックの部品 (最下層)
│       └── {module_name}/
│           ├── tools/       # 単機能関数群
│           └── pipelines/   # 複数のToolを組み合わせた処理フロー
│
├── tests/                # テストコード
├── pyproject.toml        # パッケージ設定
└── README.md             # このファイル
```

### 各ディレクトリの役割

#### sandbox/
- **役割**: PoC段階で自由に検証するスクリプト置き場
- **形式**: notebook形式（`n_`）または script形式（`s_`）
- **利用タイミング**: PoC段階

#### alg/models/
- **役割**: Pydanticの`BaseModel`を使用したデータモデル定義
- **作成タイミング**: sandbox でApproveを取得後、core/ と並行して実装
- **利用者**: core/, experimental/, entrypoints/ から利用

#### alg/core/
- **役割**: 内部ロジックの部品（純粋関数）
- **作成タイミング**: sandbox でApproveを取得後、検証コードをモジュール化
- **構造**:
  - `tools/`: 単機能関数群
  - `pipelines/`: 複数のToolを組み合わせた処理フロー

#### alg/experimental/
- **役割**: PoC段階の検証用インターフェース
- **作成タイミング**: PoC段階（core/実装後）
- **実装内容**: core/の複数モジュールを組み合わせた関数
- **利用者**: AlgE（sandboxから検証用に使用）

#### alg/entrypoints/
- **役割**: SW開発段階のAPI用インターフェース
- **作成タイミング**: SW開発段階のみ
- **実装内容**: core/の複数モジュールを組み合わせた関数（experimentalと類似）
- **利用者**: SWE（Backend APIから本番利用）

**重要**: experimental/ と entrypoints/ は**実装タイミングが異なるだけで、どちらもcore/の複数モジュールを組み合わせた関数**です。

---

## ⚙️ 開発コマンド

### テスト実行

```bash
# プロジェクトルートから
cd backend/packages/alg
pytest
```

### Lint & 型チェック

```bash
# プロジェクトルートから
cd backend/api
make lint
```

---

## 🔗 依存関係ルール

### ✅ 使用可能な依存関係

```
alg.entrypoints → alg.core
alg.experimental → alg.core

alg.core → gateways.llm (LLM接続)
alg.core → gateways.aws (AWS接続)
alg.core → gateways.ocr (OCR接続)
alg.core → gateways.{service} (その他の外部サービス接続)
```

### ❌ 使用禁止の依存関係

```
❌ alg → gateways.rdb (RDB接続は禁止)
❌ alg → src.features (Backend固有の機能)
```

**理由**: `alg`パッケージは純粋な計算ロジックを提供するため、データベースへの直接アクセスやBackend固有の機能への依存は行いません。

---

## 🔌 外部サービスの呼び出し

`alg`パッケージは、`gateways`パッケージを通じて外部サービス（LLM, AWS, OCR等）を呼び出します。

### 利用可能な外部サービス

以下の外部サービスモジュールを`alg.core`から呼び出すことができます:

- **gateways.llm**: LLM接続（OpenAI, Anthropic等）
- **gateways.aws**: AWS接続（S3, Lambda等）
- **gateways.ocr**: OCR接続（文字認識サービス）
- **gateways.{service}**: その他の外部サービス

### pyproject.tomlでの依存関係指定

**重要**: 使用する外部サービスは、`pyproject.toml`で明示的に指定してください。

#### 例: LLMとAWSを使用する場合

```toml
[project]
name = "alg"
dependencies = [
    "gateways",  # ベースのgatewaysパッケージ
]

# オプション依存関係として外部サービスを指定
[project.optional-dependencies]
llm = ["openai>=1.0.0", "anthropic>=0.5.0"]
aws = ["boto3>=1.26.0"]
ocr = ["pytesseract>=0.3.0"]

# すべての外部サービスを含む
all = [
    "openai>=1.0.0",
    "anthropic>=0.5.0",
    "boto3>=1.26.0",
    "pytesseract>=0.3.0",
]
```

#### インストール方法

```bash
# LLMのみ使用する場合
uv pip install -e ".[llm]"

# LLMとAWSを使用する場合
uv pip install -e ".[llm,aws]"

# すべての外部サービスを使用する場合
uv pip install -e ".[all]"
```


### 新しい外部サービスを追加する場合

1. `gateways`パッケージに新しいサービスモジュールを実装
2. `alg/pyproject.toml`の`[project.optional-dependencies]`に追加
3. `alg.core`から呼び出す

---

## 📖 コード規約

### importルール

#### Backend固有の機能を使う場合

`from src.`から始まるimportを使用します。

#### 共有パッケージを使う場合

`from alg.`や`from gateways.`のようにパッケージ名から始まるimportを使用します。


### sandbox/ - 検証用スクリプト

#### ファイル命名規則

```
backend/packages/alg/sandbox/{名前}/{n|s}_{日付}_{実施内容}.py
```

- `{名前}`: 実施者の名前（例: `tanaka`, `yamada`）
- `{n|s}`: ファイルタイプ
  - `n`: notebook（Jupyter Notebookから変換したコード）
  - `s`: script（通常のPythonスクリプト）
- `{日付}`: 実施日（YYYYMMDD形式、例: `20250123`）
- `{実施内容}`: 内容の説明（snake_case、例: `test_api_connection`）

#### notebookファイル（`n`で始まるファイル）

VSCodeやPyCharmでインタラクティブに実行できるよう、**セル区切り `# %%`** を使用してください。

---

## 📚 参考ドキュメント

- **アーキテクチャ詳細**: [backend/docs/architecture.md](../../docs/architecture.md)
- **依存関係図**: [backend/docs/dependencies.mmd](../../docs/dependencies.mmd)
- **AlgE向け作業ガイド**: [docs/roles/algorithm_engineer.md](../../../docs/roles/algorithm_engineer.md)
