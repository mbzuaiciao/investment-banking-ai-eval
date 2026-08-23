# Chapter 03 — What an AI Eval Is and How Graders Work

---

## 1. What Is an AI Eval?

> **"An evaluation (eval) is a repeatable, automated framework to test whether an AI system performs a task correctly, and to diagnose precisely how and why it fails."**

In traditional software development, unit tests assert that functions return expected values. In AI engineering, evaluations measure the capabilities, reliability, and error distributions of probabilistic models across standardized tasks.

---

## 2. Why Deterministic Graders over "LLM Judges"?

A common trend in generative AI benchmarking is using an LLM (such as GPT-4) as an evaluative judge to score another LLM's essay on a 1-to-5 scale.

While LLM judges are useful for subjective stylistic qualities (e.g., tone, conciseness), they are **unsuitable for financial modeling**:

```text
               DO NOT ASK AN LLM JUDGE WHETHER 17 × 23 = 391
┌───────────────────────────────────────┬───────────────────────────────────────┐
│           LLM as Judge                │         Deterministic Graders         │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ • Stochastic: Scores vary per run     │ • 100% Deterministic: Exact same score│
│ • Susceptible to hallucinated math    │ • Verified from mathematical formulas │
│ • Blind to subtle arithmetic errors   │ • Enforces strict financial accounting│
│ • Expensive and slow (extra API calls)│ • Microsecond execution locally       │
│ • Vague feedback ("looks plausible")  │ • Machine-readable diagnostic codes   │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

Wherever an objective mathematical, accounting, or evidentiary rule exists, **we write code to grade it deterministically**.

---

## 3. The 10 Deterministic Graders

The benchmark runs 10 specialized, modular graders located in `src/ib_eval/graders/`:

```text
                               10 MODULAR GRADERS
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Source Fidelity          │ 5. WACC                      │ 9. Trading Comps│
│ 2. Revenue Forecast         │ 6. Terminal Value            │ 10. Consistency │
│ 3. Margin Forecast          │ 7. Enterprise Value          │                 │
│ 4. Free Cash Flow           │ 8. Equity Bridge             │                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

Let's inspect what each grader checks:

---

### Grader 1: `source_fidelity` (Weight: 15 pts)
- **Dimension**: Evidentiary Support & Provenance
- **What it checks**: Validates that all model inputs trace to recognized sources and that forward assumptions are not falsely claimed as direct management statements.
- **Correct Example**: `revenue_growth/2026E` classified as `analyst_assumption` with qualitative note.
- **Failure Example**: Notes stating *"Management guided to 8% growth"* (`SF_GUIDANCE_FABRICATED`).

---

### Grader 2: `revenue_forecast` (Weight: 8 pts)
- **Dimension**: Mathematical Correctness & Source Trap
- **What it checks**: Validates revenue projections across 2026E–2030E, checking that growth is within a defensible 7–9% range and not confused with Q2 ($281mm) or H1 ($535mm) interim figures.
- **Correct Example**: 2026E Revenue = $1,080.0mm ($1,000mm × 1.08).
- **Failure Example**: 2026E Revenue = $281.0mm (`REV_QUARTERLY_CONFUSION`).

---

### Grader 3: `margin_forecast` (Weight: 7 pts)
- **Dimension**: Accounting Integrity
- **What it checks**: Verifies that $\text{EBITDA} = \text{Revenue} \times \text{Margin}$, $\text{D&A} = 4.0\% \times \text{Revenue}$, and $\text{EBIT} = \text{EBITDA} - \text{D&A}$.
- **Correct Example**: $\text{EBIT} = \$183.60 - \$43.20 = \$140.40\text{mm}$.
- **Failure Example**: Setting EBIT to $155.40mm without subtracting D&A (`MARGIN_EBIT_INCONSISTENCY`).

---

