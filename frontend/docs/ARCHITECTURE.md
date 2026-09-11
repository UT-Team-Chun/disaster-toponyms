# Frontend アーキテクチャ詳細ガイド

このドキュメントは、本プロジェクトのフロントエンドアーキテクチャの思想、ディレクトリ構成のルール、および開発時の注意点を詳しくまとめたものです。AIアシスタントを使用してコードを生成・修正する際は、このルールを前提知識（Context）として使用してください。

---

## 1. 設計思想 (Core Philosophy)

本プロジェクトは **React Router v7** をベースに、**機能単位の分割 (Feature-based / Vertical Slice Architecture)** を採用しています。

### 主な目的

#### 1.1 凝集度の向上 (Colocation)

特定の機能（例: projects）に関連するコード（コンポーネント、フック、型定義）を1つのディレクトリに集約することで:

- コードの見通しを良くする
- 修正時の影響範囲を限定する
- 機能単位での理解が容易になる

#### 1.2 AIとの親和性

機能ごとにディレクトリが独立しているため:

- AIに対して「この機能のフォルダ」をコンテキストとして与えるだけで、高精度なコード生成が可能
- 機能間の依存関係が明確で、AIが混乱しにくい
- 既存のパターンを参照しやすい

#### 1.3 UIとロジックの分離

「見た目を作る汎用部品」と「データを扱う機能部品」を明確に区別することで:

- デザインシステムの一貫性を保つ
- ビジネスロジックとプレゼンテーションの責務を分離
- 再利用性を高める

---

## 2. ディレクトリ構成と役割 (Directory Structure)

```
app/
├── routes/          # 1. ページのエントリーポイント (URLと対応)
├── features/        # 2. ドメインロジックの実装 (機能単位で分割)
├── components/ui/   # 3. 汎用UIコンポーネント (ドメイン知識なし)
├── lib/             # 4. 共通ユーティリティ (純粋関数)
└── gen/             # 5. 自動生成されたAPIクライアント (Orval)
```

### 詳細解説

