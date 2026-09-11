"""LLM operations for text generation and completions."""

from __future__ import annotations

import json
from typing import Any

from openai.types.chat import ChatCompletionMessageParam

from gateways.llm.connections import get_openai_client


class LLMOperations:
    """High-level LLM operations using OpenAI client."""

    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.7) -> None:
        """Initialize LLM operations with OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Default model name
            temperature: Default temperature

        """
        self._client = get_openai_client(api_key=api_key)
        self._default_model = model
        self._default_temperature = temperature

    # VLM版とかも追加したい。
    def generate(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
    ) -> str:
        """Generate completion using OpenAI's chat API.

        Args:
            messages: List of chat messages for the completion.
            model: Model name to use. If None, uses the default model.
            temperature: Temperature to use. If None, uses the default temperature.

        Returns:
            Generated completion text.

        """
        completion = self._client.chat.completions.create(
            model=model or self._default_model,
            messages=messages,
            temperature=temperature or self._default_temperature,
        )
        return completion.choices[0].message.content or ""

    def generate_json(
        self,
        messages: list[ChatCompletionMessageParam],
        schema: dict[str, Any],
        *,
        schema_name: str = "extraction",
        model: str | None = None,
    ) -> dict[str, Any]:
        """Generate a response constrained to a JSON schema.

        Args:
            messages: Chat messages describing the extraction task.
            schema: JSON Schema the answer must satisfy. Must be an object schema
                with ``additionalProperties`` set to false for strict mode.
            schema_name: Name reported to the API for the schema.
            model: Model name to use. If None, uses the default model.

        Returns:
            The parsed JSON object returned by the model.

        Raises:
            ValueError: If the model returns no content or invalid JSON.

        """
        completion = self._client.chat.completions.create(
            model=model or self._default_model,
            messages=messages,
            response_format={
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema, "strict": True},
            },
        )
        content = completion.choices[0].message.content
        if not content:
            msg = "LLM returned an empty response for a structured request"
            raise ValueError(msg)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as error:
            msg = f"LLM returned invalid JSON: {error}"
            raise ValueError(msg) from error
        if not isinstance(parsed, dict):
            msg = "LLM returned a non-object JSON payload"
            raise TypeError(msg)
        return parsed
