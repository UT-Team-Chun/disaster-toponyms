# Algorithm Engineer (AlgE) 作業ガイド

このガイドは、Algorithm Engineer (AlgE) がアルゴリズムの検証から本番実装までを行う際の作業手順と注意点をまとめたものです。

---

## 🎯 あなたの役割

AlgEの主な役割は、**アルゴリズムのPoC検証から本番実装まで**を担当することです。

**作業場所**: `backend/packages/alg/`

---

## 🚀 作業フロー: PoC検証からSW開発まで

### フロー全体像

```
【PoC段階】
1. sandbox/      → notebook/scriptで自由に検証(実際の運用方法は、PMと相談してください。)
2. ↓ Approveを取得
3. core/ + models/ → 検証コードをモジュールとして移植
4. experimental/ → core/の複数モジュールを組み合わせたPoC用インターフェース

【SW開発段階】
5. entrypoints/  → core/の複数モジュールを組み合わせたAPI用インターフェース
```

### experimental/ と entrypoints/ の違い

| 項目 | experimental/ | entrypoints/ |
|------|--------------|-------------|
| **作成タイミング** | PoC段階 | SW開発段階 |
| **利用者** | AlgE (sandbox内で検証) | SWE (Backend APIで利用) |
| **目的** | アルゴリズムの検証 | 本番環境での提供 |
| **実装内容** | core/の複数モジュールを組み合わせ | core/の複数モジュールを組み合わせ |

**重要**: experimental/ と entrypoints/ は**実装タイミングが異なるだけで、どちらもcore/の複数モジュールを組み合わせた関数**です。

---

## Step 1: sandbox/ で自由に検証 (PoC段階)

### 📁 作業場所

`backend/packages/alg/sandbox/{あなたの名前}/`

### 📝 やること

**notebook形式（推奨）** または **script形式** で自由に検証します。

- データの前処理
- アルゴリズムの試行錯誤
- LLMやAWSの接続テスト
- 精度の検証

### ✅ ファイル命名規則

```
{名前}/{n|s}_{日付}_{実施内容}.py
```

- `{名前}`: 実施者の名前（例: `tanaka`, `yamada`）
- `{n|s}`: ファイルタイプ
  - `n`: notebook（推奨）
  - `s`: script
- `{日付}`: 実施日（YYYYMMDD形式、例: `20250123`）
- `{実施内容}`: 内容の説明（snake_case、例: `test_llm_api`）

**例**:
```
backend/packages/alg/sandbox/tanaka/n_20250123_test_llm_api.py
backend/packages/alg/sandbox/yamada/s_20250124_data_preprocessing.py
```

### 📖 notebook形式（`n`で始まるファイル）の書き方

VSCodeやPyCharmでインタラクティブに実行できるよう、**セル区切り `# %%`** を使用してください。

**例**:

```python
# %%
# セル1: インポート
import pandas as pd
from gateways.llm.connections import get_openai_client

# %%
# セル2: データ読み込み
df = pd.read_csv("data.csv")
print(df.head())

# %%
# セル3: アルゴリズム検証
# ...
```

### 🔑 重要なポイント

#### 1. 既存コードを再利用する

- Backend固有の機能: `from src.`から始まるimportを使用
- 共有パッケージ: `from alg.`や`from gateways.`のようにパッケージ名から始まるimportを使用

#### 2. RDBには直接アクセスしない

`gateways.rdb`は`alg`から使用禁止です。データが必要な場合は、SWEに相談してください。

---

## Step 2: Approveを取得後、core/ + models/ に移植 (PoC段階)

### 📁 作業場所

- `backend/packages/alg/alg/core/` - 内部ロジック
- `backend/packages/alg/alg/models/` - データモデル

### 📝 やること

sandboxで検証したコードを、再利用可能なモジュールとして実装します。

#### 2-1. `models/` にデータモデルを実装

Pydanticの`BaseModel`を使用してデータモデルを定義します。

#### 2-2. `core/` に内部ロジックを実装

モジュール単位で分割された**純粋関数**の集まり。

```
core/
└── {module_name}/     # モジュール名（例: llm_analysis）
    ├── tools/         # 単機能関数群
    └── pipelines/     # 複数のToolを組み合わせた処理フロー
```

### 🔑 重要なポイント

- `core/` のコードはステートレスな純粋関数にする
- 副作用を避ける
- 単一責任の原則を守る

---

## Step 3: experimental/ で検証用インターフェースを作成 (PoC段階)

### 📁 作業場所

`backend/packages/alg/alg/experimental/`

### 📝 やること

