"""Centralized path and directory resolution for ib-eval experiments."""

from __future__ import annotations

from pathlib import Path

# Canonical stage subdirectories by case prefix
_CASE_STAGE_MAPPING: dict[str, dict[str, str]] = {
    "northstar": {
        "direct": "milestone-1",
        "structured": "milestone-2",
        "repair": "milestone-3",
        "controlled-repair": "milestone-3b",
        "controlled_repair": "milestone-3b",
    },
    "meridian": {
        "direct": "milestone-4c-direct",
        "structured": "milestone-4d-structured",
        "repair": "milestone-4e-repair",
        "controlled-repair": "milestone-4e-controlled-repair",
        "controlled_repair": "milestone-4e-controlled-repair",
    },
}

_GENERIC_STAGE_MAPPING: dict[str, str] = {
    "direct": "direct",
    "structured": "structured",
    "repair": "repair",
    "controlled-repair": "controlled-repair",
    "controlled_repair": "controlled-repair",
}


def resolve_default_output_dir(case_id: str, mode: str) -> Path:
    """Resolve the canonical default output directory for an experiment.

    Hierarchy: results/<canonical_case_id>/<experiment_stage>/

    Examples:
        resolve_default_output_dir("northstar-v1", "direct")
        -> Path("results/northstar-v1/milestone-1")

        resolve_default_output_dir("meridian-v1", "direct")
        -> Path("results/meridian-v1/milestone-4c-direct")

        resolve_default_output_dir("meridian-v1", "controlled-repair")
        -> Path("results/meridian-v1/milestone-4e-controlled-repair")
    """
    normalized_case = case_id.lower().strip()
    normalized_mode = mode.lower().strip()

    if "northstar" in normalized_case:
        case_key = "northstar"
        canonical_case_dir = "northstar-v1"
    elif "meridian" in normalized_case:
        case_key = "meridian"
        canonical_case_dir = "meridian-v1"
    else:
        case_key = None
        canonical_case_dir = normalized_case

    if case_key is not None:
        stage = _CASE_STAGE_MAPPING[case_key].get(
            normalized_mode,
            _GENERIC_STAGE_MAPPING.get(normalized_mode, normalized_mode),
        )
    else:
        stage = _GENERIC_STAGE_MAPPING.get(normalized_mode, normalized_mode)

    return Path("results") / canonical_case_dir / stage
