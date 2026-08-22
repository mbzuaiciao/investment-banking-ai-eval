"""Tests for DeepSeek baseline provider implementation, V4 models, and thinking mode."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ib_eval.baseline.interface import ProviderConfig
from ib_eval.baseline.providers.deepseek import DeepSeekAnalyst
from ib_eval.baseline.runner import run_baseline_experiment
from ib_eval.case import load_case
from ib_eval.cli import main

_CASE_DIR = Path(__file__).parent.parent / "cases" / "northstar-v1"
_GOLD_FILE = Path(__file__).parent.parent / "examples" / "gold_submission" / "submission.json"


def test_deepseek_analyst_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekAnalyst raises ValueError when DEEPSEEK_API_KEY is not set."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config = ProviderConfig(provider="deepseek", model="deepseek-v4-flash")

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekAnalyst(config=config)


def test_deepseek_v4_flash_mocked_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekAnalyst with deepseek-v4-flash makes expected API call and extracts usage."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-mock-key")
    config = ProviderConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
        temperature=0.1,
    )

    with patch("ib_eval.baseline.providers.deepseek.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = '{"analyst": "v4_flash_model"}'

        mock_prompt_details = MagicMock()
        mock_prompt_details.cached_tokens = 500

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 1500
        mock_usage.completion_tokens = 800
        mock_usage.total_tokens = 2300
        mock_usage.prompt_tokens_details = mock_prompt_details
        mock_usage.prompt_cache_hit_tokens = 500
        mock_usage.prompt_cache_miss_tokens = 1000

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response

        analyst = DeepSeekAnalyst(config=config)
        res = analyst.complete("Valuation prompt for Northstar")

        mock_openai_cls.assert_called_once_with(
            api_key="sk-deepseek-mock-key",
            base_url="https://api.deepseek.com",
            timeout=config.timeout_seconds,
        )

        assert res.raw_response == '{"analyst": "v4_flash_model"}'
        assert res.latency_seconds is not None and res.latency_seconds >= 0.0
        assert res.usage == {
            "prompt_tokens": 1500,
            "completion_tokens": 800,
            "total_tokens": 2300,
            "cached_prompt_tokens": 500,
            "prompt_cache_hit_tokens": 500,
            "prompt_cache_miss_tokens": 1000,
        }

        mock_client.chat.completions.create.assert_called_once()
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "deepseek-v4-flash"
        assert kwargs["temperature"] == 0.1
        assert kwargs["response_format"] == {"type": "json_object"}


def test_deepseek_v4_pro_thinking_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekAnalyst with deepseek-v4-pro, thinking=True, and reasoning_effort=high."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    config = ProviderConfig(
        provider="deepseek",
        model="deepseek-v4-pro",
        thinking=True,
        reasoning_effort="high",
    )

    with patch("ib_eval.baseline.providers.deepseek.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = '{"analyst": "v4_pro_thinking"}'
        # Simulate presence of reasoning_content that should NOT be used as raw_response
        mock_choice.message.reasoning_content = "Internal chain of thought step 1 2 3"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_client.chat.completions.create.return_value = mock_response

        analyst = DeepSeekAnalyst(config=config)
        res = analyst.complete("Prompt")

        assert res.raw_response == '{"analyst": "v4_pro_thinking"}'
        assert "Internal chain of thought" not in res.raw_response

        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "deepseek-v4-pro"
        assert kwargs["reasoning_effort"] == "high"
        assert kwargs["extra_body"] == {"thinking": {"type": "enabled"}}


def test_deepseek_thinking_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekAnalyst passes thinking disabled payload when thinking=False."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    config = ProviderConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
        thinking=False,
    )

    with patch("ib_eval.baseline.providers.deepseek.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = '{"analyst": "v4_flash_no_thinking"}'

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_client.chat.completions.create.return_value = mock_response

        analyst = DeepSeekAnalyst(config=config)
        res = analyst.complete("Prompt")

        assert res.raw_response == '{"analyst": "v4_flash_no_thinking"}'
        kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
        assert "reasoning_effort" not in kwargs


def test_deepseek_invalid_thinking_reasoning_combination(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekAnalyst rejects reasoning_effort when thinking is explicitly False."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    config = ProviderConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
        thinking=False,
        reasoning_effort="high",
    )

    with pytest.raises(ValueError, match="Cannot specify reasoning_effort"):
        DeepSeekAnalyst(config=config)


def test_deepseek_invalid_reasoning_effort_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekAnalyst rejects invalid reasoning_effort values."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    config = ProviderConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
        thinking=True,
        reasoning_effort="maximum",  # Invalid
    )

    with pytest.raises(ValueError, match="Invalid reasoning_effort"):
        DeepSeekAnalyst(config=config)


def test_deepseek_custom_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeekAnalyst respects DEEPSEEK_BASE_URL override."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://custom.deepseek.proxy/v1")
    config = ProviderConfig(provider="deepseek", model="deepseek-v4-flash")

    with patch("ib_eval.baseline.providers.deepseek.OpenAI") as mock_openai_cls:
        DeepSeekAnalyst(config=config)
        mock_openai_cls.assert_called_once_with(
            api_key="sk-test",
            base_url="https://custom.deepseek.proxy/v1",
            timeout=config.timeout_seconds,
        )


def test_deepseek_metadata_and_config_persistence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Full baseline experiment persists thinking and reasoning_effort in metadata and config."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test")
    config = ProviderConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
        thinking=True,
        reasoning_effort="high",
    )
    gold_text = _GOLD_FILE.read_text()

    with patch("ib_eval.baseline.providers.deepseek.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = gold_text
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 1000
        mock_usage.completion_tokens = 500
        mock_usage.total_tokens = 1500
        mock_usage.prompt_tokens_details = None
        mock_usage.prompt_cache_hit_tokens = None
        mock_usage.prompt_cache_miss_tokens = None

        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]
        mock_resp.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_resp

        analyst = DeepSeekAnalyst(config=config)
        case = load_case(_CASE_DIR)

        res = run_baseline_experiment(
            case=case,
            analyst_provider=analyst,
            config=config,
            runs=1,
            output_dir=tmp_path,
        )

        assert "thinking-high" in res.experiment_id

        # Verify config.json
        config_path = res.experiment_dir / "config.json"
        assert config_path.exists()
        saved_config = json.loads(config_path.read_text())
        assert saved_config["thinking"] is True
        assert saved_config["reasoning_effort"] == "high"

        # Verify run_001/metadata.json
        meta_path = res.experiment_dir / "run_001" / "metadata.json"
        assert meta_path.exists()
        saved_meta = json.loads(meta_path.read_text())
        assert saved_meta["thinking"] is True
        assert saved_meta["reasoning_effort"] == "high"


def test_cli_baseline_deepseek_dry_run_with_thinking() -> None:
    """CLI baseline with deepseek, thinking on, and reasoning-effort high in dry-run mode."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--thinking",
            "on",
            "--reasoning-effort",
            "high",
            "--runs",
            "3",
        ],
    )

    assert result.exit_code == 0
    assert "DRY-RUN / GUARDRAIL ACTIVE" in result.output
    assert "deepseek" in result.output
    assert "deepseek-v4-flash" in result.output
    assert "Thinking:    on" in result.output
    assert "Reasoning:   high" in result.output
    assert "--thinking on" in result.output
    assert "--reasoning-effort high" in result.output


def test_cli_baseline_deepseek_invalid_thinking_effort() -> None:
    """CLI baseline rejects --reasoning-effort when --thinking is off."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "baseline",
            "--case",
            "northstar-v1",
            "--provider",
            "deepseek",
            "--model",
            "deepseek-v4-flash",
            "--thinking",
            "off",
            "--reasoning-effort",
            "high",
        ],
    )

    assert result.exit_code != 0
    assert "Cannot specify --reasoning-effort when --thinking is set to 'off'" in result.output
