"""Unit tests for Meridian corrupted benchmark fixtures (Milestone 4B)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ib_eval.case import NorthstarCase, load_case
from ib_eval.schemas import Submission
from ib_eval.scoring import grade_submission

MERIDIAN_CASE_DIR = Path(__file__).parent.parent / "cases" / "meridian-v1"
CORRUPTED_DIR = Path(__file__).parent.parent / "examples" / "meridian_corrupted"


@pytest.fixture(scope="module")
def meridian_case() -> NorthstarCase:
    return load_case(MERIDIAN_CASE_DIR)


def load_submission(name: str) -> Submission:
    p = CORRUPTED_DIR / name / "submission.json"
    assert p.exists(), f"Missing corrupted fixture: {p}"
    return Submission.model_validate(json.loads(p.read_text()))


def test_m01_arr_revenue_confusion(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m01_arr_revenue_confusion")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "REV_ARR_CONFUSION" in codes


def test_m02_deferred_rev_reversed(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m02_deferred_rev_reversed")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "WC_DEFERRED_REV_REVERSED" in codes


def test_m03_software_double_counted(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m03_software_double_counted")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "FCF_SOFTWARE_DOUBLE_COUNTED" in codes


def test_m04_net_cash_reversed(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m04_net_cash_reversed")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "EQ_BRIDGE_NET_CASH_REVERSED" in codes


def test_m05_sbc_ebitda_inconsistency(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m05_sbc_ebitda_inconsistency")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "SBC_EBITDA_INCONSISTENCY" in codes


def test_m06_basic_shares_used(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m06_basic_shares_used")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "SHARES_BASIC_USED" in codes


def test_m07_midyear_convention_error(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m07_midyear_convention_error")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "DCF_MIDYEAR_CONVENTION_ERROR" in codes


def test_m08_nm_fcf_coerced_zero(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m08_nm_fcf_coerced_zero")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "COMPS_NM_FCF_COERCED_ZERO" in codes


def test_m09_fabricated_guidance(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m09_fabricated_guidance")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "SF_GUIDANCE_FABRICATED" in codes


def test_m10_pretax_wacc(meridian_case: NorthstarCase) -> None:
    sub = load_submission("m10_pretax_wacc")
    report = grade_submission(sub, meridian_case)
    codes = {hf.diagnostic_code for hf in report.hard_failures}
    assert "WACC_PRETAX_DEBT" in codes
