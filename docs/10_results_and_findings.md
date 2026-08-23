# Chapter 10 — Experimental Results & Research Synthesis

This document synthesizes findings across **Milestones 1, 2, 3, and 3B** of the `investment-banking-ai-eval` benchmark.

It evaluates how model reasoning, explicit domain workflow decomposition, and deterministic compiler-like feedback affect the accuracy and reliability of large language models on complex financial modeling tasks.

---

## 1. Executive Summary

On a synthetic investment-banking valuation task (**Northstar Components, Inc.**), increasing model reasoning capacity improved average numerical accuracy and reduced variance, but did not eliminate critical financial modeling errors. Imposing an explicit, multi-stage analyst workflow materially reduced those failures and eliminated a systematic terminal-value discounting defect. Adding deterministic financial invariant checks plus a single targeted revision turn eliminated the remaining observed hard failures in natural runs and successfully repaired all 10 controlled financial failure modes in the benchmark.

> [!WARNING]
> **Scope & Generalization Boundary**: These empirical findings are derived from one synthetic valuation case (Northstar v1) and one primary model configuration (`deepseek-v4-flash` with thinking/reasoning modes). They characterize benchmark behavior and reliability mechanisms rather than proving broad generalization across unconstrained institutional investment-banking workflows.

---

## 2. Experimental Progression

The benchmark evaluates financial AI reliability across an experimental ladder of increasing architectural structure while holding the underlying case data constant.

```text
Milestone 1: Direct Prompting (Unassisted)
   ├── Thinking Off  → Broad arithmetic, formula, and DCF structure failures
   └── Thinking High → High average score (97.2), but 100% hard-failure rate (TV discounting defect)
           ↓
Milestone 2: Structured Analyst Workflow
   └── Explicit 8-stage financial reasoning → Eliminates TV defect; hard-failure rate drops to 30%
           ↓
Milestone 3: Natural Feedback Repair
   └── Grader diagnostics feedback loop → 1/1 natural failures repaired; final hard-failure rate 0% (n=1)
           ↓
Milestone 3B: Controlled Repair Benchmark
   └── 10 deliberate corrupted starting states → 10/10 failure modes repaired cleanly with 0 regressions
```

---

### Milestone 1 — Direct Analyst Baseline

**Research Question**: *Can a frontier model complete a multi-schedule valuation reliably when given only raw case sources and a direct schema prompt in a single completion?*

#### Condition A: Thinking Off (Zero Reasoning Scaffold)
- **Experiment ID**: [`m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350)
- **Sample Size**: 10 trials
- **Parse Success**: 9/10 (90.0%)
- **Mean Score**: 90.5 / 100 (Std Dev: 2.7, Median: 90.4)
- **Hard-Failure Rate**: **100.0% of parsed runs** (9/9)

Without reasoning tokens, the model exhibited widespread accounting and arithmetic instability:
- **Free Cash Flow Pass Rate**: **0.0%** (frequent `FCF_UFCF_ERROR` across all 5 forecast years)
- **Terminal Value Pass Rate**: **0.0%** (`TV_FORMULA_ERROR` and `TV_PV_ERROR`)
- **WACC Pass Rate**: **33.3%** (`WACC_FORMULA_ERROR`)
- **Revenue Forecast Pass Rate**: **55.6%** (`REV_ARITHMETIC`)

#### Condition B: Thinking High (Extended Reasoning Scaffold)
- **Experiment ID**: [`m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143)
- **Sample Size**: 10 trials
- **Parse Success**: 10/10 (100.0%)
- **Mean Score**: 97.2 / 100 (Std Dev: 1.2, Median: 97.5)
- **Hard-Failure Rate**: **100.0%** (10/10)

Enabling high reasoning effort substantially improved core schedules:
- Revenue, Margin, WACC, Enterprise Value, Equity Bridge, Comps, and Consistency graders all achieved **100% pass rates**.
- **The Critical Reliability Gap**: Despite a high aggregate mean score (97.2), **100% of runs failed the Terminal Value grader** (`TV_PV_ERROR` on 10/10 trials). The direct prompt allowed the model to skip the formal present-value discounting step $PV(TV) = TV / (1 + WACC)^5$, introducing a structural valuation error in every trial.

---

### Milestone 2 — Structured Analyst Workflow

**Research Question**: *Does imposing an explicit 8-stage financial analysis workflow eliminate systematic modeling defects under matched single-call model conditions?*

