"""Pydantic schemas for the IB-Eval submission format and grader results."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class ProvenanceClassification(StrEnum):
    """How was the value sourced?"""

    DIRECT = "direct"
    DERIVED = "derived"
    ANALYST_ASSUMPTION = "analyst_assumption"


class ErrorType(StrEnum):
    ARITHMETIC = "arithmetic_error"
    FORMULA = "formula_error"
    ACCOUNTING = "accounting_inconsistency"
    VALUATION = "valuation_error"
    PROVENANCE = "source_provenance_error"
    UNSUPPORTED = "unsupported_assumption"
    CROSS_ARTIFACT = "cross_artifact_inconsistency"


class Severity(StrEnum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


class ProvenanceRecord(BaseModel):
    """One unit of evidence tracing a model input to its source."""

    metric: str
    period: str
    value: float
    source: str
    classification: ProvenanceClassification
    confidence: Annotated[float, Field(ge=0.0, le=1.0)] = 1.0
    note: str = ""


# ---------------------------------------------------------------------------
# Historical / forecast building blocks
# ---------------------------------------------------------------------------


class HistoricalYear(BaseModel):
    year: int
    revenue: float
    ebitda: float
    ebitda_margin: float
    da: float
    ebit: float
    capex: float
    nwc: float


class ForecastYear(BaseModel):
    year: int
    revenue: float
    revenue_growth: float
    ebitda_margin: float
    ebitda: float
    da: float
    ebit: float
    nopat: float
    capex: float
    nwc: float
    delta_nwc: float
    ufcf: float
    discount_factor: float
    pv_ufcf: float


# ---------------------------------------------------------------------------
# WACC
# ---------------------------------------------------------------------------


class WACCInputs(BaseModel):
    risk_free_rate: float
    equity_risk_premium: float
    beta: float
    pre_tax_cost_of_debt: float
    tax_rate: float
    equity_weight: float
    debt_weight: float

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> WACCInputs:
        total = round(self.equity_weight + self.debt_weight, 6)
        if abs(total - 1.0) > 1e-4:
            msg = f"equity_weight + debt_weight must equal 1.0, got {total}"
            raise ValueError(msg)
        return self


class WACCOutputs(BaseModel):
    cost_of_equity: float
    after_tax_cost_of_debt: float
    wacc: float


# ---------------------------------------------------------------------------
# Terminal value
# ---------------------------------------------------------------------------


class TerminalValueInputs(BaseModel):
    terminal_growth_rate: float
    method: str = "perpetual_growth"


class TerminalValueOutputs(BaseModel):
    terminal_fcf: float
    terminal_value_at_horizon: float  # TV at end of final forecast year
    pv_terminal_value: float  # PV of TV as of valuation date


# ---------------------------------------------------------------------------
# DCF outputs
# ---------------------------------------------------------------------------


class DCFOutputs(BaseModel):
    sum_pv_ufcf: float
    pv_terminal_value: float
    enterprise_value: float  # sum_pv_ufcf + pv_terminal_value


# ---------------------------------------------------------------------------
# Capital structure
# ---------------------------------------------------------------------------


class ConvertibleTreatment(StrEnum):
    DEBT = "debt"
    EQUITY = "equity"
    TREASURY_STOCK = "treasury_stock"


class CapitalStructure(BaseModel):
    gross_debt: float
    cash: float
    net_debt: float
    diluted_shares: float
    current_share_price: float
    convertible_face_value: float
    convertible_treatment: ConvertibleTreatment
    note_convertible: str = ""

    @model_validator(mode="after")
    def net_debt_reconciles(self) -> CapitalStructure:
        expected = round(self.gross_debt - self.cash, 4)
        if abs(expected - self.net_debt) > 0.01:
            msg = f"net_debt mismatch: gross_debt-cash={expected}, net_debt={self.net_debt}"
            raise ValueError(msg)
        return self


# ---------------------------------------------------------------------------
# Equity bridge
# ---------------------------------------------------------------------------


class EquityBridge(BaseModel):
    enterprise_value: float
    minus_net_debt: float
    equity_value: float
    diluted_shares: float
    implied_share_price: float

    @model_validator(mode="after")
    def equity_value_reconciles(self) -> EquityBridge:
        expected = round(self.enterprise_value - self.minus_net_debt, 4)
        if abs(expected - self.equity_value) > 0.1:
            msg = f"equity_value mismatch: EV-net_debt={expected}, equity_value={self.equity_value}"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def share_price_reconciles(self) -> EquityBridge:
        if self.diluted_shares <= 0:
            msg = "diluted_shares must be positive"
            raise ValueError(msg)
        expected = round(self.equity_value / self.diluted_shares, 6)
        if abs(expected - self.implied_share_price) > 0.01:
            msg = (
                f"implied_share_price mismatch: equity/shares={expected:.4f}, "
                f"stated={self.implied_share_price}"
            )
            raise ValueError(msg)
        return self


# ---------------------------------------------------------------------------
# Comparable companies
# ---------------------------------------------------------------------------


class CompsPeer(BaseModel):
    name: str
    ltm_ev_ebitda: float | None  # None = N/M
    ntm_ev_ebitda: float | None  # None = N/M
    excluded: bool = False
    exclusion_reason: str = ""


class CompsInputs(BaseModel):
    peers: list[CompsPeer]
    applied_multiple: float
    applied_ebitda: float | None = None
    applied_metric: str | None = None
    applied_metric_value: float | None = None
    multiple_type: str | None = None


class CompsOutputs(BaseModel):
    ltm_median: float | None
    ntm_median: float | None
    enterprise_value: float
    equity_value: float
    implied_share_price: float


# ---------------------------------------------------------------------------
# Headline valuation summary
# ---------------------------------------------------------------------------


class HeadlineValuation(BaseModel):
    """Top-level numbers the analyst is committing to."""

    dcf_enterprise_value: float
    dcf_equity_value: float
    dcf_share_price: float
    comps_enterprise_value: float
    comps_equity_value: float
    comps_share_price: float


# ---------------------------------------------------------------------------
# Full submission
# ---------------------------------------------------------------------------


class Submission(BaseModel):
    """The complete structured output from an analyst (or agent)."""

    case_id: str
    analyst: str = "unknown"
    valuation_date: str  # ISO date string, e.g. "2026-06-30"

    historical: list[HistoricalYear]
    forecast: list[ForecastYear]

    wacc_inputs: WACCInputs
    wacc_outputs: WACCOutputs

    terminal_value_inputs: TerminalValueInputs
    terminal_value_outputs: TerminalValueOutputs

    dcf_outputs: DCFOutputs
    capital_structure: CapitalStructure
    equity_bridge: EquityBridge

    comps_inputs: CompsInputs
    comps_outputs: CompsOutputs

    headline: HeadlineValuation
    provenance: list[ProvenanceRecord] = Field(default_factory=list[ProvenanceRecord])
    notes: dict[str, Any] = Field(default_factory=dict[str, Any])


# ---------------------------------------------------------------------------
# Grader result
# ---------------------------------------------------------------------------


class GraderFailure(BaseModel):
    error_type: ErrorType
    severity: Severity
    metric: str
    expected: float | str | None = None
    observed: float | str | None = None
    message: str
    diagnostic_code: str  # e.g. "EQ_BRIDGE_CASH_REVERSED"


class GraderResult(BaseModel):
    grader: str
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    max_points: float
    points_earned: float
    passed: bool
    failures: list[GraderFailure] = Field(default_factory=list[GraderFailure])
    warnings: list[str] = Field(default_factory=list[str])
    info: list[str] = Field(default_factory=list[str])


# Resolve forward reference
GraderResult.model_rebuild()


# ---------------------------------------------------------------------------
# Final scoring report
# ---------------------------------------------------------------------------


class ScoringReport(BaseModel):
    case_id: str
    analyst: str
    total_score: float
    max_score: float
    pct_score: float
    grade: str
    hard_failures: list[GraderFailure]
    grader_results: list[GraderResult]
    summary: str
