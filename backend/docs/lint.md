# Backend Lint エラー対処方法

## T201: `print` found

**エラー内容**:
```
T201 `print` found
```

**原因**:
コード内で`print()`関数を使用している。本番環境では適切なロギングを使用すべき。

**対処方法**:
`print()`の代わりに`loguru`の`logger.debug()`を使用してください。

**修正例**:
```python
# ❌ 悪い例
print(f"User ID: {user_id}")
print("Processing started")

# ✅ 良い例
from loguru import logger

logger.debug(f"User ID: {user_id}")
logger.debug("Processing started")
```

**ログレベルの使い分け**:
- `logger.debug()`: デバッグ情報（開発時のみ）
- `logger.info()`: 一般的な情報
- `logger.warning()`: 警告
- `logger.error()`: エラー
- `logger.critical()`: 致命的なエラー

---

## B904: Within an `except` clause, raise exceptions with `raise ... from err`

**エラー内容**:
```
B904 Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling
```

**原因**:
`except`ブロック内で例外を再発生させる際に、元の例外とのチェーンが明示されていない。

**対処方法**:
`raise ... from e`または`raise ... from None`を使用して、例外チェーンを明示してください。

**修正例**:
```python
# ❌ 悪い例
try:
    config_dict = yaml.safe_load(file)
    return cls(**config_dict)
except Exception as e:
    raise RuntimeError(f"Failed to load config: {e}")

# ✅ 良い例1: 元の例外を保持する場合
try:
    config_dict = yaml.safe_load(file)
    return cls(**config_dict)
except Exception as e:
    raise RuntimeError(f"Failed to load config: {e}") from e

# ✅ 良い例2: 元の例外を隠す場合
try:
    config_dict = yaml.safe_load(file)
    return cls(**config_dict)
except Exception as e:
    raise RuntimeError(f"Failed to load config: {e}") from None
```

**使い分け**:
- `from e`: 元の例外情報を保持したい場合（通常はこちらを推奨）
- `from None`: 元の例外を隠したい場合（セキュリティ上の理由など）
