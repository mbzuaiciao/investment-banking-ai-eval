"""Milestone 3B Controlled Repair Benchmark package."""

from ib_eval.controlled_repair.analysis import (
    CategoryRepairStat,
    ControlledFixtureTrialResult,
    ControlledRepairBenchmarkSummary,
    DifficultyRepairStat,
    compute_controlled_repair_statistics,
    generate_controlled_repair_markdown_summary,
)
from ib_eval.controlled_repair.fixtures import (
    CONTROLLED_FIXTURES,
    ControlledFixture,
    DifficultyType,
    ErrorCategory,
    resolve_fixtures,
)
from ib_eval.controlled_repair.runner import (
    BenchmarkDriftError,
    ControlledRepairBenchmarkResult,
    run_controlled_repair_benchmark,
)

__all__ = [
    "CONTROLLED_FIXTURES",
    "BenchmarkDriftError",
    "CategoryRepairStat",
    "ControlledFixture",
    "ControlledFixtureTrialResult",
    "ControlledRepairBenchmarkResult",
    "ControlledRepairBenchmarkSummary",
    "DifficultyRepairStat",
    "DifficultyType",
    "ErrorCategory",
    "compute_controlled_repair_statistics",
    "generate_controlled_repair_markdown_summary",
    "resolve_fixtures",
    "run_controlled_repair_benchmark",
]
