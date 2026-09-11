# alg/

アルゴリズムレイヤー。純粋な計算ロジックを実装し、ビジネスロジックから分離します。

## 役割

- 純粋な計算・アルゴリズムの実装
- ステートレスな関数による処理
- 外部依存を持たない計算ロジック

## ディレクトリ構成

```
alg/
├── entrypoints/        # 公開インターフェース（Facade）
│   ├── scoring.py      # スコアリング処理の入口
│   └── ...
└── core/               # 内部実装（Private）
    ├── pipelines/      # 複数のToolを組み合わせた処理フロー
    ├── tools/          # ステートレスな単機能関数群
    └── scoring/        # スコアリング関連の内部実装
```

## 各ディレクトリの役割

### `entrypoints/` (公開インターフェース)
- `features/`（Usecase）が呼び出す**唯一の入口**
- Facadeパターン: Domainモデルを受け取り、`core/`の複雑な処理を隠蔽
- 依存性の逆転: `features/`は`core/`の詳細を知らない

### `core/` (内部実装)
- **`tools/`**: ステートレスな単機能関数
  - 例: `normalize()`, `calculate_weight()`, `apply_threshold()`
- **`pipelines/`**: 複数のToolを組み合わせた処理フロー
  - 例: `scoring_pipeline()`, `data_processing_pipeline()`

## 実装ルール

### ✅ やるべきこと

- **純粋関数**: 副作用のない関数を実装
- **ステートレス**: 状態を持たない設計
- **テスタビリティ**: 単体テストが容易な構造
- **型ヒント**: すべての関数に型ヒントを付与

### ❌ やってはいけないこと

- **I/O操作**: DB接続、API呼び出し、ファイル操作は禁止
- **状態管理**: クラス変数や外部状態への依存は禁止
- **featuresへの依存**: `features/`を直接importしない
- **gatewaysへの依存**: `gateways/`を直接importしない

## 使用例

### entrypoints/scoring.py (公開インターフェース)
```python
from domain_models.domain_a import DomainA
from alg.core.pipelines.scoring_pipeline import execute_scoring_pipeline

def calculate_score(domain: DomainA, threshold: float = 0.5) -> float:
    """
    スコアリング処理の入口

    Args:
        domain: ドメインモデル
        threshold: 閾値

    Returns:
        計算されたスコア
    """
    # Domainモデルからプリミティブな値に変換
    data = {
        "value": domain.value,
        "weight": domain.weight,
    }

    # 内部パイプラインを実行
    return execute_scoring_pipeline(data, threshold)
```

### core/tools/normalize.py
```python
def normalize(value: float, min_val: float, max_val: float) -> float:
    """
    値を0-1の範囲に正規化

    Args:
        value: 正規化する値
        min_val: 最小値
        max_val: 最大値

    Returns:
        正規化された値（0-1）
    """
    if max_val == min_val:
        return 0.0
    return (value - min_val) / (max_val - min_val)
```

### core/pipelines/scoring_pipeline.py
```python
from alg.core.tools.normalize import normalize
from alg.core.tools.weight import apply_weight

def execute_scoring_pipeline(data: dict, threshold: float) -> float:
    """
    スコアリングパイプライン

    Args:
        data: 入力データ
        threshold: 閾値

    Returns:
        最終スコア
    """
    # ステップ1: 正規化
    normalized = normalize(data["value"], 0, 100)

    # ステップ2: 重み付け
    weighted = apply_weight(normalized, data["weight"])

    # ステップ3: 閾値適用
    if weighted < threshold:
        return 0.0

    return weighted
```

## 依存関係

```
features → alg.entrypoints → alg.core

alg.core → domain_models (ドメインモデルの利用は可)

❌ alg → features
❌ alg → gateways
```

## テスト

純粋関数なので、単体テストが容易です:

```python
def test_normalize():
    assert normalize(50, 0, 100) == 0.5
    assert normalize(0, 0, 100) == 0.0
    assert normalize(100, 0, 100) == 1.0
```
