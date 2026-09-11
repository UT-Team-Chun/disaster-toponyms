"""Config読み取りテスト - 設定ファイルの読み込みと環境変数の統合を検証.

このスクリプトは以下を検証します:
1. YAMLファイルからの設定読み込み (app, alg)
2. 環境変数からの設定読み込み (LLM, AWS)
3. 統合されたConfigオブジェクトの動作確認
"""

# %%
import traceback

from src.config.config import get_config


# %%
def test_alg_config():
    """アルゴリズム設定の読み込みテスト."""
    config = get_config()

    print("=" * 80)
    print("Algorithm Config (environment variables)")
    print("=" * 80)
    print(f"Input Data Path: {config.alg.input_data}")
    print(f"Output Data Path: {config.alg.output_data}")
    print(f"Model Cache Path: {config.alg.model_cache}")
    print()
    print(f"Embedding Dimensions: {config.alg.embedding_dimensions}")
    print(f"Batch Size: {config.alg.embedding_batch_size}")
    print()
    print(f"Chunk Size: {config.alg.chunk_size}")
    print(f"Chunk Overlap: {config.alg.chunk_overlap}")
    print(f"Max Concurrency: {config.alg.max_concurrency}")
    print()


# %%
def test_env_config():
    """環境変数からの設定読み込みテスト."""
    config = get_config()

    print("=" * 80)
    print("Environment Variable Config")
    print("=" * 80)
    print("LLM Config:")
    print(f"  OpenAI API Key: {'***' if config.llm.openai_api_key else 'Not Set'}")
    print(f"  LLM Provider: {config.llm.llm_provider}")
    print(f"  LLM Model: {config.llm.llm_model}")
    print(f"  Temperature: {config.llm.temperature}")
    print(f"  Max Tokens: {config.llm.max_tokens}")
    print(f"  Embedding Model: {config.llm.embedding_model}")
    print()
    print("AWS Config:")
    print(f"  AWS Access Key ID: {'***' if config.aws.access_key_id else 'Not Set'}")
    print(f"  AWS Secret Access Key: {'***' if config.aws.secret_access_key else 'Not Set'}")
    print(f"  AWS Region: {config.aws.region}")
    print()


# %%
def test_config_as_dict():
    """設定の辞書変換テスト (デバッグ用)."""
    config = get_config()

    print("=" * 80)
    print("Config as Dictionary")
    print("=" * 80)
    print("Algorithm Config:", config.alg.model_dump())
    print()


# %%
def run_practical_example():
    """実用例: 設定を使ってLLMクライアントを初期化する想定."""
    config = get_config()

    print("=" * 80)
    print("Practical Example: LLM Client Configuration")
    print("=" * 80)

    # 環境変数からLLMパラメータを取得
    llm_provider = config.llm.llm_provider
    llm_model = config.llm.llm_model
    temperature = config.llm.temperature
    max_tokens = config.llm.max_tokens

    # 環境変数からAPIキーを取得
    api_key = None
    if llm_provider == "openai":
        api_key = config.llm.openai_api_key

    print(f"Provider: {llm_provider}")
    print(f"Model: {llm_model}")
    print(f"Temperature: {temperature}")
    print(f"Max Tokens: {max_tokens}")
    print(f"API Key: {'Set' if api_key else 'Not Set'}")
    print()

    if api_key:
        print("✅ LLMクライアントを初期化できる状態です")
    else:
        print("⚠️  APIキーが設定されていません (.envrcを確認してください)")
    print()


# %%
def main():
    """メイン実行関数."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Config Loading Verification Test" + " " * 26 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    try:
        # 各テストを実行
        test_alg_config()
        test_env_config()
        test_config_as_dict()
        run_practical_example()

        print("=" * 80)
        print("✅ All config loading tests completed successfully!")
        print("=" * 80)

    except Exception as e:
        print("=" * 80)
        print(f"❌ Error occurred: {e}")
        print("=" * 80)
        traceback.print_exc()


# %%
if __name__ == "__main__":
    main()

# %%
