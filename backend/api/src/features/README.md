# features/

機能レイヤー（Vertical Slices）。アプリケーションの機能単位でフォルダを分割し、各機能に必要なすべてのコンポーネントをまとめます。

## 役割

- APIエンドポイントの定義と入力検証
- ユースケース（ビジネスフロー）の実装
- トランザクション管理
- 各レイヤー（domain_models, alg, gateways, config）の統合

## ディレクトリ構成

```
features/
├── case1/              # 機能1（ユースケース1）
│   ├── router.py       # FastAPI Router（API入口）
│   ├── usecase.py      # ユースケース（ビジネスフロー）
│   ├── request_and_response.py       # API I/O定義（Request/Response）
│   └── model.py        # 機能固有の内部モデル
├── health/             # ヘルスチェック機能
│   └── router.py
└── ...                 # 新しい機能ごとにフォルダを追加
```

## 各ファイルの役割

### `router.py` (API入口)
- FastAPIのルーター定義
- HTTPリクエストの受け取り
- 入力バリデーション（Pydantic Schema）
- `usecase.py`の呼び出し
- **ロジックは書かない**

### `usecase.py` (ビジネスフロー)
- アプリケーションの手順・フローの記述
- トランザクション管理（`commit`/`rollback`）の責任
- `domain_models`, `alg.entrypoints`, `gateways`, `config`の統合
- エラーハンドリング

### `request_and_response.py` (API I/O定義)
- APIのRequest/Responseモデル
- Pydanticモデルによる型定義とバリデーション

### `model.py` (機能固有モデル)
- この機能内でのみ使用する内部モデル
- 複数の機能で共有する場合は`domain_models/`に移動

## 実装ルール

### ✅ やるべきこと

- **機能の独立性**: 各機能は独立して動作する
- **トランザクション管理**: `usecase.py`でDBトランザクションを管理
- **レイヤーの統合**: `domain_models`, `alg`, `gateways`, `config`を組み合わせる

### ❌ やってはいけないこと

- **他機能への依存**: 他の`features/`フォルダを直接importしない
- **routerにロジック**: `router.py`にビジネスロジックを書かない
- **共通コードの重複**: 複数機能で共有するコードは`domain_models/`や`alg/`に移動

## 使用例

### router.py
```python
from fastapi import APIRouter, Depends
from features.case1.request_and_response import Case1Request, Case1Response
from features.case1.usecase import Case1Usecase

router = APIRouter(prefix="/case1", tags=["case1"])

@router.post("/", response_model=Case1Response)
def create_case1(request: Case1Request, usecase: Case1Usecase = Depends()):
    """Case1の作成"""
    return usecase.execute(request)
```

### usecase.py
```python
from gateways.operations.repositories.user_repository import UserRepository
from alg.entrypoints.scoring import calculate_score
from domain_models.domain_a import DomainA

class Case1Usecase:
    def __init__(self, user_repo: UserRepository = Depends()):
        self.user_repo = user_repo

    def execute(self, request: Case1Request) -> Case1Response:
        # 1. データ取得
        user = self.user_repo.get(request.user_id)

        # 2. ドメインモデルに変換
        domain = DomainA.from_orm(user)

        # 3. アルゴリズム実行
        score = calculate_score(domain)

        # 4. 結果保存
        self.user_repo.update_score(user.id, score)
        self.user_repo.commit()  # トランザクション完了

        return Case1Response(score=score)
```

## 依存関係

```
features → domain_models
features → alg.entrypoints
features → gateways
features → config

❌ features → features (他機能への依存禁止)
```
