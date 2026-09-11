# Software Engineer (SWE) 作業ガイド

このガイドは、Software Engineer (SWE) がBackend API/Frontend UIの実装を行う際の作業手順と注意点をまとめたものです。

---

## 🎯 あなたの役割

SWEの主な役割は、**Backend APIとFrontend UIの実装からテストまで**を担当することです。

**作業場所**:
- Backend: `backend/api/src/features/`
- Frontend: `frontend/app/`

---

## 🚀 Backend 開発フロー

### フロー全体像

```
1. features/ にAPI実装
2. OpenAPI仕様書を生成
3. テスト実装
4. Lint & 型チェック
```

---

### Step 1: Backend API実装 (`src/features/`)

#### 📁 作業場所

`backend/api/src/features/{feature_name}/`

#### 📝 やること

機能単位で以下の3つのファイルを作成します:

```
src/features/{feature_name}/
├── router.py                    # APIの入口（入力検証のみ）
├── usecase.py                   # ビジネスロジックのオーケストレーション
└── request_and_response.py      # リクエスト・レスポンスのスキーマ
```

#### 🔑 重要なポイント

##### 1. Routerはロジックを書かない

Routerは入力検証のみを行い、usecaseを呼び出します。

##### 2. Usecaseがトランザクション管理を行う

トランザクションの責任はUsecaseにあります。

- `session.commit()` - Usecaseで実行
- `session.rollback()` - Usecaseで実行
- `session.close()` - Usecaseで実行

---

### Step 2: OpenAPI仕様書の生成

API変更後は必ず実行してください:

```bash
cd backend/api
make openapi-generate
```

これにより、`openapi.yaml` が生成され、Frontendで型安全なAPIクライアントを生成できるようになります。

---

### Step 3: テスト実装 (`tests/`)

#### 📁 作業場所

`backend/api/tests/`

#### 📝 やること

実装したAPIのテストを作成します。

---

### Step 4: Lint & 型チェック

実装後は必ず実行してください:

```bash
cd backend/api
make fix    # 自動修正
make lint   # Lint & 型チェック
make test   # テスト実行
```

---

## 🚀 Frontend 開発フロー

### フロー全体像

```
1. Backend APIからOpenAPI仕様書を取得
2. yarn gen でAPIクライアント生成
3. features/ にUI実装
4. Lint & 型チェック
```

---

### Step 1: Backend APIからOpenAPI仕様書を取得

Backend側でAPIが実装されたら、OpenAPI仕様書を生成してもらいます:

```bash
cd backend/api
make openapi-generate
```

---

### Step 2: APIクライアントの生成

Frontend側でAPIクライアントを生成します:

```bash
cd frontend
yarn gen
```

生成されたコードは `app/gen/` に配置されます:

```
app/gen/
├── default/              # タグごとに分割されたAPI関数
│   └── default.ts        # API呼び出し関数
└── schema/               # TypeScript型定義
    └── *.ts              # レスポンス・リクエストの型定義
```

---

### Step 3: Frontend実装 (`app/`)

#### 📁 作業場所

`frontend/app/features/{feature_name}/`

#### 📝 やること

機能単位で以下のように実装します:

```
app/features/{feature_name}/
├── components/           # 機能固有のUIコンポーネント
├── hooks/               # カスタムフック
└── {feature}Route.tsx   # ルートコンポーネント
```

#### 🔑 重要なポイント

##### 1. 必ずOrval生成のAPIクライアントを使用

手動でfetchを使ってはいけません。必ず `app/gen/` に生成されたAPIクライアントを使用してください。

##### 2. routes/はロジックを書かない

routes/はデータ取得とコンポーネントの配置のみを行います。複雑なUIロジックは`features/`に実装してください。

---

### Step 4: Lint & 型チェック

実装後は必ず実行してください:

```bash
cd frontend
yarn fmt        # フォーマット
yarn lint       # Lint
yarn typecheck  # 型チェック
yarn test       # テスト実行
```

---

## ⚠️ 注意点

### Backend

#### 1. AlgEが作成したアルゴリズムを使う

**SW開発段階では** `alg.entrypoints`からimportしてください:

```python
from alg.entrypoints.sample_entrypoint import calculate_with_description

# usecaseで使用
result = calculate_with_description(value=100)
```

**重要**:
- `alg.experimental`を使用しないでください（PoC段階のみ使用）
- `alg.core`を直接使用しないでください（entrypoints経由で使用）

#### 2. DB操作を追加する

`gateways/rdb/operations/repositories/` にRepositoryを実装してください。

**重要**: トランザクション管理はUsecaseで行います（Repositoryでは`commit`しない）。

### Frontend

#### 1. Backend APIが更新されたら

以下の手順で再生成してください:

1. Backend側でOpenAPI仕様書を生成: `cd backend/api && make openapi-generate`
2. Frontend側でAPIクライアントを再生成: `cd frontend && yarn gen`

#### 2. 汎用UIコンポーネントを追加

shadcn/uiを使用してください:

```bash
yarn shadcn add button
yarn shadcn add card
```

生成されたコンポーネントは `app/components/ui/` に配置されます。

#### 3. 環境変数を追加

`app/env.ts` に追加してください。

`.env.development` にも追加します。

---

## 🔍 よくある質問

### Q. 依存関係がわからない

**A.** 以下のドキュメントを参照してください:

- [依存関係図 (Mermaid)](../../backend/docs/dependencies.mmd)
- [アーキテクチャ詳細](../../backend/docs/architecture.md)

### Q. Lintエラーが出たら

**A.** [Lintエラー対処法](../../backend/docs/lint.md)を参照してください。

### Q. 新しい機能を追加する際の手順は?

**A.** 以下の順序で実装してください:

1. Backend APIを実装 (`src/features/`)
2. OpenAPI仕様書を生成 (`make openapi-generate`)
3. Frontend APIクライアントを生成 (`yarn gen`)
4. Frontend UIを実装 (`app/features/`)
5. テストを実装
6. Lint & 型チェック

### Q. AlgEのexperimentalを使いたい

**A.** `alg.experimental`は**PoC段階のみ**使用します。**SW開発段階では`alg.entrypoints`を使用**してください。

### Q. entrypointsはいつ作成される?

**A.** **SW開発段階**でAlgEが作成します。PoC段階で作成されたexperimentalをベースに、API用のインターフェースとしてentrypointsを実装します。

---

## 📚 参考ドキュメント

- **アーキテクチャ詳細**: [backend/docs/architecture.md](../../backend/docs/architecture.md)
- **依存関係図**: [backend/docs/dependencies.mmd](../../backend/docs/dependencies.mmd)
- **Lintエラー対処法**: [backend/docs/lint.md](../../backend/docs/lint.md)
- **Backend APIのREADME**: [../../backend/api/README.md](../../backend/api/README.md)
- **FrontendのREADME**: [../../frontend/README.md](../../frontend/README.md)
