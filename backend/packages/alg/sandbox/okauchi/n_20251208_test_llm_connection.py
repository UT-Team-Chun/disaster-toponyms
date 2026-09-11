"""Test script for gateways.llm connection from sandbox.

This script verifies:
1. LLM configuration can be loaded
2. OpenAI client can be instantiated
3. LLM operations can generate text successfully

This file uses Jupyter-style cell markers (# %%) for interactive execution.
"""

# %%
# Cell 1: Imports
from gateways.llm.config import LLMConfig
from gateways.llm.connections import get_openai_client
from gateways.llm.operations.llm_operations import LLMOperations

# %%
# Cell 2: Test LLM Configuration
print("=== Test 1: LLM Configuration ===")
config = LLMConfig()
print(f"LLM Provider: {config.llm_provider}")
print(f"LLM Model: {config.llm_model}")
print(f"Temperature: {config.temperature}")
print(f"Max Tokens: {config.max_tokens}")
print(f"Embedding Model: {config.embedding_model}")

# Check if API key is available
has_api_key = config.openai_api_key is not None
print(f"API Key Available: {has_api_key}")
print()

# %%
# Cell 3: Test OpenAI Client
print("=== Test 2: OpenAI Client ===")
try:
    client = get_openai_client(config.openai_api_key)
    print(f"OpenAI Client: {type(client).__name__}")
    print("✅ Client instantiated successfully")
except Exception as e:
    print(f"❌ Failed to instantiate client: {e}")
print()

# %%
# Cell 4: Test LLM Operations (Text Generation)
print("=== Test 3: LLM Operations ===")
try:
    # Check if API key is available
    config = LLMConfig()
    if config.openai_api_key is None:
        print("⚠️ openai_api_key not set in config")
        print("Skipping generation test")
        print()
        print("To run this test, set the configuration:")
        print('export OPENAI_API_KEY="your-api-key-here"')
    else:
        # Initialize LLM operations
        llm_ops = LLMOperations(
            api_key=config.openai_api_key,
            model=config.llm_model,
            temperature=config.temperature,
        )

        # Simple test generation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, World!' in Japanese."},
        ]

        print(f"Sending request to {config.llm_model}...")
        response = llm_ops.generate(messages)
        print(f"Response: {response}")
        print("✅ Generation successful")

except Exception as e:
    print(f"❌ Failed to generate: {e}")
    import traceback

    traceback.print_exc()
print()

# %%
# Cell 5: Summary
print("=" * 60)
print("All tests completed")
print("=" * 60)
print()
print("Summary:")
print("- Cell 2: LLM Configuration ✅")
print("- Cell 3: OpenAI Client (depends on API key)")
print("- Cell 4: LLM Operations (depends on API key)")
print()
print("To run with API key:")
print('export OPENAI_API_KEY="sk-..."')
print("Then re-run Cell 3 and Cell 4")

# %%
