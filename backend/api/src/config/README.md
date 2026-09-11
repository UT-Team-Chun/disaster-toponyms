# config/

設定管理レイヤー。環境変数とYAMLファイルを統合し、アプリケーション全体にTyped Configを提供します。

## 役割

- 環境変数 (`.env`) とYAML設定ファイルの読み込み
- 型安全な設定値の提供
- アプリケーション全体での設定の一元管理

## ディレクトリ構成

```
config/
├── config.py           # 統合された設定クラス（メインエントリーポイント）
├── env_config/         # 環境変数ベースの設定
│   ├── aws_config.py   # AWS関連の環境変数
│   └── llm_config.py   # LLM関連の環境変数
└── yaml_config/        # YAMLファイルベースの設定
    ├── alg_config.py   # アルゴリズム設定（backend/config/alg_config.yaml）
    └── app_config.py   # アプリケーション設定（backend/config/config.yaml）
```

## 実装ルール

### ✅ やるべきこと

- **統合設定の使用**: `config.py`経由で設定値を取得する
- **型定義**: Pydanticを使用して型安全な設定クラスを定義
- **環境変数の優先**: 環境変数がある場合はYAMLよりも優先する

### ❌ やってはいけないこと

- **直接のos.getenv**: アプリケーションコード内で`os.getenv`を直接使用しない
- **設定値のハードコード**: 設定値をコード内に直接記述しない
- **他レイヤーへの依存**: config層は他のレイヤーに依存しない

## 使用例

```python
from config.config import Config

# 設定の取得
config = Config()

# 環境変数ベースの設定
aws_config = config.aws
openai_api_key = config.llm.openai_api_key

# YAMLベースの設定
alg_threshold = config.alg.threshold
app_name = config.app.name
```

## 依存関係

```
他のレイヤー → config
```

- `features/`, `gateways/`, `alg/` から参照される
- 他のレイヤーに依存しない
