"""Case and rubric loader for IB-Eval."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GraderConfig:
    name: str
    weight: float
    tolerances: dict[str, float] = field(default_factory=dict[str, float])
    params: dict[str, Any] = field(default_factory=dict[str, Any])


@dataclass
class Rubric:
    case_id: str
    max_score: float
    graders: list[GraderConfig]
    hard_failure_codes: list[str]

    def grader_by_name(self, name: str) -> GraderConfig | None:
        for g in self.graders:
            if g.name == name:
                return g
        return None

    def total_weight(self) -> float:
        return sum(g.weight for g in self.graders)


@dataclass
class CaseMeta:
    case_id: str
    company: str
    industry: str
    valuation_date: str
    currency: str
    units: str
    description: str


@dataclass
class NorthstarCase:
    meta: CaseMeta
    rubric: Rubric
    case_dir: Path


def load_case(case_dir: Path) -> NorthstarCase:
    """Load case metadata and rubric from a case directory."""
    case_path = case_dir / "case.yaml"
    rubric_path = case_dir / "rubric.yaml"

    with case_path.open() as f:
        case_raw: dict[str, Any] = yaml.safe_load(f) or {}

    with rubric_path.open() as f:
        rubric_raw: dict[str, Any] = yaml.safe_load(f) or {}

    meta = CaseMeta(
        case_id=str(case_raw["case_id"]),
        company=str(case_raw["company"]),
        industry=str(case_raw["industry"]),
        valuation_date=str(case_raw["valuation_date"]),
        currency=str(case_raw.get("currency", "USD")),
        units=str(case_raw.get("units", "millions")),
        description=str(case_raw.get("description", "")),
    )

    graders: list[GraderConfig] = []
    raw_graders: list[dict[str, Any]] = rubric_raw.get("graders", [])
    for g in raw_graders:
        tolerances_raw: dict[str, float] = g.get("tolerances", {})
        params_raw: dict[str, Any] = g.get("params", {})
        graders.append(
            GraderConfig(
                name=str(g["name"]),
                weight=float(g["weight"]),
                tolerances=tolerances_raw,
                params=params_raw,
            )
        )

    rubric = Rubric(
        case_id=str(rubric_raw["case_id"]),
        max_score=float(rubric_raw.get("max_score", 100.0)),
        graders=graders,
        hard_failure_codes=list(rubric_raw.get("hard_failure_codes", [])),
    )

    return NorthstarCase(meta=meta, rubric=rubric, case_dir=case_dir)
