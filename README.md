# Investment Banking AI Eval

> **The benchmark does not ask only whether an AI produced the right valuation.
> It asks whether the financial process producing that valuation is defensible.**

A deterministic, typed evaluation harness for assessing AI systems on
investment-banking financial analysis tasks. Built around the fictional
**Northstar Components, Inc.** case.

---

## What this benchmark evaluates

Investment banking analysis involves a chain of decisions: selecting source
data, interpreting qualitative guidance, building a financial model, and
translating that model into a valuation conclusion.

Each step can fail in distinct ways:

| Failure type | Example |
|---|---|
| **Arithmetic error** | NOPAT = EBIT × (1 + tax) instead of × (1 − tax) |
| **Formula error** | WACC computed without the tax shield on debt |
| **Accounting inconsistency** | EBIT ≠ EBITDA − D&A |
| **Source error** | Q2 quarterly revenue used as full-year annual revenue |
| **Provenance fabrication** | Claiming management stated exactly 8% growth |
| **Valuation error** | Terminal value not discounted to present value |
| **Cross-artifact inconsistency** | Headline share price differs from model output |

An AI that fluently writes financial prose can still commit every one of
these errors. This benchmark evaluates whether the *financial process* is
correct, not whether the output reads well.

---

## Why financial correctness differs from fluent financial writing

A large language model can produce text that *sounds* like a professional
investment-banking memo — complete with appropriate hedging language, correct
terminology, and structurally coherent prose — while embedding material
computational errors.

Consider:
- A model that writes "we derive a WACC of 9.3%" but applies the pre-tax
  cost of debt (failing to apply the tax shield) will produce a subtly wrong
  discount rate that inflates the DCF enterprise value.
- A model that writes "management guided to 8% growth" when management only
  stated "high single digits" has fabricated a fact — even if 8% is a
  defensible assumption.

Deterministic graders can catch these errors mechanically; a human reading
the output might not notice.

---

## Three dimensions of correctness

This benchmark distinguishes three orthogonal dimensions:

### 1. Mathematical correctness
Is the arithmetic right? Does EBIT = EBITDA − D&A? Does UFCF equal
NOPAT + D&A − Capex − ΔNWC? Is the terminal value discounted?

These have objectively correct answers. The graders check them without tolerance.

### 2. Financial reasonableness
Are the assumptions defensible? A 2026E revenue growth rate of 8% is
reasonable given "high single digits" guidance. A rate of 20% is not.

The benchmark allows judgment differences within defensible ranges and does
not penalize reasonable assumption choices.

### 3. Evidentiary support
Is each assumption traceable to a source? Is the source correctly interpreted?
Is a qualitative statement correctly classified as such, rather than being
treated as a precise numerical commitment?

The provenance system tracks this dimension explicitly.

---

## The Northstar Components, Inc. case

**Industry**: Industrial components  
**Valuation date**: June 30, 2026  
**Units**: USD millions (except per-share values)

### Historical financials

| Metric | 2023A | 2024A | 2025A |
|---|---|---|---|
| Revenue | 820.0 | 905.0 | 1,000.0 |
| EBITDA | 131.2 | 149.3 | 165.0 |
| EBITDA margin | 16.0% | 16.5% | 16.5% |
| D&A | 32.8 | 36.2 | 40.0 |
| EBIT | 98.4 | 113.1 | 125.0 |
| Capex | 36.9 | 40.7 | 45.0 |
| NWC | 98.4 | 108.6 | 120.0 |

### Gold DCF assumptions

| Parameter | Value |
|---|---|
| 2026E revenue growth | 8.0% (analyst interpretation of "high single digits") |
| EBITDA margins | 17.0% → 18.5% (2026–2030E) |
| D&A | 4.0% of revenue |
| Capex | 4.5% of revenue |
| NWC | 12.0% of revenue |
| Tax rate | 25% |
| Risk-free rate | 4.1% |
| Beta | 1.18 |
| ERP | 5.5% |
| Pre-tax cost of debt | 6.2% |
| Equity weight | 78% |
| Debt weight | 22% |
| **WACC** | **9.2832%** |
| Terminal growth | 2.5% |

### Gold headline valuation (code-derived)

