"""Tests for baseline provider interfaces and mock/OpenAI implementations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ib_eval.baseline.interface import ProviderConfig
from ib_eval.baseline.providers import MockAnalyst, OpenAIAnalyst


def test_mock_analyst_single_response() -> None:
    """Mock analyst returns fixed response and tracks calls."""
    mock = MockAnalyst('{"test": "val"}', simulated_latency=0.1)
    res = mock.complete("prompt 1")

    assert res.raw_response == '{"test": "val"}'
    assert res.latency_seconds == 0.1
    assert res.usage is not None
    assert mock.call_count == 1
    assert mock.prompts_received == ["prompt 1"]


def test_mock_analyst_multiple_responses_cycling() -> None:
    """Mock analyst cycles through a list of responses."""
    mock = MockAnalyst(["resp1", "resp2"])

    res1 = mock.complete("p1")
    res2 = mock.complete("p2")
    res3 = mock.complete("p3")

    assert res1.raw_response == "resp1"
    assert res2.raw_response == "resp2"
    assert res3.raw_response == "resp1"
    assert mock.call_count == 3


def test_mock_analyst_callable() -> None:
    """Mock analyst accepts a dynamic generator function."""
    mock = MockAnalyst(lambda p: f"echo: {p}")
    res = mock.complete("hello")
    assert res.raw_response == "echo: hello"


def test_openai_analyst_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenAIAnalyst raises ValueError when no API key is available in environment."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = ProviderConfig(provider="openai", model="gpt-4o")

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIAnalyst(config=config)


def test_openai_analyst_mocked_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenAIAnalyst makes expected API call and extracts latency and usage."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-mock-key")
    config = ProviderConfig(
        provider="openai",
        model="gpt-4o",
        temperature=0.2,
        seed=42,
    )

    with patch("ib_eval.baseline.providers.openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = '{"analyst": "test"}'

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50
        mock_usage.total_tokens = 150

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response

        analyst = OpenAIAnalyst(config=config)
        res = analyst.complete("Test prompt")

        assert res.raw_response == '{"analyst": "test"}'
        assert res.latency_seconds is not None and res.latency_seconds >= 0.0
        assert res.usage == {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

        mock_client.chat.completions.create.assert_called_once()
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "gpt-4o"
        assert kwargs["temperature"] == 0.2
        assert kwargs["seed"] == 42
        assert kwargs["response_format"] == {"type": "json_object"}