### Grader 4: `free_cash_flow` (Weight: 10 pts)
- **Dimension**: Formula Correctness
- **What it checks**: Verifies $\text{NOPAT} = \text{EBIT} \times (1 - t)$, $\text{Capex} = 4.5\% \times \text{Revenue}$, $\Delta\text{NWC} = \text{NWC}_t - \text{NWC}_{t-1}$, and $\text{UFCF} = \text{NOPAT} + \text{D&A} - \text{Capex} - \Delta\text{NWC}$.
- **Correct Example**: 2026E UFCF = $\$105.30 + \$43.20 - \$48.60 - \$9.60 = \$90.30\text{mm}$.
- **Failure Example**: Doubling Capex ($97.20mm) due to terminology confusion (`FCF_CAPEX_DOUBLE_COUNTED`).

---

### Grader 5: `wacc` (Weight: 8 pts)
- **Dimension**: Corporate Finance Formula
- **What it checks**: Re-derives CAPM cost of equity ($K_e$), after-tax cost of debt ($K_d(1-t)$), capital structure weights ($W_e + W_d = 1.0$), and blended WACC.
- **Correct Example**: $\text{WACC} = 0.78(10.59\%) + 0.22(4.65\%) = 9.2832\%$.
- **Failure Example**: Using pre-tax debt ($6.2\%$) yielding wrong WACC of $9.6242\%$ (`WACC_PRETAX_DEBT`).

---

### Grader 6: `terminal_value` (Weight: 7 pts)
- **Dimension**: Valuation Formula & Discounting
- **What it checks**: Ensures Gordon Growth is applied ($TV = FCF_{T+1}/(WACC - g)$), $g < WACC$, and critically, that $TV$ is **discounted to the valuation date** by $(1+WACC)^5$.
- **Correct Example**: $\text{PV}(TV) = \$2,003.78 \times 0.641554 = \$1,285.53\text{mm}$.
- **Failure Example**: Using $\$2,003.78\text{mm}$ undiscounted as PV (`TV_NOT_DISCOUNTED`).

---

### Grader 7: `enterprise_value` (Weight: 5 pts)
- **Dimension**: Valuation Aggregation
- **What it checks**: Verifies that $\text{EV} = \sum \text{PV}(\text{UFCF}) + \text{PV}(TV)$.
- **Correct Example**: $\text{EV} = \$427.43\text{mm} + \$1,285.53\text{mm} = \$1,712.97\text{mm}$.
- **Failure Example**: Summing forecast UFCFs incorrectly (`EV_SUM_ERROR`).

---

### Grader 8: `equity_bridge` (Weight: 10 pts)
- **Dimension**: Capital Structure Bridge
- **What it checks**: Reconciles $\text{Net Debt} = \text{Gross Debt} - \text{Cash}$, $\text{Equity Value} = \text{EV} - \text{Net Debt}$, and $\text{Share Price} = \text{Equity} / \text{Shares}$.
- **Correct Example**: $\text{Equity} = \$1,712.97 - \$325.00 = \$1,387.97\text{mm}$ ($\$23.13/\text{share}$).
- **Failure Example**: Adding cash to debt ($\text{Net Debt} = \$515\text{mm}$) (`EQ_BRIDGE_CASH_REVERSED`).

---

### Grader 9: `comps` (Weight: 10 pts)
- **Dimension**: Market Multiples & Edge Cases
- **What it checks**: Excludes negative EBITDA peers (Evergreen Controls) from median calculation; computes EV, Equity Value, and Share Price from multiple × EBITDA.
- **Correct Example**: Median of `[7.3, 7.9, 8.5, 9.2]` = 8.20x; Evergreen = N/M.
- **Failure Example**: Setting Evergreen to 0.0x and computing median = 7.9x (`COMPS_NM_COERCED_ZERO`).

---

### Grader 10: `consistency` (Weight: 20 pts)
- **Dimension**: Cross-Artifact Truth
- **What it checks**: Ensures that the headline executive summary numbers match the underlying financial model schedules exactly.
- **Correct Example**: Headline DCF Equity = $\$1,387.97\text{mm}$ == Model Equity = $\$1,387.97\text{mm}$.
- **Failure Example**: Headline reports $\$1,578.00\text{mm}$ while model calculated $\$1,387.97\text{mm}$ (`CONSISTENCY_HEADLINE_DCF`).

