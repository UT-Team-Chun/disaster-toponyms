# API Tests

このディレクトリには、APIレイヤーの統合テストが含まれています。

## テストファイル

### [test_dependency.py](./test_dependency.py)

パッケージ間の依存関係が正しく設定されているかを検証するテスト。

#### テスト内容

1. **`test_alg_import()`**
   - API → alg の依存関係をテスト
   - `from alg.entrypoints...` のimportパターンを検証
   - 実際に関数を呼び出して動作確認

2. **`test_gateways_import()`**
   - API → gateways の依存関係をテスト
   - `from gateways.llm...` のimportパターンを検証
   - 関数とクラスが正しくimportできることを確認

3. **`test_alg_to_gateways()`**
   - alg → gateways の依存関係をテスト
   - algパッケージ内部からgatewaysを呼び出せることを確認

## テストの実行

### すべてのテストを実行
```bash
cd backend/api
uv run pytest tests/api/ -v
```

### 特定のテストファイルのみ実行
```bash
cd backend/api
uv run pytest tests/api/test_dependency.py -v
```

### 特定のテスト関数のみ実行
```bash
cd backend/api
uv run pytest tests/api/test_dependency.py::test_alg_import -v
```

## テスト結果の確認

すべてのテストが成功すると、以下のような出力が表示されます:

```
tests/api/test_dependency.py::test_alg_import PASSED
tests/api/test_dependency.py::test_gateways_import PASSED
tests/api/test_dependency.py::test_alg_to_gateways PASSED

============================== 3 passed in 0.25s ===============================
```

## 検証されるimportパターン

### API側 (test_dependency.py)
```python
# ✅ API → alg (正しいパターン)
from alg.entrypoints.sample_entrypoint import (
    calculate_with_description,
    check_llm_connection_available,
)

# ✅ API → gateways (正しいパターン)
from gateways.llm.connections import get_openai_client
from gateways.llm.operations.llm_operations import LLMOperations
```

## 関連ファイル

- [backend/packages/alg/tests/](../../../packages/alg/tests/) - algパッケージのユニットテスト
- [backend/packages/gateways/tests/](../../../packages/gateways/tests/) - gatewaysパッケージのユニットテスト

## トラブルシューティング

### Import Error が出る場合

テストが失敗する場合は、以下を確認してください:

1. 依存関係が正しくインストールされているか:
   ```bash
   cd backend/api
   uv sync
   ```

2. パッケージが正しくビルドされているか:
   ```bash
   cd backend/packages/alg
   uv sync
   cd ../gateways
   uv sync
   ```

3. pyproject.tomlの設定が正しいか確認
   - algとgatewaysのパッケージ設定
   - workspace設定
