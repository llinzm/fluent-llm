from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .prompt_builder import PromptBuilder
from .schema import TDF_JSON_SCHEMA


class LLMClientError(Exception):
    """Raised when the LLM client cannot complete a request."""
    pass


class StructuredJSONError(LLMClientError):
    """Raised when the model response cannot be parsed or validated as TDF JSON."""
    pass


class LLMClient:
    """
    LLM client with:
    - real OpenAI integration
    - structured JSON enforcement
    - retry loop on invalid JSON

    Notes
    -----
    - OpenAI path is implemented using the official Python client and
      chat.completions with `response_format={"type":"json_schema", ...}`.
    - Claude is not implemented yet in this version.
    - The retry loop handles malformed or schema-incomplete JSON by appending
      a corrective instruction and trying again.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: float = 60.0,
    ) -> None:
        self.provider = provider.lower()
        self.model = model or "gpt-5.4-mini"
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.max_retries = max_retries
        self.timeout = timeout
        self.prompt_builder = PromptBuilder()

    def generate_tdf(
        self,
        ifu_text: str,
        capability_hints: Optional[Dict[str, Any]] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        prompt = self.prompt_builder.build(
            ifu_text=ifu_text,
            capability_hints=capability_hints,
            additional_context=additional_context,
        )

        last_error: Optional[Exception] = None
        retry_suffix = ""

        for attempt in range(1, self.max_retries + 1):
            full_prompt = prompt + retry_suffix
            raw_text = self._call_provider(full_prompt)

            try:
                parsed = self._parse_json(raw_text)
                self._validate_tdf(parsed)
                return parsed
            except Exception as exc:
                last_error = exc
                retry_suffix = self._build_retry_suffix(exc, raw_text, attempt)

        raise StructuredJSONError(
            f"Failed to obtain valid structured TDF JSON after {self.max_retries} attempts: {last_error}"
        )

    # --------------------------------------------------
    # Provider dispatch
    # --------------------------------------------------

    def _call_provider(self, prompt: str) -> str:
        if self.provider == "openai":
            return self._call_openai(prompt)

        if self.provider == "claude":
            raise LLMClientError("Claude integration is not implemented in this version.")

        raise LLMClientError(f"Unsupported provider: {self.provider}")

    def _call_openai(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMClientError("OPENAI_API_KEY is missing.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMClientError(
                "The 'openai' package is required for OpenAI integration. Install it with: pip install openai"
            ) from exc

        client = OpenAI(api_key=self.api_key, timeout=self.timeout)

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You output only structured assay JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": TDF_JSON_SCHEMA,
            },
        )

        message = response.choices[0].message
        content = message.content

        if not content:
            raise StructuredJSONError("OpenAI returned empty content.")

        return content

    # --------------------------------------------------
    # Structured JSON handling
    # --------------------------------------------------

    def _parse_json(self, raw_text: str) -> Dict[str, Any]:
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise StructuredJSONError(f"Invalid JSON returned by model: {exc}") from exc

    def _validate_tdf(self, data: Dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise StructuredJSONError("Top-level TDF must be a JSON object.")

        if "steps" not in data:
            raise StructuredJSONError("TDF must contain a top-level 'steps' field.")

        if not isinstance(data["steps"], list):
            raise StructuredJSONError("'steps' must be a list.")

        for idx, step in enumerate(data["steps"]):
            if not isinstance(step, dict):
                raise StructuredJSONError(f"Step at index {idx} must be an object.")
            if "type" not in step:
                raise StructuredJSONError(f"Step at index {idx} is missing 'type'.")
            if "params" not in step:
                raise StructuredJSONError(f"Step at index {idx} is missing 'params'.")
            if not isinstance(step["params"], dict):
                raise StructuredJSONError(f"Step 'params' at index {idx} must be an object.")

    def _build_retry_suffix(self, exc: Exception, raw_text: str, attempt: int) -> str:
        return f"""

Previous attempt {attempt} failed structured JSON validation.

Error:
{exc}

Previous raw response:
{raw_text}

Regenerate the assay strictly as valid JSON matching the required schema.
Do not include markdown, commentary, or code fences.
"""
