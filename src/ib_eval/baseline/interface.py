"""Interface definitions for Milestone 1 Direct Analyst Baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ib_eval.schemas import ScoringReport, Submission


@dataclass
class CompletionResult:
    """Raw output and metadata from a single model completion."""

    raw_response: str
    latency_seconds: float | None = None
    usage: dict[str, int] | None = None


class Analyst(Protocol):
    """Protocol for an analyst completion provider."""

    def complete(self, prompt: str, schema: dict[str, Any] | None = None) -> CompletionResult:
        """Submit a single prompt to the underlying model and return completion."""
        ...


@dataclass
class ProviderConfig:
    """Configuration for an analyst model provider."""

    provider: str
    model: str
    mode: str = "direct"
    temperature: float | None = None
    seed: int | None = None
    timeout_seconds: float = 180.0
    thinking: bool | None = None
    reasoning_effort: str | None = None
    extra_params: dict[str, Any] = field(default_factory=dict[str, Any])


@dataclass
class TrialMetadata:
    """Metadata recorded for a single experiment trial."""

    run_index: int
    provider: str
    model: str
    timestamp: str
    mode: str = "direct"
    temperature: float | None = None
    seed: int | None = None
    thinking: bool | None = None
    reasoning_effort: str | None = None
    latency_seconds: float | None = None
    token_usage: dict[str, int] | None = None
    parsed_successfully: bool = False
    score: float | None = None
    hard_failure_count: int = 0
    hard_failure_codes: list[str] = field(default_factory=list[str])
    git_commit: str | None = None


@dataclass
class TrialResult:
    """Full outcome of a single trial."""

    metadata: TrialMetadata
    raw_response: str
    submission: Submission | None = None
    parse_error: str | None = None
    grade: ScoringReport | None = None
