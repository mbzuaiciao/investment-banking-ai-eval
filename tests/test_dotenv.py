"""Unit tests for automatic .env loading and environment precedence."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

from ib_eval.baseline.interface import ProviderConfig
from ib_eval.baseline.providers.deepseek import DeepSeekAnalyst
from ib_eval.baseline.providers.openai import OpenAIAnalyst


def test_dotenv_loads_unset_variable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that load_dotenv loads a variable from .env when not already set in environment."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_IB_EVAL_KEY=secret_from_env_file\n")

    monkeypatch.delenv("TEST_IB_EVAL_KEY", raising=False)
    assert os.environ.get("TEST_IB_EVAL_KEY") is None

    # Load from the custom .env path without override
    loaded = load_dotenv(dotenv_path=env_file, override=False)
    assert loaded is True
    assert os.environ.get("TEST_IB_EVAL_KEY") == "secret_from_env_file"


def test_dotenv_preserves_already_exported_variable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that load_dotenv does NOT overwrite an existing shell environment variable."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_IB_EVAL_PREEXISTING=from_env_file\n")

    # Set pre-existing shell environment variable
    monkeypatch.setenv("TEST_IB_EVAL_PREEXISTING", "from_shell_environment")

    load_dotenv(dotenv_path=env_file, override=False)
    assert os.environ.get("TEST_IB_EVAL_PREEXISTING") == "from_shell_environment"


def test_deepseek_provider_key_lookup_with_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that DeepSeekAnalyst uses key loaded from .env when not passed explicitly."""
    env_file = tmp_path / ".env"
    env_file.write_text("DEEPSEEK_API_KEY=ds_mock_key_from_env\n")

    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    load_dotenv(dotenv_path=env_file, override=False)

    config = ProviderConfig(provider="deepseek", model="deepseek-v4-flash")
    with patch("ib_eval.baseline.providers.deepseek.OpenAI") as mock_openai:
        analyst = DeepSeekAnalyst(config=config)
        assert analyst is not None
        mock_openai.assert_called_once()
        _, kwargs = mock_openai.call_args
        assert kwargs["api_key"] == "ds_mock_key_from_env"


def test_openai_provider_key_lookup_with_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that OpenAIAnalyst uses key loaded from .env when not passed explicitly."""
    env_file = tmp_path / ".env"
    env_file.write_text("OPENAI_API_KEY=oa_mock_key_from_env\n")

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    load_dotenv(dotenv_path=env_file, override=False)

    config = ProviderConfig(provider="openai", model="gpt-4o")
    with patch("ib_eval.baseline.providers.openai.OpenAI") as mock_openai:
        analyst = OpenAIAnalyst(config=config)
        assert analyst is not None
        mock_openai.assert_called_once()
        _, kwargs = mock_openai.call_args
        assert kwargs["api_key"] == "oa_mock_key_from_env"


def test_provider_key_lookup_missing_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing API keys continue to raise ValueError with a helpful message."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    config = ProviderConfig(provider="deepseek", model="deepseek-v4-flash")
    with pytest.raises(ValueError, match="DeepSeek API key not found"):
        DeepSeekAnalyst(config=config)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    oa_config = ProviderConfig(provider="openai", model="gpt-4o")
    with pytest.raises(ValueError, match="OpenAI API key not found"):
        OpenAIAnalyst(config=oa_config)