- **Experiment ID**: [`m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-2/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042)
- **Sample Size**: 10 trials
- **Parse Success**: 10/10 (100.0%)
- **Mean Score**: 99.0 / 100 (Std Dev: 1.2, Median: 99.2)
- **Hard-Failure Rate**: **30.0%** (3/10)

#### Key Architectural Intervention
Holding provider, model, and reasoning parameters identical to Milestone 1 Condition B, the prompt was restructured into an explicit 8-stage decomposition:
$$\text{Source Extraction} \rightarrow \text{Assumption Ledger} \rightarrow \text{Forecast Schedules} \rightarrow \text{WACC} \rightarrow \text{Terminal Value} \rightarrow \text{Bridge} \rightarrow \text{Comps} \rightarrow \text{Invariant Check}$$

#### Key Observation
- **Terminal Value Grader Pass Rate**: Rose from **0.0% (Milestone 1) to 100.0% (Milestone 2)**. Decomposing the horizon TV calculation from PV discounting completely eliminated the systematic discounting error.
- **Residual Failures**: 3 of 10 runs contained isolated residual errors: 2 runs emitted `FCF_NOPAT_ERROR` (NOPAT formula discrepancy) and 1 run emitted `COMPS_MEDIAN_ERROR` (median ranking mistake).

---

### Milestone 3 — Natural Deterministic Feedback Repair

**Research Question**: *When the model makes an error during generation, can machine-readable deterministic grader diagnostics guide it to repair the defect in a single revision turn?*

- **Experiment ID**: [`m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-3/m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546)
- **Sample Size**: 10 trials
- **Parse Success**: 10/10 (100.0%)
- **Initial Hard-Failure Rate**: 10.0% (1/10)
- **Final Hard-Failure Rate**: **0.0%** (0/10)
- **Repair Success Rate**: **100.0% (1/1 initially failing run repaired)**
- **Newly Introduced Errors**: 0

#### Benchmark Dynamics & Sample Size Limitation
In this 10-run live experiment, 9 of 10 initial completions were already clean (0 hard failures) and appropriately skipped the repair call. Exactly 1 trial emitted a hard failure (`FCF_NOPAT_ERROR`). When presented with the violated accounting invariant, the model cleanly resolved the NOPAT calculation, recomputed downstream cash flows, and achieved a final score of 100.0 with 0 hard failures.

> [!NOTE]
> **Why Milestone 3B Was Necessary**: While Milestone 3 demonstrated that compiler-like feedback successfully repaired a real residual failure, evaluating $n=1$ failing trial is statistically insufficient to characterize repair reliability across diverse financial error types.

---

### Milestone 3B — Controlled Repair Benchmark

**Research Question**: *Across a comprehensive, controlled set of 10 known financial failure modes, can the model reliably repair each error in one revision without introducing regressions?*

