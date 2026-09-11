# Frontend Application

React Router v7とTypeScriptを使用した、モダンなフルスタックWebアプリケーションのテンプレートです。

> **📖 このREADMEについて**
>
> このファイルには、**frontend/ のディレクトリ構造**、**セットアップ手順**、**開発コマンド**、**依存関係ルール**、**コード規約**が記載されています。
>
> - **Frontend開発の作業手順やベストプラクティス** → [docs/roles/software_engineer.md](../docs/roles/software_engineer.md) を参照してください
> - **アーキテクチャ設計の詳細** → [frontend/docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) を参照してください

---

## 📂 ディレクトリ構造

```
frontend/
├── app/
│   ├── routes/               # React Routerのルート定義
│   │   ├── _index.tsx       # トップページ
│   │   ├── projects/        # プロジェクト一覧ページ
│   │   └── projects_.$id/   # プロジェクト詳細ページ
│   │
│   ├── features/            # 機能ごとのディレクトリ
│   │   └── {feature_name}/
│   │       ├── components/  # 機能固有のコンポーネント
│   │       ├── hooks/       # 機能固有のカスタムフック
│   │       └── {feature}Route.tsx
│   │
│   ├── components/
│   │   └── ui/             # shadcn/uiのUIコンポーネント
│   │
│   ├── lib/                # ユーティリティ関数
│   │   ├── utils.ts        # 汎用ユーティリティ
│   │   ├── fetch.ts        # API通信関連
│   │   └── safeRedirect.ts # 安全なリダイレクト処理
│   │
│   ├── gen/                # Orvalで生成されたAPIクライアント
│   │   ├── default/        # API関数
│   │   └── schema/         # 型定義
│   │
│   ├── env.ts              # 環境変数定義
│   ├── app.css             # グローバルスタイル
│   └── root.tsx            # アプリケーションルート
│
├── public/                 # 静的ファイル
├── .env.development        # 開発環境の環境変数
├── vite.config.ts          # Vite設定
├── react-router.config.ts  # React Router設定
├── vitest.config.mjs       # Vitest設定
├── eslint.config.js        # ESLint設定
├── components.json         # shadcn/ui設定
└── package.json
```

---

## ⚠️ 重要な制約

### Node 22 以上 / Yarn 1 (classic)

`orval` が Node 22 以上を要求します。`yarn.lock` は **v1 形式**で、
`package.json` の `packageManager` で `yarn@1.22.22` に固定しています。
Corepack 経由で Yarn Berry を使うとロックファイルが v8 に変換され、CI が壊れます。

```bash
node --version   # v22 以上であること
yarn --version   # 1.22.22 であること
```

### 閲覧時に Backend API は呼ばない

公開サイトは静的 SPA（`ssr: false`）で、`public/data/` に置いた GeoJSON / JSON を
fetch します。取得は `app/lib/dataset/client.ts` に集約しています。
Backend API を追加する場合は従来どおり Orval 生成コードを使ってください。

### Tailwind v4 と maplibre-gl.css

`maplibre-gl.css` は Tailwind のカスケードレイヤーの外にあるため、
`.maplibregl-map { position: relative }` が `absolute` などのユーティリティに勝ちます。
地図コンテナの位置と大きさはインラインスタイルで指定しています
（`app/features/toponym-map/components/mapView.tsx`）。

---

## ⚙️ セットアップ

### 依存関係のインストール

```bash
yarn install
```

### 環境変数の設定

`.env.development`ファイルを作成し、必要な環境変数を設定してください。

```bash
# .env.development の例
VITE_API_URL=http://localhost:8000
```

---

## ⚙️ 開発コマンド

### 開発サーバーの起動

```bash
yarn dev
```

アプリケーションは `http://localhost:5173` で起動します。

### APIクライアント生成

OpenAPI仕様からAPIクライアントを生成します。

```bash
yarn gen
```

### Lint実行

```bash
yarn lint
```

### フォーマット

```bash
yarn fmt
```

### 型チェック

```bash
yarn typecheck
```

### テスト実行

```bash
yarn test
```

---

## 🏗️ ビルド

### プロダクションビルド

```bash
yarn build
```

### GitHub Pages 向けビルド

リポジトリ名がパスの先頭に付くため、`basename` を与えてビルドし、
SPA フォールバック用の `404.html` を生成します。

```bash
yarn build:pages    # VITE_BASE_PATH=/disaster-toponyms/ でビルド
yarn preview:pages  # 同じサブパスでローカル配信して確認
```

ビルド成果物は以下のディレクトリに出力されます：

```
build/
└── client/    # 静的アセット
```

### プロダクション起動

```bash
yarn start
```

---

## 🔗 依存関係ルール

### ✅ 使用可能な依存関係

```
app/routes → app/features
app/routes → app/components/ui

app/features → app/components/ui
app/features → app/lib

app/components/ui → app/lib (utils only)
```

### ❌ 使用禁止の依存関係

```
❌ app/components/ui → app/features
❌ app/components/ui → app/routes
❌ app/features → app/features (機能間の直接参照)
```

---

## 📖 コード規約

### パスエイリアス

`~` をルートとした絶対パスを使用してください。

### 汎用UIコンポーネントの追加

shadcn/uiを使用して汎用UIコンポーネントを追加してください:

```bash
yarn shadcn add button
yarn shadcn add card
```

### APIクライアントの使用

**必ず `gen/` に生成されたAPIクライアントを使用してください**。

**手動で `axios` や `fetch` を使ってAPIを呼び出すことは禁止**です。

### 環境変数

`@t3-oss/env-core`を使用した型安全な環境変数管理を行います。

環境変数は `app/env.ts` で定義し、`.env.development` にも追加してください。

---

## 🛠️ 技術スタック

### コアフレームワーク

- **[React](https://react.dev/)** v19 - UIライブラリ
- **[React Router](https://reactrouter.com/)** v7 - SSR対応のルーティングフレームワーク
- **[TypeScript](https://www.typescriptlang.org/)** - 型安全な開発環境
- **[Vite](https://vite.dev/)** - 高速ビルドツール

### スタイリング

- **[Tailwind CSS](https://tailwindcss.com/)** v4 - ユーティリティファーストCSSフレームワーク
- **[shadcn/ui](https://ui.shadcn.com/)** - Radix UIベースのコンポーネントライブラリ

### ツール・ライブラリ

- **[Vitest](https://vitest.dev/)** - 高速なユニットテストフレームワーク
- **[ESLint](https://eslint.org/)** - コード品質チェック
- **[Prettier](https://prettier.io/)** - コードフォーマッター
- **[Orval](https://orval.dev/)** - OpenAPI仕様からAPIクライアント自動生成
- **[Zod](https://zod.dev/)** - スキーマバリデーション
- **[ky](https://github.com/sindresorhus/ky)** - モダンなHTTPクライアント
- **[@t3-oss/env-core](https://env.t3.gg/)** - 型安全な環境変数管理

---

## 📚 参考ドキュメント

- **React Router v7の詳細**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **SWE向け作業ガイド**: [docs/roles/software_engineer.md](../docs/roles/software_engineer.md)

---

## 📖 公式ドキュメント

- [React Router Documentation](https://reactrouter.com/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Vite Documentation](https://vite.dev/)
- [Vitest Documentation](https://vitest.dev/)
