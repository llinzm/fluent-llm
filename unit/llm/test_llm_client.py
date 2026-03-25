import pytest

from execution_engine.llm.llm_client import LLMClient, StructuredJSONError, LLMClientError


def test_parse_valid_json():
    client = LLMClient(provider="openai", api_key="dummy")
    parsed = client._parse_json('{"steps":[{"type":"mix","params":{}}]}')

    assert "steps" in parsed
    assert parsed["steps"][0]["type"] == "mix"


def test_validate_tdf_rejects_missing_steps():
    client = LLMClient(provider="openai", api_key="dummy")

    with pytest.raises(StructuredJSONError):
        client._validate_tdf({"assay_id": "x"})


def test_retry_loop_succeeds_after_invalid_json(monkeypatch):
    client = LLMClient(provider="openai", api_key="dummy", max_retries=3)

    calls = {"count": 0}

    def fake_call(prompt):
        calls["count"] += 1
        if calls["count"] == 1:
            return "not-json"
        return '{"steps":[{"type":"incubate","params":{"time_s":600}}]}'

    monkeypatch.setattr(client, "_call_provider", fake_call)

    result = client.generate_tdf("Incubate for 10 minutes")

    assert result["steps"][0]["type"] == "incubate"
    assert calls["count"] == 2


def test_retry_loop_fails_after_max_retries(monkeypatch):
    client = LLMClient(provider="openai", api_key="dummy", max_retries=2)

    monkeypatch.setattr(client, "_call_provider", lambda prompt: "bad-json")

    with pytest.raises(StructuredJSONError):
        client.generate_tdf("Anything")


def test_unsupported_provider_raises():
    client = LLMClient(provider="unsupported", api_key="dummy")

    with pytest.raises(LLMClientError):
        client._call_provider("hello")


def test_claude_placeholder_raises():
    client = LLMClient(provider="claude", api_key="dummy")

    with pytest.raises(LLMClientError):
        client._call_provider("hello")