| ディレクトリ           | 役割・責務                                                                                                                       | Do / Don't                                                                                                                  |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **app/routes/**        | 「データの入口」と「ルーティング」<br>- ページのURL定義<br>- loader/actionによるデータフェッチ<br>- ページの全体レイアウトを担当 | ✅ features からコンポーネントをimportして配置する<br>⛔ 複雑なUIロジックや長いJSXをここに直接書かない                      |
| **app/features/**      | 「機能の実体」<br>- ビジネスロジック<br>- 機能固有のUI<br>- カスタムフック<br>- 型定義<br>例: projects/, auth/, dashboard/       | ✅ 特定機能に関わる変更は原則この中だけで完結させる<br>⛔ 他の features を直接importしない（依存関係が複雑になるため）      |
| **app/components/ui/** | 「汎用UIパーツ」<br>- ボタン、カード、テーブルなど<br>- 特定のビジネスロジックを持たない再利用可能な部品                         | ✅ props でデータやコールバックを受け取る設計にする<br>⛔ features や routes のコードをimportしてはいけない（循環参照禁止） |
| **app/lib/**           | 「共通処理」<br>- APIクライアント<br>- 日付操作<br>- バリデーションなど<br>アプリ全体で使うヘルパー関数                          | ✅ 純粋関数（Pure Function）であることを心がける<br>⛔ Reactコンポーネントを含めない                                        |
| **app/gen/**           | 「自動生成APIクライアント」<br>- Orvalで自動生成されたコード<br>- BackendのOpenAPI仕様書から生成<br>- 型安全なAPI呼び出し関数    | ✅ `yarn gen` で再生成する<br>⛔ 直接編集してはいけない（再生成時に上書きされる）                                           |

---

## 3. 依存関係のルール (Dependency Rules)

コードの保守性を保つため、**上から下への単方向依存** を厳守してください。

### ✅ 許可されるインポートの流れ

```
app/routes (Pages)
⬇️ imports
app/features/* (Domain Logic)
⬇️ imports
app/components/ui/* (Generic UI)
⬇️ imports
app/lib/* (Utils)
```

**別の視点で見ると:**

```
app/routes/ → app/features/*
app/routes/ → app/components/ui/*

app/features/* → app/components/ui/*
app/features/* → app/lib/*
app/features/* → app/gen/* (API calls)

app/components/ui/* → app/lib/* (utils only)

app/lib/* → app/gen/* (if needed)
```

### ⛔ 禁止されるインポート (Anti-Patterns)

| ❌ 禁止パターン                                                      | 理由                                       | 解決策                                                      |
| -------------------------------------------------------------------- | ------------------------------------------ | ----------------------------------------------------------- |
| `components/ui` が `features` をインポート                           | 汎用部品が特定の機能に依存してしまう       | propsで受け取る設計にする                                   |
| ある `feature` が別の `feature` の内部コンポーネントを深くインポート | 機能間の結合度が高まる                     | 共通化すべき機能であれば `lib` や `components` に昇格させる |
| `lib` が `features` をインポート                                     | ユーティリティがビジネスロジックに依存する | イベント経由で連携するか、設計を見直す                      |

---

## 4. 各レイヤーの詳細

### 4.1 routes/ (ルーティング層)

#### 役割

- URLパスとコンポーネントの対応付け
- データフェッチ（loader/action）
- ページ全体のレイアウト

#### ファイル命名規則（React Router v7 flat routes）

| パターン     | ファイルパス                          | URL                   | 説明                           |
| ------------ | ------------------------------------- | --------------------- | ------------------------------ |
| インデックス | `routes/_index.tsx`                   | `/`                   | トップページ                   |
| 静的ルート   | `routes/projects/route.tsx`           | `/projects`           | プロジェクト一覧               |
| 動的ルート   | `routes/projects_.$id/route.tsx`      | `/projects/:id`       | プロジェクト詳細               |
| ネストルート | `routes/dashboard.projects/route.tsx` | `/dashboard/projects` | ダッシュボード内のプロジェクト |

#### 実装例

```tsx
// routes/projects/route.tsx
import { ProjectsRoute } from "~/features/projects/projectsRoute";

export default function Projects() {
  return <ProjectsRoute />;
}
```

---

### 4.2 features/ (機能・ドメイン層)

#### 役割

- 特定機能に関するすべてのコード
- ビジネスロジック
- 機能固有のUI
- カスタムフック
- 型定義

#### ディレクトリ構成例

```
features/
└── projects/
    ├── components/
    │   ├── ProjectCard.tsx      # プロジェクトカード
    │   ├── ProjectList.tsx      # プロジェクト一覧
    │   └── ProjectForm.tsx      # プロジェクト作成フォーム
    ├── hooks/
    │   ├── useProjects.ts       # プロジェクト一覧取得
    │   ├── useProject.ts        # プロジェクト詳細取得
    │   └── useCreateProject.ts  # プロジェクト作成
    ├── types/
    │   └── project.ts           # 型定義
    └── projectsRoute.tsx        # ルートコンポーネント
```

#### 実装例

```tsx
// features/projects/projectsRoute.tsx
import { ProjectList } from "./components/ProjectList";
import { useProjects } from "./hooks/useProjects";

export function ProjectsRoute() {
  const { projects, loading } = useProjects();
  return <ProjectList projects={projects} loading={loading} />;
}
```

---

### 4.3 components/ui/ (汎用UI層)

#### 役割

- デザインシステムの構成要素
- shadcn/ui などの汎用UIライブラリ
- 特定のビジネスロジックを持たない

#### 実装原則

1. **propsでデータを受け取る**
2. **ビジネスロジックを持たない**
3. **featuresやroutesをimportしない**

#### 実装例

```tsx
// components/ui/button.tsx
interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "default" | "destructive";
}

export function Button({
  children,
  variant = "default",
  onClick,
}: ButtonProps) {
  return <button onClick={onClick}>{children}</button>;
}
```

---

### 4.4 lib/ (共通ユーティリティ層)

#### 役割

- 純粋関数
- APIクライアント
- バリデーション
- 日付操作
- 文字列操作

#### 実装原則

1. **純粋関数であること**
2. **Reactコンポーネントを含めない**
3. **副作用を最小限にする**

#### 実装例

```ts
// lib/utils.ts
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("ja-JP").format(date);
}

// lib/fetch.ts
export async function fetchApi<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}
```

---

### 4.5 gen/ (自動生成APIクライアント層)

#### 役割

- BackendのOpenAPI仕様書から自動生成されたAPIクライアント
- 型安全なAPI呼び出し関数
- TypeScript型定義（リクエスト・レスポンス）

#### ディレクトリ構成

```
gen/
├── default/            # タグごとに分割されたAPI関数
│   └── default.ts      # API呼び出し関数
└── schema/             # TypeScript型定義
    └── index.ts        # レスポンス・リクエストの型定義
```

#### 重要なルール

1. **直接編集禁止**
   - `yarn gen` で再生成されるため、手動での変更は失われる
   - カスタマイズが必要な場合は `lib/` にラッパー関数を作成

2. **BackendのAPIを呼び出す場合は必ずOrval生成コードを使用**
   - 手動で `axios` や `fetch` を使ってAPIを呼び出すことは禁止
   - 必ず `app/gen/` に生成されたコードを使用する

3. **BackendでAPIを更新した場合**
   - Backend側: `cd backend/api && make openapi-generate`
   - Frontend側: `cd frontend && yarn gen`

#### 実装例

```tsx
// features/projects/hooks/useProjects.ts
import { getProjects } from "~/gen/default/default";
import { Project } from "~/gen/schema";

export function useProjects() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProjects().then((data) => {
      setProjects(data);
      setLoading(false);
    });
  }, []);

  return { projects, loading };
}
```

---

## 5. 開発・AI生成時のガイドライン

### Q. どこにファイルを作成すべきか？

| やりたいこと                         | 配置場所                            | 具体例                       |
| ------------------------------------ | ----------------------------------- | ---------------------------- |
| 新しい画面を作りたい                 | `app/routes/`                       | `routes/dashboard.tsx`       |
| プロジェクト管理機能のUIを作りたい   | `app/features/projects/components/` | `components/ProjectCard.tsx` |
| プロジェクト管理のロジックを作りたい | `app/features/projects/hooks/`      | `hooks/useProjects.ts`       |
| 全体で使うデザインのボタンを変えたい | `app/components/ui/`                | `ui/button.tsx`              |
| 日付フォーマット関数を作りたい       | `app/lib/`                          | `lib/date.ts`                |
| BackendのAPIを呼び出したい           | `app/gen/` (自動生成)               | `yarn gen` で生成            |

### AIプロンプトへのヒント

AIにコード生成を依頼する際は、配置場所と依存関係のルールを明示してください。

**良い例:**

```
「プロジェクト管理機能を features/projects 内に実装してください。
UIパーツは components/ui の既存のものを再利用し、
他の features をimportしないでください。」
```

---

## 6. よくある質問 (FAQ)

### Q1: 複数の feature で同じロジックを使いたい場合は？

共通化すべきロジックは `lib/` に昇格させてください。

### Q2: feature 間でデータを共有したい場合は？

以下のいずれかを使用:

1. Context を使う (app/root.tsx で Provider を配置)
2. URL の search params や state を使う
3. loader から両方の feature に props を渡す

### Q3: components/ui のコンポーネントをカスタマイズしたい場合は？

直接編集してください。shadcn/ui のコンポーネントはコピーされたものなので自由にカスタマイズ可能です。

### Q4: gen/ のコードをカスタマイズしたい場合は？

`gen/` のコードは直接編集せず、`lib/` にラッパー関数を作成してください。`yarn gen` で再生成されると変更が失われます。

### Q5: BackendでAPIを追加・変更した場合は？

1. Backend側で OpenAPI 仕様書を生成: `cd backend/api && make openapi-generate`
2. Frontend側でAPIクライアントを再生成: `cd frontend && yarn gen`
3. 型チェックを実行: `yarn typecheck`

---

## 7. チェックリスト

実装時に以下をチェックしてください:

### ✅ 依存関係のチェック

- [ ] `components/ui` が `features` をimportしていないか？
- [ ] ある `feature` が別の `feature` を直接importしていないか？
- [ ] `lib` が Reactコンポーネントを含んでいないか？

### ✅ ファイル配置のチェック

- [ ] 機能固有のコンポーネントが `features/{feature}/components/` にあるか？
- [ ] 汎用UIコンポーネントが `components/ui/` にあるか？
- [ ] 純粋関数が `lib/` にあるか？
- [ ] BackendのAPI呼び出しに `gen/` の生成コードを使っているか？
- [ ] `gen/` のコードを直接編集していないか？

### ✅ コードスタイルのチェック

- [ ] パスエイリアス `~` を使っているか？
- [ ] PascalCase でコンポーネント名を書いているか？
- [ ] camelCase で関数・変数名を書いているか？

---

## 8. まとめ

本アーキテクチャの核心は以下の4点です:

1. **機能単位の独立性**: features/ で機能を完結させる
2. **単方向の依存関係**: 上から下へのみインポート
3. **UIとロジックの分離**: components/ui/ は汎用、features/ は機能固有
4. **型安全なAPI呼び出し**: gen/ (Orval) で自動生成されたコードを使用

この原則を守ることで、**保守性が高く、AIとの協調開発がしやすい** フロントエンドアーキテクチャを実現できます。

---

**Last Updated:** 2025-12-14
