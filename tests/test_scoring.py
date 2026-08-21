"""Tests for scoring utilities."""

from __future__ import annotations

from ib_eval.scoring import grade_letter


def test_grade_letter_a_plus() -> None:
    assert grade_letter(1.0) == "A+"
    assert grade_letter(0.95) == "A+"


def test_grade_letter_a() -> None:
    assert grade_letter(0.90) == "A"
    assert grade_letter(0.92) == "A"


def test_grade_letter_b_plus() -> None:
    assert grade_letter(0.85) == "B+"


def test_grade_letter_b() -> None:
    assert grade_letter(0.80) == "B"


def test_grade_letter_c() -> None:
    assert grade_letter(0.70) == "C"


def test_grade_letter_d() -> None:
    assert grade_letter(0.60) == "D"


def test_grade_letter_f() -> None:
    assert grade_letter(0.50) == "F"
    assert grade_letter(0.0) == "F"
