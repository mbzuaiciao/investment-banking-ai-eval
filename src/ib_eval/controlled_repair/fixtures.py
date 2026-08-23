"""Controlled repair benchmark fixture definitions and loader."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from ib_eval.schemas import Submission


class ErrorCategory(StrEnum):
    """Broad error categories for grouping financial failure modes."""

    SOURCE_FIDELITY = "source_fidelity"
    VALUATION = "valuation"
    ACCOUNTING_BRIDGE = "accounting_bridge"
    COMPS = "comps"
    ARITHMETIC = "arithmetic"
    FORMULA = "formula"
    CONSISTENCY = "consistency"


class DifficultyType(StrEnum):
    """Repair difficulty classification based on dependency propagation."""

    LOCAL = "local"
    PROPAGATING = "propagating"


@dataclass(frozen=True)
class ControlledFixture:
    """Metadata and definition of a controlled corrupted benchmark fixture."""

    fixture_id: str  # e.g. "c01"
    dir_name: str  # e.g. "c01_quarterly_revenue"
    name: str  # e.g. "Quarterly revenue confusion"
    expected_diagnostic: str  # e.g. "REV_QUARTERLY_CONFUSION"
    category: ErrorCategory
    difficulty: DifficultyType
    description: str

    def load_submission(self, corrupted_dir: Path) -> Submission:
        """Load and validate the initial corrupted Submission object."""
        fixture_path = corrupted_dir / self.dir_name / "submission.json"
        if not fixture_path.exists():
            raise FileNotFoundError(f"Corrupted fixture submission not found: {fixture_path}")
        return Submission.model_validate_json(fixture_path.read_text())


# Canonical list of the 10 Milestone 0 corrupted fixtures
CONTROLLED_FIXTURES: list[ControlledFixture] = [
    ControlledFixture(
        fixture_id="c01",
        dir_name="c01_quarterly_revenue",
        name="Quarterly Revenue Confusion",
        expected_diagnostic="REV_QUARTERLY_CONFUSION",
        category=ErrorCategory.VALUATION,
        difficulty=DifficultyType.PROPAGATING,
        description="Uses Q2 quarterly revenue (281.0) instead of full-year 2025A base (1000.0).",
    ),
    ControlledFixture(
        fixture_id="c02",
        dir_name="c02_tv_not_discounted",
        name="Terminal Value Not Discounted",
        expected_diagnostic="TV_NOT_DISCOUNTED",
        category=ErrorCategory.VALUATION,
        difficulty=DifficultyType.PROPAGATING,
        description=(
            "Adds undiscounted horizon TV directly to Enterprise Value without discounting."
        ),
    ),
    ControlledFixture(
        fixture_id="c03",
        dir_name="c03_cash_subtracted",
        name="Cash Subtracted in Bridge",
        expected_diagnostic="EQ_BRIDGE_CASH_REVERSED",
        category=ErrorCategory.ACCOUNTING_BRIDGE,
        difficulty=DifficultyType.PROPAGATING,
        description="Subtracts cash from gross debt (adding to net debt) in equity bridge.",
    ),
    ControlledFixture(
        fixture_id="c04",
        dir_name="c04_debt_omitted",
        name="Debt Omitted from Bridge",
        expected_diagnostic="EQ_BRIDGE_DEBT_OMITTED",
        category=ErrorCategory.ACCOUNTING_BRIDGE,
        difficulty=DifficultyType.PROPAGATING,
        description="Omits net debt deduction, equating Enterprise Value directly to Equity Value.",
    ),
    ControlledFixture(
        fixture_id="c05",
        dir_name="c05_nm_peer_zero",
        name="N/M Peer Multiple Coerced to Zero",
        expected_diagnostic="COMPS_NM_COERCED_ZERO",
        category=ErrorCategory.COMPS,
        difficulty=DifficultyType.LOCAL,
        description=(
            "Coerces negative EBITDA peer multiple to 0.0x instead of excluding from median."
        ),
    ),
    ControlledFixture(
        fixture_id="c06",
        dir_name="c06_fabricated_guidance",
        name="Fabricated Explicit Guidance",
        expected_diagnostic="SF_GUIDANCE_FABRICATED",
        category=ErrorCategory.SOURCE_FIDELITY,
        difficulty=DifficultyType.LOCAL,
        description="Classifies analyst revenue growth assumption as direct management guidance.",
    ),
    ControlledFixture(
        fixture_id="c07",
        dir_name="c07_ebitda_inconsistency",
        name="EBITDA / D&A / EBIT Inconsistency",
        expected_diagnostic="MARGIN_EBIT_INCONSISTENCY",
        category=ErrorCategory.ARITHMETIC,
        difficulty=DifficultyType.PROPAGATING,
        description="EBIT forecast does not equal EBITDA minus D&A across forecast periods.",
    ),
    ControlledFixture(
        fixture_id="c08",
        dir_name="c08_capex_double_counted",
        name="Capex Double Counted",
        expected_diagnostic="FCF_CAPEX_DOUBLE_COUNTED",
        category=ErrorCategory.FORMULA,
        difficulty=DifficultyType.PROPAGATING,
        description="Capex subtracted twice in the Unlevered Free Cash Flow forecast schedule.",
    ),
    ControlledFixture(
        fixture_id="c09",
        dir_name="c09_headline_mismatch",
        name="Headline / Schedule Mismatch",
        expected_diagnostic="CONSISTENCY_HEADLINE_DCF",
        category=ErrorCategory.CONSISTENCY,
        difficulty=DifficultyType.LOCAL,
        description=(
            "Headline DCF valuation outputs do not match underlying detailed DCF schedules."
        ),
    ),
    ControlledFixture(
        fixture_id="c10",
        dir_name="c10_pretax_wacc",
        name="Pre-Tax Cost of Debt in WACC",
        expected_diagnostic="WACC_PRETAX_DEBT",
        category=ErrorCategory.FORMULA,
        difficulty=DifficultyType.PROPAGATING,
        description=(
            "Uses pre-tax cost of debt in WACC without applying corporate interest tax shield."
        ),
    ),
]


def resolve_fixtures(selector: str, corrupted_dir: Path) -> list[ControlledFixture]:
    """Resolve fixture selector ('all' or comma-separated IDs/names) to ControlledFixtures."""
    cleaned = selector.strip()
    if cleaned.lower() == "all":
        return list(CONTROLLED_FIXTURES)

    tokens = [t.strip().lower() for t in cleaned.split(",") if t.strip()]
    if not tokens:
        return list(CONTROLLED_FIXTURES)

    resolved: list[ControlledFixture] = []
    available_map: dict[str, ControlledFixture] = {}
    for f in CONTROLLED_FIXTURES:
        available_map[f.fixture_id.lower()] = f
        available_map[f.dir_name.lower()] = f

    for token in tokens:
        if token in available_map:
            resolved.append(available_map[token])
        else:
            valid_keys = sorted(set(list(available_map.keys())))
            raise ValueError(
                f"Unknown fixture identifier: '{token}'. "
                f"Valid options include 'all' or specific IDs: {', '.join(valid_keys)}"
            )

    return resolved
