"""DeepSeek provider implementation for Milestone 1 Direct Analyst Baseline."""

from __future__ import annotations

import os
import time
from typing import Any, cast

from openai import OpenAI
from openai.types.chat import ChatCompletion

from ib_eval.baseline.interface import Analyst, CompletionResult, ProviderConfig

_DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_VALID_REASONING_EFFORTS = {"low", "medium", "high"}


class DeepSeekAnalyst(Analyst):
    """Analyst backed by DeepSeek chat completion API."""

    def __init__(
        self,
        config: ProviderConfig,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.config = config

        # Validate thinking & reasoning_effort combination
        if config.reasoning_effort is not None:
            normalized_effort = config.reasoning_effort.lower()
            if normalized_effort not in _VALID_REASONING_EFFORTS:
                msg = (
                    f"Invalid reasoning_effort '{config.reasoning_effort}'. "
                    f"Expected one of: {sorted(_VALID_REASONING_EFFORTS)}."
                )
                raise ValueError(msg)
            if config.thinking is False:
                msg = "Cannot specify reasoning_effort when thinking mode is explicitly disabled."
                raise ValueError(msg)

        effective_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not effective_key:
            msg = (
                "DeepSeek API key not found. Please set the DEEPSEEK_API_KEY environment "
                "variable or pass api_key explicitly."
            )
            raise ValueError(msg)

        effective_base_url = (
            base_url
            or os.environ.get("DEEPSEEK_BASE_URL")
            or _DEFAULT_DEEPSEEK_BASE_URL
        )

        self.client = OpenAI(
            api_key=effective_key,
            base_url=effective_base_url,
            timeout=config.timeout_seconds,
        )

    def complete(self, prompt: str, schema: dict[str, Any] | None = None) -> CompletionResult:
        """Call DeepSeek chat completions API with requested model and prompt."""
        start_time = time.perf_counter()

        system_msg = (
            "You are an expert investment-banking analyst producing structured JSON submissions."
        )
        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_msg,
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        if self.config.temperature is not None:
            kwargs["temperature"] = self.config.temperature

        # Explicit reasoning_effort and thinking configuration
        if self.config.reasoning_effort is not None:
            kwargs["reasoning_effort"] = self.config.reasoning_effort.lower()

        if self.config.thinking is not None:
            extra_body = dict(kwargs.get("extra_body", {}))
            if self.config.thinking:
                extra_body["thinking"] = {"type": "enabled"}
            else:
                extra_body["thinking"] = {"type": "disabled"}
            kwargs["extra_body"] = extra_body

        kwargs.update(self.config.extra_params)

        response = cast(ChatCompletion, self.client.chat.completions.create(**kwargs))
        elapsed = time.perf_counter() - start_time

        # Strictly extract standard content, ignoring any reasoning_content
        raw_text: str = ""
        if response.choices and response.choices[0].message.content:
            raw_text = str(response.choices[0].message.content)

        usage_dict: dict[str, int] | None = None
        if response.usage:
            usage_dict = {
                "prompt_tokens": int(response.usage.prompt_tokens),
                "completion_tokens": int(response.usage.completion_tokens),
                "total_tokens": int(response.usage.total_tokens),
            }

            # Capture DeepSeek cache metadata if provided
            prompt_tokens_details = getattr(response.usage, "prompt_tokens_details", None)
            if prompt_tokens_details is not None:
                cached_tokens = getattr(prompt_tokens_details, "cached_tokens", None)
                if cached_tokens is not None:
                    usage_dict["cached_prompt_tokens"] = int(cached_tokens)

            prompt_cache_hit = getattr(response.usage, "prompt_cache_hit_tokens", None)
            if prompt_cache_hit is not None:
                usage_dict["prompt_cache_hit_tokens"] = int(prompt_cache_hit)

            prompt_cache_miss = getattr(response.usage, "prompt_cache_miss_tokens", None)
            if prompt_cache_miss is not None:
                usage_dict["prompt_cache_miss_tokens"] = int(prompt_cache_miss)

        return CompletionResult(
            raw_response=raw_text,
            latency_seconds=round(elapsed, 3),
            usage=usage_dict,
        )