The exact values below are computed from first principles by the DCF engine.
They may differ slightly from the approximate values in the specification due
to full-precision floating-point arithmetic; the code-derived values are canonical.

Run `uv run python cases/northstar-v1/ground_truth/generate_gold.py` to see
the precise outputs.

Approximate values per spec:
- DCF enterprise value: ~$1,713mm
- DCF equity value: ~$1,388mm
- DCF implied share price: ~$23.13
- Comps NTM median: 8.2x
- Comps equity value: ~$1,180.5mm
- Comps implied share price: ~$19.68

### Deliberate source traps

The case contains eight deliberate traps that test extraction accuracy:

1. **Quarterly/YTD confusion**: Q2 revenue ($281mm) and H1 revenue ($535mm) both appear in sources
2. **EBITDA definition**: Management references "adjusted EBITDA"; historical uses GAAP EBIT + D&A
3. **High-single-digit guidance**: Management never states exactly 8%
4. **Restructuring charge**: $9mm 2025 charge may or may not be normalized
5. **Convertible debt**: $75mm convertible — treatment must be explicit
6. **N/M peer**: Evergreen Controls has negative EBITDA; must not be assigned zero
7. **Fiscal-year mismatch**: Crestline Systems has Sep 30 FY end
8. **Capex terminology**: "Capital investment" (guidance) = "purchases of PP&E" (cash flow statement)

---

## How to run the benchmark

### Prerequisites

- Python 3.12+
- `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

```bash
uv sync --all-groups
```

### Grade the gold submission

```bash
uv run ib-eval grade examples/gold_submission
```

Expected output:
```
100 / 100
```

### Grade a custom submission

```bash
uv run ib-eval grade path/to/your/submission/
```

The submission directory must contain a `submission.json` conforming to
the `Submission` schema defined in `src/ib_eval/schemas.py`.

### Run tests

```bash
uv run pytest
```

### Lint and type-check

```bash
uv run ruff check .
uv run pyright
```

### Regenerate gold submission

```bash
uv run python cases/northstar-v1/ground_truth/generate_gold.py
```

### Run all corrupted fixtures

```bash
for d in examples/corrupted/*/; do
  echo "--- $d ---"
  uv run ib-eval grade "$d" --quiet
done
```

---

## Repository structure

```
investment-banking-ai-eval/
├── pyproject.toml
├── cases/northstar-v1/
│   ├── case.yaml          # Case metadata
│   ├── rubric.yaml        # Grader weights and tolerances
│   ├── sources/           # Synthetic source documents (with traps)
│   └── ground_truth/      # Gold submission generator
├── src/ib_eval/
│   ├── cli.py             # CLI entry point
│   ├── schemas.py         # Pydantic submission schema
│   ├── dcf.py             # DCF engine (explicit formulas)
│   ├── comps.py           # Trading comps engine
│   ├── provenance.py      # Provenance helpers
│   ├── case.py            # Case/rubric loader
│   ├── scoring.py         # Aggregator
│   └── graders/           # 10 deterministic graders
├── examples/
│   ├── gold_submission/   # Perfect-score submission
│   └── corrupted/         # One fixture per error class
└── tests/                 # Comprehensive test suite
```

---

## Current limitations (Milestone 0)

- No LLM or agent integration — graders evaluate structured JSON submissions only
- Qualitative memo grading is out of scope
- Only one case (Northstar v1)
- No web UI or notebook interface
- No RAG or document extraction pipeline

---

## Future roadmap

- **Milestone 1**: Agent harness — plug in an LLM agent and evaluate its structured output
- **Milestone 2**: Document extraction — evaluate source-reading accuracy from raw documents
- **Milestone 3**: Additional cases — more companies, industries, and deal types
- **Milestone 4**: Qualitative grading — evaluate memo writing and reasoning chains
- **Milestone 5**: Leaderboard — compare models and agents systematically

---

## Design principles

- **Deterministic**: Graders produce the same result for the same input every time
- **Typed**: All schemas are Pydantic models; all graders are typed Python
- **Inspectable**: Every grader failure includes a diagnostic code and message
- **Tolerant where appropriate**: Judgment differences are not penalized
- **Strict where objective**: Hard failures are always reported

---

*This benchmark is an independent research project. It is not affiliated with
or endorsed by any AI company.*
