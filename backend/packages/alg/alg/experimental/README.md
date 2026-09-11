# experimental/

検証段階のインターフェース層。sandbox から呼び出して検証するための関数を配置します。

## 📋 概要

`experimental/` は、`entrypoints/` と同じレイヤーに位置し、`core/` の複数モジュールを統合して提供する検証用のインターフェースです。

### 位置づけ

```
sandbox/
  ↓ (検証段階)
experimental/  ← core/の複数モジュールを統合
  ↓ (検証完了後)
entrypoints/   ← core/の複数モジュールを統合
  ↓
SW (features/)
```

### 3層構造

```
sandbox/ → experimental/ → entrypoints/
              ↓              ↓
            core/ (共通の内部ロジック部品)
```

## 🎯 役割

- **core/の複数モジュールを統合**: 単一の関数として提供
- **sandboxから利用可能**: `from alg.experimental.xxx import yyy` でimport
- **entrypointsの前段階**: 検証が完了したら `entrypoints/` に昇格
- **entrypointsと同様の実装スタイル**: core/を組み合わせるFacadeパターン

## 📁 ファイル配置

```
experimental/
├── README.md                    # このファイル
├── __init__.py
└── {function_name}.py           # 検証用関数（1ファイル = 1機能）
```

**例**:
```
experimental/
├── README.md
├── __init__.py
├── test_calculator.py           # 計算機能の検証
└── test_data_processor.py       # データ処理機能の検証
```

## 🔧 実装パターン

### 基本パターン: core/の複数モジュールを統合

```python
# experimental/test_calculator.py
"""Calculator feature for testing (experimental)."""

from alg.core.calculation.tools.basic_math import add, multiply
from alg.core.formatting.tools.text_formatter import format_result


def calculate_and_format(a: int, b: int, operation: str) -> str:
    """Calculate and format the result (experimental).

    Args:
        a: First operand
        b: Second operand
        operation: Operation type ("add" or "multiply")

    Returns:
        Formatted result string

    """
    # core/の複数モジュールを統合
    if operation == "add":
        result = add(a, b)
    elif operation == "multiply":
        result = multiply(a, b)
    else:
        raise ValueError(f"Unknown operation: {operation}")

    return format_result(result)
```

### gatewaysを利用するパターン

```python
# experimental/test_llm_processor.py
"""LLM-based text processor (experimental)."""

from alg.core.text.tools.preprocessor import clean_text
from alg.core.text.tools.postprocessor import format_output
from gateways.llm.connections import get_openai_client
from gateways.llm.operations.llm_operations import LLMOperations


def process_text_with_llm(input_text: str, api_key: str) -> str:
    """Process text using LLM (experimental).

    Args:
        input_text: Input text to process
        api_key: OpenAI API key

    Returns:
        Processed text

    """
    # core/で前処理
    cleaned = clean_text(input_text)

    # gateways.llmでLLM呼び出し
    llm_ops = LLMOperations(api_key=api_key)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": cleaned},
    ]
    llm_result = llm_ops.generate(messages)

    # core/で後処理
    return format_output(llm_result)
```

## 📝 sandboxから利用する

### 使用例

```python
# sandbox/okauchi/s_20251208_test_calculator.py
"""Test experimental calculator function."""

from alg.experimental.test_calculator import calculate_and_format

# experimentalを使って検証
result = calculate_and_format(10, 20, "add")
print(result)  # "Result: 30"

result = calculate_and_format(5, 6, "multiply")
print(result)  # "Result: 30"
```

### 実行方法

```bash
cd backend/packages/alg
uv run python sandbox/okauchi/s_20251208_test_calculator.py
```

## 🚀 entrypointsへの昇格フロー

検証が完了し、本番環境で使用する準備ができたら、`entrypoints/` に昇格させます。

### ステップ1: experimental/で実装・検証

```python
# experimental/test_calculator.py
def calculate_and_format(a: int, b: int, operation: str) -> str:
    """Calculate and format (experimental)."""
    # 実装
    pass
```

### ステップ2: sandboxで動作確認

```python
# sandbox/okauchi/s_20251208_test_calculator.py
from alg.experimental.test_calculator import calculate_and_format

# 動作確認
result = calculate_and_format(10, 20, "add")
assert result == "Result: 30"
```

### ステップ3: entrypointsに昇格

```python
# entrypoints/calculator.py
def execute_calculation(a: int, b: int, operation: str) -> str:
    """Calculate and format (production)."""
    # experimental/から実装をコピー・リファクタリング
    pass
```

### ステップ4: experimental/を削除またはアーカイブ

```bash
# 削除する場合
rm experimental/test_calculator.py

# または、アーカイブする場合
git mv experimental/test_calculator.py experimental/_archived/test_calculator.py
```

## ⚠️ 注意事項

### DO: やるべきこと

- ✅ core/の複数モジュールを統合する
- ✅ entrypointsと同様の実装スタイルを採用
- ✅ sandboxから呼び出して十分に検証する
- ✅ 検証完了後はentrypointsに昇格させる
- ✅ 関数名はわかりやすく、目的を明確にする

### DON'T: やってはいけないこと

- ❌ experimental/をSW（features/）から直接呼び出す
- ❌ experimental/に複雑なビジネスロジックを直接実装する（core/に分割すべき）
- ❌ 検証が完了したexperimental/をそのまま放置する
- ❌ experimental/からexperimental/を呼び出す（flat構造を維持）

## 📊 依存関係

```
experimental/
  ↓ import OK
core/*
gateways.*

experimental/
  ↓ import NG
features/
entrypoints/
experimental/ (自己参照)
```

## 🔄 ライフサイクル

1. **sandbox/** - 検証スクリプト（モジュール化前）
2. **experimental/** - 検証用インターフェース（core/を統合）← **ここ**
3. **entrypoints/** - 本番用インターフェース（core/を統合）
4. **features/** - SWから呼び出される

## 📚 関連ドキュメント

- [docs/architecture.md](../../../../docs/architecture.md) - アーキテクチャ詳細

## 💡 Tips

### entrypointsとの違い

| 項目 | experimental/ | entrypoints/ |
|------|--------------|--------------|
| **目的** | 検証段階の機能 | 本番環境の確定機能 |
| **呼び出し元** | sandbox/ | features/ (SW) |
| **安定性** | 不安定・変更可能性大 | 安定・変更は慎重に |
| **テスト** | sandboxで検証中 | 本番環境で使用中 |

### 命名規則

```python
# experimental/
test_xxx.py         # テスト中の機能
draft_xxx.py        # ドラフト版
experimental_xxx.py # 実験的実装

# entrypoints/への昇格時
test_calculator.py → calculator.py
draft_processor.py → processor.py
experimental_analyzer.py → analyzer.py
```

### デバッグ時のヒント

```python
# experimental/では詳細なログを出力してOK
def calculate_and_format(a: int, b: int) -> str:
    print(f"DEBUG: Input: a={a}, b={b}")  # OK in experimental/
    result = add(a, b)
    print(f"DEBUG: Result: {result}")      # OK in experimental/
    return format_result(result)

# entrypoints/ではログを整理
def execute_calculation(a: int, b: int) -> str:
    # print文は削除、必要ならloggerを使用
    result = add(a, b)
    return format_result(result)
```
