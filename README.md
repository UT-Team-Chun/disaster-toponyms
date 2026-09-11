# disaster-toponyms — 警鐘地名マップ

日本の**警鐘地名（災害地名）**を、文字パターンではなく地誌・地名考・伝承・災害記録という
**出典に基づいて**集約し、日本地図上に表示します。

**公開先: <https://ut-team-chun.github.io/disaster-toponyms/>**

群馬県桐生市の旧小字「梅ヶ久保」は字面では梅の生えた窪地に見えますが、『桐生市地名考』は
「梅は埋の替字で山腹の崩壊で埋まって傾斜地の出来たくぼ」と記しています。
災害を示す字は無難な字に置き換えられる（替字）ため、表記の一致だけでは取りこぼします。
そこで各地名に**根拠レベル**（0: 字面のみ／1: 地形由来の記載／2: 災害由来・替字の明記／
3: 災害記録・伝承との対応）を付け、出典の逐語引用とともに表示します。

出典自身が由来に疑義を示す場合は**異説あり**として反証も並べます
（例: 広島市八木の「八木蛇落地悪谷」は伝説が寺に伝わる一方、広島市郷土資料館は
「蛇落地」「悪谷」を記す文献を確認できないとしている）。

地名は点ではなく広がりです。ハザードマップとして読めるよう、各地名が属する
**町丁・字等の範囲**を国勢調査の境界データから重ねて表示します
（小字の境界は全国では公開されていないため、これが公開されている最も細かい単位です）。

| 区分 | 件数 |
|---|---|
| 出典で裏づけた地名（全47都道府県） | 1,066（レベル3: 39 / レベル2: 193 / レベル1: 834） |
| 字面のみの候補（全47都道府県） | 18,001（うち現在の住所に残らない旧地名 7,380） |
| 被災記録が結びついた地名 | 127 |
| 地名がカバーする範囲 | 7,432 |
| 自然災害伝承碑 | 2,469 |

収録の密度は「危険の密度」ではなく **「資料を読み込めた地域」** を表します。
全国は吉田東伍『大日本地名辞書』（1907年、パブリックドメイン）で覆っていますが、
由来を説明している項目は一部にすぎません。一方で桐生市のように市域の小字すべてに
解説を付けた地名考がある地域は密度が高くなります。

> **📖 データパイプラインと設計の詳細**: [docs/disaster_toponyms.md](docs/disaster_toponyms.md)

```bash
# データセットの再生成（pdftotext が必要: brew install poppler）
cd backend && make download-data && make build-data

# サイトのローカル確認（GitHub Pages と同じサブパスで配信）
cd frontend && yarn build:pages && yarn preview:pages
```

---

## 技術基盤

FastAPI (Backend) と React Router v7 (Frontend) のモノレポ。
**Vertical Slice Architecture** と **DDD** の要素を組み合わせた設計で、機能の独立性と計算ロジックの純粋性を重視しています。
公開サイトは静的 SPA として配信するため、閲覧時に Backend API は使いません。

