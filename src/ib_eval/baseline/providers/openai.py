"""OpenAI provider implementation for Milestone 1 Direct Analyst Baseline."""

from __future__ import annotations

import os
import time
from typing import Any, cast

from openai import OpenAI
from openai.types.chat import ChatCompletion

from ib_eval.baseline.interface import Analyst, CompletionResult, ProviderConfig


class OpenAIAnalyst(Analyst):
    """Analyst backed by OpenAI chat completion."""

    def __init__(
        self,
        config: ProviderConfig,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.config = config
        effective_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not effective_key:
            msg = (
                "OpenAI API key not found. Please set the OPENAI_API_KEY environment "
                "variable or pass api_key explicitly."
            )
            raise ValueError(msg)

        self.client = OpenAI(
            api_key=effective_key,
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
            timeout=config.timeout_seconds,
        )

    def complete(self, prompt: str, schema: dict[str, Any] | None = None) -> CompletionResult:
        """Call OpenAI chat completions API with requested model and prompt."""
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
        if self.config.seed is not None:
            kwargs["seed"] = self.config.seed

        kwargs.update(self.config.extra_params)

        response = cast(ChatCompletion, self.client.chat.completions.create(**kwargs))
        elapsed = time.perf_counter() - start_time

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

        return CompletionResult(
            raw_response=raw_text,
            latency_seconds=round(elapsed, 3),
            usage=usage_dict,
        )
