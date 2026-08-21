# Chapter 00 — Project Overview

> **"The benchmark does not ask only whether an AI produced the right valuation. It asks whether the financial process producing that valuation is defensible."**

---

## 1. The Core Problem

Large language models (LLMs) excel at generating fluent, authoritative-sounding text. When prompted to perform a corporate valuation, a modern frontier model will easily generate a multi-page investment memorandum complete with correct financial terminology, standard valuation headers, and professional hedging language.

However, fluency is not correctness.

A model can write:
> *"Applying our rigorous discounted cash flow model, we discount unlevered free cash flows using a Weighted Average Cost of Capital (WACC) of 9.3%, reflecting the company's capital structure and market risk profile..."*

While secretly committing fatal errors:
1. **Mathematical Error**: Applying the pre-tax cost of debt in the WACC formula, forgetting the debt tax shield $(1 - t)$.
2. **Evidentiary Error**: Claiming that management "explicitly guided to 8.0% annual revenue growth" when management only stated qualitative "high single digits."
3. **Accounting Inconsistency**: Projecting operating income (EBIT) that does not equal EBITDA minus D&A.
4. **Valuation Error**: Calculating terminal value at the end of year 5 and adding it to enterprise value without discounting it back to present value.

To a human reader skimming the text, the prose looks impeccable. To an investment-banking transaction team, the model is financially broken.

---

## 2. Beyond "Right Answer" Evaluation

Standard machine learning benchmarks often evaluate tasks using single-point accuracy: did the model predict class $Y$, or generate exact string $X$?

In corporate finance, single-point accuracy is fundamentally insufficient:
- **Multiple defensible assumptions**: When management provides qualitative guidance ("high single digits"), an analyst choosing $7.5\%$, $8.0\%$, or $8.5\%$ revenue growth is making a defensible modeling choice. The benchmark must not mark an analyst wrong simply for picking $8.2\%$ instead of $8.0\%$.
- **Right answer for the wrong reason**: A model might make two compounding errors (e.g., overestimating cash flows by $20\%$ and overestimating discount rate by $200\text{ bps}$) that accidentally cancel out and yield the target share price.

This benchmark evaluates the **integrity of the financial process**.

```text
               EVALUATION OF FINANCIAL PROCESS
┌─────────────────────────────────────────────────────────────┐
│ 1. Evidentiary Basis: Are inputs grounded in source facts?  │
│ 2. Mathematical Integrity: Do formulas compute correctly?   │
│ 3. Accounting Logic: Do financial statements reconcile?     │
│ 4. Valuation Bridges: Does EV bridge to Equity correctly?   │
│ 5. Cross-Artifact Truth: Do headlines match underlying math?│
└─────────────────────────────────────────────────────────────┘
```

---

## 3. The Three Orthogonal Dimensions

To avoid collapsing complex financial work into a single subjective "quality" score, this benchmark evaluates three distinct dimensions:

```text
                   ┌───────────────────────────────────┐
                   │   Three Dimensions of AI Eval     │
                   └─────────────────┬─────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│   Mathematical    │       │     Financial     │       │    Evidentiary    │
│    Correctness    │       │   Reasonableness  │       │      Support      │
├───────────────────┤       ├───────────────────┤       ├───────────────────┤
│ • NOPAT formula   │       │ • Growth within   │       │ • Distinguishes   │
│ • UFCF derivation │       │   7–9% range      │       │   source facts    │
│ • WACC weighting  │       │ • Defensible      │       │   from assumptions│
│ • TV discounting  │       │   margins         │       │ • No fabricated   │
│ • EV/Equity bridge│       │ • Comp selection  │       │   guidance claims │
└───────────────────┘       └───────────────────┘       └───────────────────┘
```

### Dimension 1: Mathematical Correctness (Objective)
Is the math objectively true?
- Does $\text{NOPAT} = \text{EBIT} \times (1 - t)$?
- Does $\text{UFCF} = \text{NOPAT} + \text{D&A} - \text{Capex} - \Delta\text{NWC}$?
- Was terminal value discounted by $(1 + \text{WACC})^T$?
- Was net debt subtracted (rather than added) from enterprise value?

These are graded strictly and deterministically with zero tolerance for formula corruption.

### Dimension 2: Financial Reasonableness (Bounded Judgment)
Is the assumption economically defensible given the context?
- Given "high single digit" guidance, is 2026E growth between $7\%$ and $9\%$?
- Is EBITDA margin within a reasonable band around $17\%$?
- Did the analyst select an appropriate peer multiple band?

These allow bounded variation. A submission is not penalized for an analyst's judgment within justifiable bounds.

### Dimension 3: Evidentiary Support & Provenance (Traceability)
Where did each number come from, and is the epistemic claim honest?
- If the model assumes $8.0\%$ growth, does it label it as `analyst_assumption`, or does it claim management stated $8.0\%$ as a `direct` fact?
- Does every historical number trace back to a recognized source document?

Fabricating management guidance or claiming direct evidence for an assumption is a critical failure.

---

## 4. The Project Architecture & Milestones

The project is structured into clear, incremental milestones:

### Milestone 0: Deterministic Benchmark Foundation (Frozen)
Before testing any AI model, we must prove that the evaluator itself is flawless.
- Encodes the synthetic **Northstar Components, Inc.** case.
- Contains canonical first-principles DCF and trading comps models.
- Implements 10 deterministic Python graders returning machine-readable diagnostics.
- Includes 10 deliberately corrupted fixtures to prove that every grader catches its intended error.
- Verified with 100% test pass rate and strict static typing.

### Milestone 1: Direct Analyst Baseline
The simplest possible frontier-model experiment:
- Prompts a frontier model with the full Northstar source packet and JSON schema.
- Uses a single, unaided completion (no critics, no verifiers, no multi-turn loops).
- Parses responses strictly and grades them using Milestone 0.
- Aggregates multi-run statistics (mean score, variance, hard failure rate, error distributions).

---

## Next Steps

Now that you understand the motivation and architecture, proceed to **[Chapter 01 — The Northstar Case](01_northstar_case.md)** to explore the company, the evidence packet, and the deliberate traps.