**core/の複数モジュールを組み合わせた検証用の関数**を作成します。

- sandboxから `from alg.experimental.xxx import yyy_function` で利用可能
- PoC段階での精度検証に使用

### 🔑 重要なポイント

- experimentalはあくまで検証用
- 本番環境では使用しない
- SW開発段階では、同様の実装をentrypoints/に作成する

---

## Step 4: entrypoints/ でAPI用インターフェースを作成 (SW開発段階)

### 📁 作業場所

`backend/packages/alg/alg/entrypoints/`

### 📝 やること

**core/の複数モジュールを組み合わせたAPI用の関数**を作成します。

- SWEが `from alg.entrypoints.xxx import yyy_function` でBackend APIから利用
- 本番環境で使用される公開インターフェース

### 🔑 重要なポイント

#### entrypoints/の作成タイミング

**SW開発段階のみ**作成します。以下の条件を満たしたとき:

- ✅ PoC段階でアルゴリズムの精度が確認できた
- ✅ エラーハンドリングが実装されている
- ✅ テストが書かれている
- ✅ SWEがBackend APIで使用する準備ができた

#### experimental/との関係

- experimentalで検証した内容をベースに、entrypointsを作成
- 実装内容は似ているが、**利用タイミングと目的が異なる**
- experimentalはPoC用、entrypointsはSW開発用

---

## ⚠️ 注意点

### 1. 依存関係を守る

#### ✅ 使用可能

- `gateways.llm`: LLM接続（OpenAI, Anthropic等）
- `gateways.aws`: AWS接続（S3, Lambda等）
- `gateways.ocr`: OCR接続（文字認識サービス）
- `gateways.{service}`: その他の外部サービス
- `src.domain`: ドメインモデル
- `src.config`: 設定

#### ❌ 使用禁止

- `gateways.rdb`: RDB接続は禁止
- `src.features`: Backend固有の機能

**理由**: `alg`パッケージは純粋な計算ロジックを提供するため、データベースへの直接アクセスは行いません。

### 2. テストを書く

実装後は必ずテストを書いてください。

### 3. 外部サービスの呼び出しとpyproject.toml

`alg`パッケージで外部サービス（LLM, AWS, OCR等）を使用する場合は、`pyproject.toml`で依存関係を明示的に指定してください。

**重要**: 新しい外部サービスを追加する場合は、必ず`pyproject.toml`を更新してください。

詳細は [backend/packages/alg/README.md](../../backend/packages/alg/README.md#-外部サービスの呼び出し) を参照してください。

### 4. Lint & 型チェックを実行

実装後は必ず実行してください:

```bash
cd backend/api
make fix    # 自動修正
make lint   # Lint & 型チェック
```

---

## 🔍 よくある質問

### Q. sandboxで何を使える？

**A.** 以下を使用できます:

- `gateways.llm`: LLM接続（OpenAI, Anthropic等）
- `gateways.aws`: AWS接続（S3, Lambda等）
- `gateways.ocr`: OCR接続（文字認識サービス）
- `gateways.{service}`: その他の外部サービス
- `src.domain`: ドメインモデル
- `src.config`: 設定

### Q. sandboxでRDBにアクセスしたい

**A.** `alg`パッケージからは直接RDBにアクセスできません。データが必要な場合は、SWEに相談してください。

### Q. experimentalとentrypointsの使い分けは？

**A.**

- **experimental/**: PoC段階でsandboxから検証用に使用
- **entrypoints/**: SW開発段階でBackend APIから本番利用

実装内容は似ていますが、**利用タイミングと目的が異なります**。

### Q. entrypoints/はいつ作成する？

**A.** **SW開発段階のみ**作成します。PoC段階では作成しません。

### Q. models/には何を書く？

**A.** Pydanticの`BaseModel`を使用したデータモデルを定義します。

### Q. 新しい外部サービス（例: OCR）を使いたい

**A.** 以下の手順で追加してください:

1. `gateways`パッケージに新しいサービスモジュールを実装（SWEに依頼）
2. `backend/packages/alg/pyproject.toml`の`[project.optional-dependencies]`に追加
3. `uv pip install -e ".[ocr]"`でインストール
4. `alg.core`から`from gateways.ocr.connections import ...`で呼び出す

---

## 📚 参考ドキュメント

- **アーキテクチャ詳細**: [backend/docs/architecture.md](../../backend/docs/architecture.md)
- **依存関係図**: [backend/docs/dependencies.mmd](../../backend/docs/dependencies.mmd)
- **algパッケージのREADME**: [../../backend/packages/alg/README.md](../../backend/packages/alg/README.md)