> **📖 このREADMEについて**
>
> このファイルには、**プロジェクト全体の概要**、**クイックスタート**、**ドキュメントの目次**が記載されています。
>
> - **作業手順やベストプラクティス** → [役割別ガイド](#-役割別ガイド) を参照してください
> - **各フォルダの詳細な構成やコマンド** → 各ディレクトリのREADME ([backend/api](backend/api/README.md), [frontend](frontend/README.md) など) を参照してください
> - **アーキテクチャ設計の詳細** → [backend/docs/architecture.md](backend/docs/architecture.md) を参照してください

---

## 🎯 プロジェクト概要

### 技術スタック

**Backend**
- FastAPI (Python 3.12+) / SQLAlchemy / Alembic / uv

**Frontend**
- React 19 / React Router v7 / TypeScript 5.9 / Tailwind CSS v4 / Vite 7

**共有パッケージ**
- `alg`: アルゴリズム・計算ロジック
- `gateways`: 外部システム接続 (RDB, LLM, AWS)

### プロジェクト構造

```
project_root/
├── frontend/          # React Router v7 アプリケーション（静的SPA・地図UI）
│   └── public/data/   # ビルド済みデータセット（Pages が配信）
├── backend/
│   ├── api/           # FastAPI アプリケーション
│   └── packages/
│       ├── alg/       # アルゴリズム・計算ロジック（データパイプライン本体）
│       └── gateways/  # 外部システム接続 (RDB, LLM, AWS, GSI, NDL, Web)
├── data/
│   ├── curated/       # 人手キュレーション（要素辞典・出典・代表事例）※git 管理
│   └── raw/           # 取得した公開データ ※git 管理外
└── docs/              # プロジェクト全体のドキュメント
```

---

## 🚀 クイックスタート

### Backend

```bash
cd backend/api
uv sync
make dev
```

APIサーバーが http://localhost:8000 で起動します。

### Frontend

```bash
cd frontend
yarn install
yarn dev
```

開発サーバーが http://localhost:5173 で起動します。

### データセット

地図が表示するデータは `frontend/public/data/` にコミット済みです。
再生成する場合のみ以下を実行します（`pdftotext` が必要: `brew install poppler`）。

```bash
cd backend
make download-data   # 公開データを data/raw/ に取得
make build-data      # frontend/public/data/ に書き出す
```

### 公開

`main` への push で GitHub Actions が GitHub Pages に配信します
（[.github/workflows/deploy_pages.yml](.github/workflows/deploy_pages.yml)）。

---

## 👥 役割別ガイド

あなたの役割に応じたガイドを参照してください。

### AlgE (Algorithm Engineer) 向け

**主な作業場所**: `backend/packages/alg/`

- **[AlgE作業ガイド](docs/roles/algorithm_engineer.md)** - PoC検証から本番実装までの作業手順
- [アルゴリズムパッケージREADME](backend/packages/alg/README.md) - フォルダ構成・コマンド・依存関係

### SWE (Software Engineer) 向け

**主な作業場所**: `backend/api/src/features/`, `frontend/app/`

- **[SWE作業ガイド](docs/roles/software_engineer.md)** - Backend/Frontend開発の作業手順
- [Backend API README](backend/api/README.md) - フォルダ構成・コマンド・依存関係
- [Frontend README](frontend/README.md) - フォルダ構成・コマンド・依存関係

---

## 📚 ドキュメント

### 役割別ガイド

| ドキュメント | 説明 |
|------------|------|
| [docs/roles/algorithm_engineer.md](docs/roles/algorithm_engineer.md) | **AlgE作業ガイド** - PoC検証から本番実装までの作業手順 |
| [docs/roles/software_engineer.md](docs/roles/software_engineer.md) | **SWE作業ガイド** - Backend/Frontend開発の作業手順 |

### プロジェクト全体

| ドキュメント | 説明 |
|------------|------|
| [docs/disaster_toponyms.md](docs/disaster_toponyms.md) | **警鐘地名マップ** - データパイプライン・根拠レベル・版面パーサ・LLMの制約・収録の増やし方 |
| [frontend/public/data/README.md](frontend/public/data/README.md) | 配信データの内容・根拠レベル・出典と利用条件 |

### Backend

| ドキュメント | 説明 |
|------------|------|
| [backend/api/README.md](backend/api/README.md) | FastAPI アプリケーション - フォルダ構成・コマンド・依存関係 |
| [backend/packages/alg/README.md](backend/packages/alg/README.md) | アルゴリズムパッケージ - フォルダ構成・コマンド・依存関係 |
| [backend/packages/gateways/README.md](backend/packages/gateways/README.md) | ゲートウェイパッケージ - フォルダ構成・コマンド・依存関係 |
| [backend/docs/architecture.md](backend/docs/architecture.md) | Backendアーキテクチャ設計の詳細 |
| [backend/docs/dependencies.mmd](backend/docs/dependencies.mmd) | Backend依存関係図（Mermaid） |
| [backend/docs/lint.md](backend/docs/lint.md) | Lintエラーの対処法 |

### Frontend

| ドキュメント | 説明 |
|------------|------|
| [frontend/README.md](frontend/README.md) | React Router v7 アプリケーション - フォルダ構成・コマンド・依存関係 |
| [frontend/docs/ARCHITECTURE.md](frontend/docs/ARCHITECTURE.md) | Frontendアーキテクチャの詳細 |

---

## 🆘 困ったときは

- **アーキテクチャで悩んだら**: [backend/docs/architecture.md](backend/docs/architecture.md)
- **Lintエラーが出たら**: [backend/docs/lint.md](backend/docs/lint.md)
- **依存関係がわからない**: [backend/docs/dependencies.mmd](backend/docs/dependencies.mmd)

---

## 📖 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [React Router公式ドキュメント](https://reactrouter.com/)
- [uv公式ドキュメント](https://docs.astral.sh/uv/)
