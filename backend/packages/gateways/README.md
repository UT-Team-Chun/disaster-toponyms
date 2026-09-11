# Gateways Package

外部システム接続パッケージ。
バックエンドとジョブアプリケーション間で共有される外部システムとの接続・操作を提供します。

> **📖 このREADMEについて**
>
> このファイルには、**backend/packages/gateways/ のディレクトリ構造**、**開発コマンド**、**実装パターン**、**コード規約**が記載されています。
>
> - **SWEの作業手順やDB操作の追加方法** → [docs/roles/software_engineer.md](../../../docs/roles/software_engineer.md) を参照してください
> - **アーキテクチャ設計の詳細** → [backend/docs/architecture.md](../../docs/architecture.md) を参照してください
> - **依存関係図** → [backend/docs/dependencies.mmd](../../docs/dependencies.mmd) を参照してください

---

## 📂 ディレクトリ構造

```
backend/packages/gateways/
└── gateways/                # パッケージ本体
    ├── rdb/                 # RDB接続
    │   ├── connections.py   # DB接続管理
    │   ├── models/          # SQLAlchemyモデル (ORM)
    │   └── operations/
    │       └── repositories/  # Repository実装 (CRUD操作)
    │
    ├── llm/                 # LLM接続 (OpenAI等)
    │   ├── connections.py   # クライアント生成
    │   ├── config.py        # モデル名・推論レベル・APIキー
    │   ├── models/          # データモデル
    │   └── operations/      # LLM操作 (generate / generate_json)
    │
    ├── aws/                 # AWS接続 (S3等)
    │   ├── connections.py   # クライアント生成
    │   ├── models/          # データモデル
    │   └── operations/      # AWS操作
    │
    ├── http/                # 共有HTTPクライアント（ディスクキャッシュ・レート制限）
    ├── gsi/                 # 国土地理院（住所検索・ハザードタイル・自然災害伝承碑）
    ├── estat/               # e-Stat（国勢調査 小地域境界）
    ├── ndl/                 # 国立国会図書館（次世代デジタルライブラリーの全文OCR）
    ├── nihu/                # 人間文化研究機構（歴史地名データ）
    ├── codh/                # 人文学オープンデータ共同利用センター（歴史地名索引）
    └── web/                 # 一般Webページ・Wikipedia
```

### 警鐘地名マップで使うゲートウェイ

| モジュール | 取得するもの | 出典・条件 |
|---|---|---|
| `ndl` | 『大日本地名辞書』のコマ単位 OCR 全文とブロック外接矩形 | パブリックドメイン資料 |
| `nihu` | 歴史地名 29.8 万件の緯度経度・読み・原本の表記 | 出典明示のうえ自由利用 |
| `codh` | 歴史地名 8 万件の現在の住所と代表点 | CC BY 4.0 |
| `gsi` | 自然災害伝承碑・ハザードタイル・住所検索 | 国土地理院コンテンツ利用規約 |
| `estat` | 町丁・字等の境界ポリゴン | 政府統計の総合窓口 |

`http` は共有クライアントで、応答を `data/cache/http/` に保存し、ホストごとに
間隔を空けて要求します。一部の政府系サーバは旧方式の TLS 再ネゴシエーションを
行うため、`OP_LEGACY_SERVER_CONNECT` を有効にしています。

---

## 🎯 各サービスの役割

### `rdb/` - RDB接続・データベース操作

**Repository Pattern** を採用し、SQLAlchemyを使用します。

#### connections.py
- `get_sync_session()`: 同期セッションを取得 (FastAPIの依存性注入で使用)
- `get_async_session()`: 非同期セッションを取得 (将来の拡張用)
- Alembicによるマイグレーション管理

#### models/
- SQLAlchemyモデル (ORM)
- `Base`: すべてのORMモデルの基底クラス
- テーブル定義 (例: `User`, `Project` など)

#### operations/repositories/
- CRUD操作の実装
- **重要**: ORMオブジェクトをそのまま返さず、必ずPydanticモデルに変換して返す
- トランザクション管理は呼び出し側 (usecase) の責任

---

### `llm/` - LLM接続 (OpenAI等)

#### connections.py
- `get_openai_client()`: OpenAIクライアントの取得

#### operations/
- LLM操作の実装 (テキスト生成、埋め込み生成など)

---

### `aws/` - AWS接続 (S3等)

#### connections.py
- `get_s3_client()`: S3クライアントの取得

#### operations/
- AWS操作の実装 (S3アップロード、ダウンロードなど)

---

## ⚠️ 重要なルール

### 1. ORMオブジェクトの流出禁止

RepositoryはORMオブジェクトをそのまま返さず、必ずPydanticモデルに変換して返してください。

### 2. トランザクション管理

Repositoryはトランザクション管理を行いません（`commit`, `rollback`しない）。

- Repositoryでは必要に応じて`flush()`のみ使用 (IDを取得する場合など)
- トランザクション管理は呼び出し側 (usecase) の責任

### 3. セッション管理

FastAPIの`Depends(get_sync_session)`で依存性注入します。

---

## 🔍 よくある質問

### Q. 新しいRepositoryを追加したい

**A.** `gateways/rdb/operations/repositories/` にファイルを作成してください。

### Q. マイグレーションを実行したい

**A.** Alembicを使用してスキーマ変更を管理します:

```bash
# マイグレーションファイル生成
alembic revision --autogenerate -m "Add users table"

# マイグレーション実行
alembic upgrade head
```

### Q. LLMを使いたい

**A.** `gateways.llm`を使用してください。

### Q. AWSを使いたい

**A.** `gateways.aws`を使用してください。

---

## 📚 参考ドキュメント

- **アーキテクチャ詳細**: [docs/architecture.md](../../docs/architecture.md)
- **依存関係図**: [docs/dependencies.mmd](../../docs/dependencies.mmd)