- **Experiment ID**: [`m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-3b/m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803)
- **Fixtures Evaluated**: 10 standardized corrupted benchmark starting states (`c01`–`c10`)
- **Parse Success**: 10/10 (100.0%)
- **Controlled Repair Success Rate**: **100.0%** (10/10 repaired to 0 hard failures)
- **Target Diagnostic Resolution Rate**: **100.0%** (10/10 target errors resolved)
- **New Error Introduction Rate**: **0.0%** (0/10 regressions)
- **Mean Score Shift**: **95.6 $\rightarrow$ 100.0** ($\Delta = +4.4$)

#### Breakdown by Propagation Difficulty
- **Local Repairs** (3/3 clean): Succeeded on Comps median coercion (`c05`), fabricated guidance provenance (`c06`), and headline/schedule synchronization (`c09`).
- **Propagating Repairs** (7/7 clean): Succeeded on multi-schedule cascading corrections: quarterly revenue confusion (`c01`), TV undiscounted (`c02`), equity bridge cash reversal (`c03`), debt omission (`c04`), EBITDA/EBIT inconsistency (`c07`), capex double counting (`c08`), and pre-tax WACC (`c10`). In every propagating case, the model correctly recomputed dependent schedules through to Implied Share Price.

---

## 3. Consolidated Results Table

| Experiment | Workflow Configuration | Sample Size | Parse Success | Mean Score | Hard-Failure Rate | Key Empirical Result |
|---|---|:---:|:---:|:---:|:---:|---|
| **M1 Direct (Thinking Off)** | Zero reasoning; direct schema prompt | 10 runs | 90.0% (9/10) | 90.5 | 100.0% *(of parsed)* | Widespread formula & arithmetic failures; 0% pass on FCF & TV |
| **M1 Direct (Thinking High)** | High reasoning effort; direct schema prompt | 10 runs | 100.0% (10/10) | 97.2 | 100.0% | Core arithmetic improved; systematic TV discounting error on 10/10 runs |
| **M2 Structured Workflow** | High reasoning effort; 8-stage financial decomposition | 10 runs | 100.0% (10/10) | 99.0 | 30.0% | TV discounting defect eliminated (100% pass); hard failures reduced to 30% |
| **M3 Natural Feedback Repair** | Structured prompt + conditional deterministic repair turn | 10 runs | 100.0% (10/10) | 98.8 *(final)* | 0.0% *(final)* | 9 clean runs skipped; 1/1 natural failure cleanly repaired ($n=1$) |
| **M3B Controlled Repair** | 10 Corrupted fixture starting states + 1-shot repair revision | 10 fixtures | 100.0% (10/10) | 100.0 *(final)* | 0.0% *(final)* | 10/10 target errors resolved; 0 regressions across local & propagating tiers |

*Note: For M1 Thinking Off, hard-failure rate is computed over the 9 successfully parsed runs. For M3B, the 10 fixtures represent deterministic coverage of known benchmark failure modes rather than independent random samples.*

---

## 4. High Scores Are Not the Same as Reliability

A central methodological finding of this research is that **aggregate benchmark scores conceal critical financial modeling failures**.

In Milestone 1 (Thinking High), models achieved an average score of **97.2 out of 100**. In traditional NLP evaluations, a 97% accuracy score would be interpreted as near-human ceiling performance. However, because the missing points stemmed from a single omitted discount factor on Terminal Value, every single valuation model produced an enterprise value inflated by over \$200 million.

```text
Aggregate Score: 97.2 / 100  ("A Grade")
       ├── Revenue Forecast:  100% Correct
       ├── Margin Forecast:   100% Correct
       ├── WACC Derivation:   100% Correct
       ├── Equity Bridge:     100% Correct
       └── Terminal Value:    PV(TV) Undiscounted  →  Valuation Invalidated ($200M+ Error)
```

In institutional finance, a financial model that is 97% correct is unacceptable if the remaining 3% inverts the valuation conclusion. Robust AI evaluation harnesses must track:
1. **Mean & Median Aggregate Scores**;
2. **Hard-Failure Incidence** (proportion of runs violating non-negotiable accounting/financial invariants);
3. **Specific Diagnostic Code Frequencies**;
4. **Cross-Artifact & Schedule Consistency**.

---

## 5. The Three Reliability Layers

The empirical results reveal that financial modeling reliability is governed by three distinct structural layers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│  Layer 3: Deterministic Invariant Auditing & Targeted Repair           │
│  • Fast Python compiler checks financial invariants                    │
│  • Targeted machine-readable diagnostics guide 1-shot self-repair       │
│  • Result: Eliminates residual failures (0% hard failures in M3/M3B)   │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 2: Explicit Workflow Decomposition                              │
│  • 8-stage financial reasoning path (extraction → assumptions → DCF)   │
│  • Forces intermediate variable materialization before synthesis       │
│  • Result: Eliminates structural defects (TV pass rate: 0% → 100%)     │
├────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Frontier Model Reasoning (Thinking Mode)                     │
│  • Internal chain-of-thought calculation & constraint adherence        │
│  • Reduces arithmetic noise and score variance                         │
│  • Result: Lifts baseline score (90.5 → 97.2), but leaves blind spots   │
└────────────────────────────────────────────────────────────────────────┘
```

Reliability improved most effectively when raw model intelligence was paired with **domain structure** and **deterministic compiler verification**, rather than relying on unconstrained reasoning tokens alone.

---

## 6. What Deterministic Grading Does NOT Mean

A critical distinction in this evaluation methodology is separating **objective financial invariants** from **financial judgment**.

```text
               TAXONOMY OF FINANCIAL EVALUATION CRITERIA
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Deterministic Invariants (Strict Graders & Diagnostic Repair)            │
│    • Mathematical & accounting identities: NOPAT = EBIT × (1 - t)           │
│    • Valuation discounting: PV(TV) = TV / (1 + WACC)^n                      │
│    • Bridge arithmetic: Equity Value = EV - Debt + Cash                     │
│    • Comps median selection and cross-schedule consistency                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Convention-Dependent Assumptions (Tolerance Ranges & Explicit Notes)      │
│    • Mid-year vs. year-end discounting convention                           │
│    • Day-count conventions, calendarization, stub periods                   │
│    • Convertible debt in-the-money vs. debt treatment conventions           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Professional Judgment & Qualitative Thesis (Rubric / Human Review)       │
│    • Selection of comparable peer group                                     │
│    • Normalization and quality-of-earnings adjustments                      │
│    • Terminal growth rate selection relative to long-term GDP               │
│    • Management credibility assessment and guidance skepticism              │
└─────────────────────────────────────────────────────────────────────────────┘
```

Deterministic evaluators are designed to enforce **Level 1 Invariants** and verify the internal mathematical and evidentiary integrity of candidate models. They do not claim that investment banking can be reduced to deterministic rules.

---

## 7. Key Findings

1. **Reasoning Tokens Materially Improve Baseline Precision**: High reasoning effort improved mean score from 90.5 to 97.2 and reduced standard deviation from 2.7 to 1.2.
2. **Reasoning Alone Leaves Systematic Blind Spots**: Despite high reasoning capacity, 100% of direct prompt runs omitted terminal value discounting, proving that scaling reasoning without domain structure does not guarantee domain correctness.
3. **Structured Decomposition Eliminates Structural Defects**: Decomposing analysis into 8 financial stages lifted TV pass rates from 0% to 100% and reduced overall hard failures from 100% to 30%.
4. **Aggregate Scores Conceal Valuation-Breaking Flaws**: High average scores ($\ge 97\%$) occurred simultaneously with critical enterprise value calculation errors.
5. **Deterministic Diagnostics Enable Precision Self-Repair**: Providing invariant feedback without leaking ground-truth answers enabled clean resolution of residual failures in live generation ($n=1$) and across all 10 controlled failure modes ($n=10$).
6. **Propagating Errors Were Fully Repaired in the Controlled Benchmark**: When prompted with cascade recomputation instructions, models successfully updated all downstream schedules (UFCF $\rightarrow$ EV $\rightarrow$ Share Price) without introducing secondary arithmetic errors.
7. **The Best Results Came From a Hybrid Reliability Architecture**: The combination of LLM evidentiary extraction + structured analyst workflows + deterministic invariant verification achieved the highest overall reliability.

---

## 8. Benchmark Limitations

To maintain scientific integrity, the following limitations must be recognized:

- **Single Synthetic Case**: All experiments were run on Northstar Components, Inc. Performance on other corporate structures, distress cases, or irregular reporting periods remains unmeasured.
- **Single Model Family**: Primary comparative data reflects `deepseek-v4-flash` under specific reasoning parameters. Cross-provider comparisons across different model families may reveal different failure distributions.
- **Small Sample Sizes**: 10-run sample sizes are intended to expose architectural failure modes and evaluate mechanisms, not to establish population-level statistical confidence intervals.
- **Synthetic Corrupted Fixtures**: Milestone 3B tests 10 deliberately constructed failure modes. While representative of common financial modeling errors, they do not encompass all possible real-world errors.
- **Grader Scope**: A clean benchmark score indicates **absence of detected invariant violations**, not complete financial wisdom or investment viability.

---

## 9. What the Results Support vs. Do Not Support

### Supported by the Evidence:
- Within the Northstar benchmark, structured workflows and deterministic compiler feedback materially improved model reliability.
- Deterministic feedback enabled clean, single-revision repair across 10 controlled financial error classes without introducing regressions.
- High aggregate scores alone are insufficient to verify financial correctness.

### NOT Supported by the Evidence:
- The system is "production-ready" for live, autonomous corporate transaction execution without human review.
- The 10 deterministic graders cover all possible investment-banking failure modes.
- A 100% repair success rate on synthetic fixtures guarantees repair of every future arbitrary financial error.
- Structured prompting is universally optimal across all non-financial domains.

---

## 10. Recommended Next Milestone: Cross-Case Generalization

Rather than further hyper-optimizing performance against Northstar v1, the most valuable next research milestone is **cross-case generalization**.

### Milestone 4 — Multi-Case Generalization
- **Core Research Question**: *Do the structured workflow, deterministic graders, and invariant repair architecture generalize to a completely different corporate financial profile without modification?*
- **Proposed Case Profile** (e.g. `meridian-energy-v1` or `summit-saas-v1`):
  - Different industry operating model (e.g. recurring subscription revenue or heavy asset depreciation);
  - High debt leverage / complex capital structure (preferred shares, minority interest);
  - Different management guidance ambiguity traps;
  - Negative historical cash flows requiring customized terminal value mechanics.

---

## Results Provenance & Directory Index

All quantitative metrics and diagnostic traces in this report are verifiable via their artifact bundles:

| Milestone | Experiment ID | Primary Summary Link |
|---|---|---|
| **M1 Thinking Off** | `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350` | [summary.json](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350/summary.json) |
| **M1 Thinking High** | `m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143` | [summary.json](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143/summary.json) |
| **M2 Structured** | `m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042` | [summary.json](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-2/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042/summary.json) |
| **M3 Feedback Repair** | `m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546` | [summary.json](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-3/m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546/summary.json) |
| **M3B Controlled Repair** | `m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803` | [summary.json](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-3b/m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803/summary.json) |

---

## Quick Navigation

- Previous: **[Chapter 09 — Controlled Repair Benchmark](09_controlled_repair_benchmark.md)**
- Roadmap: **[Chapter 06 — Where This Can Go](06_where_this_can_go.md)**
- Benchmark Root: **[README.md](../README.md)**
