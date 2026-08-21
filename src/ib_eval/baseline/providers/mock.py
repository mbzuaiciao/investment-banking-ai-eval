"""Mock analyst provider for offline testing and deterministic evaluation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ib_eval.baseline.interface import Analyst, CompletionResult


class MockAnalyst(Analyst):
    """Mock analyst returning preconfigured responses without network calls."""

    def __init__(
        self,
        responses: str | list[str] | Callable[[str], str] | None = None,
        *,
        simulated_latency: float = 0.05,
        simulated_usage: dict[str, int] | None = None,
    ) -> None:
        self.call_count: int = 0
        self.prompts_received: list[str] = []
        self.simulated_latency: float = simulated_latency
        self.simulated_usage: dict[str, int] = (
            simulated_usage
            if simulated_usage is not None
            else {"prompt_tokens": 1200, "completion_tokens": 800, "total_tokens": 2000}
        )

        if responses is None:
            self._responses: list[str] = ["{}"]
            self._callable: Callable[[str], str] | None = None
        elif callable(responses):
            self._responses = []
            self._callable = responses
        elif isinstance(responses, str):
            self._responses = [responses]
            self._callable = None
        else:
            self._responses = list(responses)
            self._callable = None

    def complete(self, prompt: str, schema: dict[str, Any] | None = None) -> CompletionResult:
        self.call_count += 1
        self.prompts_received.append(prompt)

        if self._callable is not None:
            raw = self._callable(prompt)
        elif self._responses:
            idx = (self.call_count - 1) % len(self._responses)
            raw = self._responses[idx]
        else:
            raw = "{}"

        return CompletionResult(
            raw_response=raw,
            latency_seconds=self.simulated_latency,
            usage=dict(self.simulated_usage),
        )