---

## 4. Why Machine-Readable Diagnostics Matter

When a human grader reviews a student's model, writing *"Wrong answer on line 42"* is unhelpful. Instead, our graders emit structured diagnostic objects:

```json
{
  "error_type": "accounting_inconsistency",
  "severity": "critical",
  "metric": "equity_bridge.minus_net_debt",
  "expected": 325.0,
  "observed": 515.0,
  "message": "Cash appears to have been ADDED to gross debt rather than subtracted. Net debt = 420 - 95 = 325, not 515.",
  "diagnostic_code": "EQ_BRIDGE_CASH_REVERSED"
}
```

### Why diagnostic codes are powerful:
1. **Automated Error Taxonomy**: We can calculate that 35% of model failures are `SF_GUIDANCE_FABRICATED` while only 5% are `EQ_BRIDGE_CASH_REVERSED`.
2. **Deterministic Debugging**: Engineers can write regression tests that assert the presence of specific diagnostic codes.
3. **Future AI Verifier Feedback**: In later milestones, these exact diagnostic codes can be fed to verifier agents to test automated model repair.

---

## 5. Scoring Points vs. Hard Failure Flags

The benchmark uses a **100-point scoring system**. However, points alone can be deceptive:
- A model might get 95/100 by performing every forecast step correctly, but add cash instead of subtracting it in the equity bridge.
- In corporate finance, a \$190 million equity error is not a "minor 5-point deduction" — it is a catastrophic transaction error.

Therefore, the benchmark separates **points earned** from **hard failure flags**:

```text
┌─────────────────────────────────────────────────────────────┐
│ SCORING REPORT                                              │
│ Total Score:  97.5 / 100  (A+)                              │
│                                                             │
│ Hard Failures (1):                                          │
│   [CRITICAL] EQ_BRIDGE_CASH_REVERSED: Cash added to debt    │
│                                                             │
│ VERDICT: Model failed critical execution check!             │
└─────────────────────────────────────────────────────────────┘
```

A submission is only considered genuinely passing if it scores high **AND** has zero hard failures.

---

## 6. Architecture Rule: Parsing vs. Grading Abstraction Boundary

The benchmark enforces a strict separation of concerns between data deserialization and financial evaluation:

> **Design Principle**: *"Parsing validates representability; graders validate financial correctness."*

### Why Financially Wrong Answers Must Parse Successfully
In an AI evaluation harness, a submission that contains financial errors is precisely what the benchmark is designed to evaluate and diagnose. If the Pydantic schema layer enforces mathematical identities or financial invariants (such as rejecting WACC weights that do not sum to 1.0 or equity bridges where $\text{EV} - \text{Net Debt} \neq \text{Equity Value}$), the evaluation harness rejects the candidate before deterministic graders can execute.

This conflates **model error** with **parser failure**, obscuring the exact failure mode and corrupting reliability metrics:

```text
┌───────────────────────────────┬───────────────────────────────┐
│     Structural Invalidity     │     Financial Invalidity      │
├───────────────────────────────┼───────────────────────────────┤
│ • Malformed or truncated JSON │ • WACC weights sum to 100%    │
│ • Missing required fields     │ • EV − Net Debt ≠ Equity Value│
│ • Invalid data types (None)   │ • EBITDA − D&A ≠ EBIT         │
│ • Invalid enum values         │ • Net cash subtracted from EV │
├───────────────────────────────┼───────────────────────────────┤
│     PARSE FAILURE (0 pts)     │  PARSE SUCCESS + GRADER FAILS │
│     Taxonomy: Schema/JSON     │  Taxonomy: Diagnostic Codes   │
└───────────────────────────────┴───────────────────────────────┘
```

By keeping the schema focused purely on structural types and moving all mathematical and accounting checks into the 10 deterministic graders, candidate submissions remain 100% gradeable and emit explicit diagnostic codes.

---

## Next Steps

Now let's see these graders in action on real error examples in **[Chapter 04 — Learning from the Corrupted Fixtures](04_failure_modes.md)**.
