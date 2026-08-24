# Chapter 10 — Experimental Results & Research Synthesis

This document synthesizes findings across **Milestones 1 through 4E** of the `investment-banking-ai-eval` benchmark.

It evaluates how model reasoning, explicit domain workflow decomposition, deterministic verification, and deterministic compiler-like feedback affect the accuracy and reliability of large language models on complex investment banking valuations across two distinct corporate profiles: **Northstar Components, Inc.** (mature industrial manufacturing) and **Meridian Cloud Systems, Inc.** (high-growth B2B SaaS).

---

## 1. Executive Summary

Across two materially different financial cases, increasing model reasoning capacity improved average numerical calculation precision and reduced variance, but failed to eliminate systematic financial modeling defects. Imposing an explicit, multi-stage analyst workflow reduced structural omissions, but revealed that rigid or single-case prompts can accidentally encode prompt-induced accounting errors. Adding deterministic financial verification exposed valuation-breaking errors concealed beneath high aggregate scores. Finally, closing the loop with a single deterministic feedback repair turn resolved **100% of controlled target failure modes on both cases** (10/10 Northstar, 10/10 Meridian) and produced **95.0% clean repaired submissions across all 20 controlled fixtures** (10/10 Northstar, 9/10 Meridian).

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                             THE FOUR-LAYER RELIABILITY LADDER                            │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Deterministic Feedback Repair                                                   │
│   • Single-pass revision guided by machine-readable compiler diagnostics                 │
│   • Result: 100% target error resolution across 20 controlled fixtures (95% fully clean) │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ Layer 3: Deterministic Invariant Verification                                            │
│   • Fast Python evaluators verify mathematical, accounting, and valuation identities    │
│   • Result: Separates internal consistency from true financial correctness               │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Structured Workflow Decomposition                                               │
│   • 8-stage financial reasoning path (Extraction → Ledger → DCF → WACC → Bridge → Comps) │
│   • Result: Eliminates structural omissions (e.g. TV discounting 0% → 100% pass)         │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Frontier Model Reasoning (Thinking Mode)                                        │
│   • Internal chain-of-thought calculation & constraint adherence                         │
│   • Result: Lifts baseline precision (Mean: 90.5 → 97.2), but leaves systematic flaws     │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

> [!WARNING]
> **Scope & Generalization Boundary**: These empirical findings are derived from two synthetic valuation cases (`northstar-v1`, `meridian-v1`) and one primary model family (`deepseek-v4-flash` under thinking/reasoning modes). They characterize benchmark reliability mechanisms rather than proving broad generalization across unconstrained, real-world institutional transactions.

---

## 2. Canonical Experiments Summary

The table below summarizes the canonical experiments across both benchmark cases.

| Case | Milestone & Stage | Prompt / Workflow | Runs | Parse Rate | Mean Score | Score SD | Hard-Failure Rate | Key Failure Mode / Empirical Finding |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Northstar** | **M1 Direct (Thinking Off)** | `direct_v1` | 10 | 90.0% (9/10) | 90.5 | 2.7 | **100.0%** *(of parsed)* | Widespread arithmetic errors; 0% pass on FCF & TV schedules |
| **Northstar** | **M1 Direct (Thinking High)** | `direct_v1` | 10 | 100.0% (10/10) | 97.2 | 1.2 | **100.0%** | Arithmetic stabilized; 10/10 runs omitted TV discounting (`TV_PV_ERROR`) |
| **Northstar** | **M2 Structured (Thinking High)** | `structured_v1` | 10 | 100.0% (10/10) | 99.0 | 1.2 | **30.0%** | TV discounting fixed (100% pass); 3/10 residual NOPAT/comps errors |
| **Northstar** | **M3 Natural Repair** | `structured_v1` + repair | 10 | 100.0% (10/10) | 98.8 *(final)* | 1.8 | **0.0%** *(final)* | 9 clean runs skipped; 1/1 natural failing trial cleanly repaired |
| **Northstar** | **M3B Controlled Repair** | `c01`–`c10` (10 fixtures) | 10 | 100.0% (10/10) | 100.0 *(final)* | 0.0 | **0.0%** *(final)* | **10/10 target errors resolved; 10/10 fully clean repairs (0 regressions)** |
| **Meridian** | **M4C Direct (Thinking Off)** | `direct_v1` | 10 | 90.0% (9/10) | 84.5 | 16.3 | **100.0%** | Severe SaaS accounting confusion (SBC, deferred rev, net cash reversed) |
| **Meridian** | **M4C Direct (Thinking High)** | `direct_v1` | 10 | 100.0% (10/10) | 85.5 | 9.8 | **100.0%** | Reprocessed 10/10 parsed; systematic comps (10/10) & UFCF (8/10) failures; TV & WACC errors |
| **Meridian** | **M4D Structured (v1 Historical)** | `structured_v1` *(flawed)* | 10 | 100.0% (10/10) | 94.2 | 2.8 | **100.0%** | **Prompt-induced defect**: prompt hardcoded `EBIT = EBITDA - DA`, causing 10/10 SBC omissions |
| **Meridian** | **M4D Structured (v2 Generalized)** | `structured_v2` | 10 | 100.0% (10/10) | 93.7 | 3.3 | **100.0%** | SBC error dropped to 4/10; revealed natural D&A (7/10) and UFCF (6/10) residuals |
| **Meridian** | **M4E Natural Repair** | `structured_v2` + repair | 10 | 100.0% (10/10) | 98.9 *(final)* | 1.6 | **40.0%** *(final)* | Mean +3.6; HF rate 70% $\rightarrow$ 40%; clean runs 3 $\rightarrow$ 6; 3/7 failing runs fully clean |
| **Meridian** | **M4E Controlled Repair** | `m01`–`m10` (10 fixtures) | 10 | 100.0% (10/10) | 99.8 *(final)* | 0.7 | **10.0%** *(final)* | **10/10 target errors resolved; 9/10 fully clean repairs (1 partial repair)** |

*Note on Meridian Direct (Thinking High): Reprocessed after schema financial validators were properly relocated to deterministic graders, establishing a true 10/10 parsed baseline.*

---

## 3. The Four-Layer Reliability Architecture

### Layer 1: Model Reasoning (Extended Thinking Tokens)
- **Role**: Expands internal chain-of-thought calculation tokens to execute multi-step arithmetic, percentage derivations, and schema constraint satisfaction.
- **Contribution**: Substantially reduced arithmetic noise and compressed score variance (Northstar SD: 2.7 $\rightarrow$ 1.2; Meridian Parse: 90% $\rightarrow$ 100%).
- **Limitation**: **Reasoning does not guarantee domain completeness**. Without external structure, models systematically omitted present-value discounting on Northstar (10/10 runs) and misapplied SaaS revenue run-rates on Meridian.

### Layer 2: Structured Workflow Decomposition
- **Role**: Restructures the prompt into an explicit 8-stage financial modeling pipeline ($\text{Extraction} \rightarrow \text{Assumptions} \rightarrow \text{Forecast Schedules} \rightarrow \text{WACC} \rightarrow \text{Terminal Value} \rightarrow \text{Bridge} \rightarrow \text{Comps} \rightarrow \text{Invariant Checklist}$).
- **Contribution**: Forces intermediate calculation materialization before final synthesis. On Northstar, TV discounting pass rate rose from **0.0% to 100.0%**.
- **Limitation**: **Rigid structure can encode systematic errors**. If workflow instructions assume single-case conventions (e.g. standard industrial EBITDA accounting), they induce systematic errors when applied to different corporate structures.

### Layer 3: Deterministic Invariant Verification
- **Role**: Implements fast, rule-based Python evaluators that enforce mathematical identities, accounting bridges, and valuation mechanics.
- **Contribution**: Decouples structural parsing from financial correctness. Provides precise, localized failure classification without human evaluation latency.
- **Limitation**: Graders only evaluate encoded invariants; they verify correctness relative to case facts, not unconstrained investment thesis validity.

### Layer 4: Deterministic Feedback Repair
- **Role**: Feeds machine-readable grader diagnostics (affected metric, submitted value, and violated invariant rule) back to the candidate model for a single revision turn.
- **Contribution**: **The most effective reliability intervention in the benchmark**. Converted explicit compiler-like diagnostics into clean, cascading corrections across 95% of tested failure modes without ground-truth leakage.
- **Limitation**: Repair is not infallible; models can occasionally resolve a target failure while introducing a new secondary discrepancy (e.g. Meridian `m05`). Repaired outputs must always be re-graded.

---

## 4. Core Finding: Consistency Is Not Financial Correctness

A foundational result across both cases is that **internal mathematical reconciliation does NOT imply financial or economic truth**.

```text
               APPARENT VS. TRUE VALUATION INTEGRITY
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Structural Representability (Pydantic Schema Validation)                 │
│    • Valid JSON conforming to types, field keys, and enums                  │
│    • Pass Rate: 100% across all structured runs                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Internal Mechanical Reconciliation (Consistency Grader: 20/20 Points)    │
│    • EV = Sum(PV(UFCF)) + PV(TV)  [Checked: Matches Model's Schedules]      │
│    • Equity Value = EV - Net Debt  [Checked: Matches Model's Schedules]     │
│    • Implied Share Price = Equity / Shares [Checked: Exact Division]        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. True Financial Correctness (Accounting & Valuation Invariants)           │
│    • Did the model omit $100M+ in Stock-Based Compensation? (SBC Error)     │
│    • Did the model subtract Net Cash instead of adding it? (Net Debt Sign)  │
│    • Did the model apply EV/Revenue multiple to EBITDA? (Comps Metric Mismatch)│
└─────────────────────────────────────────────────────────────────────────────┘
```

In multiple Meridian trials, the model submitted valuation models where:
- Headline Enterprise Value matched the DCF table down to the penny ($20.0 / 20.0$ consistency score);
- Equity Bridge reconciled perfectly with submitted net debt;
- Implied share price was mathematically exact;
- **Yet the valuation was invalidated** because the model omitted non-cash SBC from GAAP EBIT or inverted the cash sign on net debt.

> [!IMPORTANT]
> **Implication for Financial AI Systems**: Evaluators cannot rely on scalar scores or self-reconciliation checks alone. Systems must grade specific, non-negotiable financial invariants independently.

---

## 5. Case Study: Evaluation Workflows Must Themselves Be Evaluated

During Milestone 4D, benchmarking on Meridian Cloud Systems revealed a critical evaluation artifact:

1. **The Flaw in `structured_v1`**: The initial structured prompt hardcoded Northstar's simple industrial accounting formula:
   $$\text{EBIT}_t = \text{EBITDA}_t - \text{D\&A}_t$$
2. **The Impact on Meridian**: For Meridian (a B2B SaaS firm), reported EBITDA is Adjusted EBITDA, requiring non-cash Stock-Based Compensation (SBC) to be deducted to bridge to GAAP EBIT:
   $$\text{GAAP EBIT}_t = \text{Adjusted EBITDA}_t - \text{SBC}_t - \text{D\&A}_t$$
   By following the prompt's hardcoded equation, the model omitted SBC in **10 out of 10 runs**, creating a 100% `SBC_EBITDA_INCONSISTENCY` hard-failure rate.
3. **The `structured_v2` Generalization**: We generalized the prompt to instruct the model to identify the case-specific accounting bridge and reconcile reported metrics to GAAP EBIT from source documents.
4. **The Empirical Result**: In `structured_v2`, SBC error incidence dropped from **10/10 (100%) to 4/10 (40%)**, demonstrating that the majority of initial SBC omissions were prompt-induced rather than model-induced.

> [!NOTE]
> **Evaluation Lesson**: Historical `structured_v1` artifacts are preserved intact in `results/` as empirical documentation of how rigid workflow templates can inject systematic errors.

---

## 6. Synthesis: Natural Deterministic Feedback Repair

| Case | Initial Runs Needing Repair | Initial Mean Score | Repaired Mean Score | Initial HF Rate | Final HF Rate | Clean Runs (0 HF) | Outcome |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Northstar v1** | 1 / 10 (10.0%) | 98.8 | **98.8** | 10.0% (1 run) | **0.0%** (0 runs) | 9 $\rightarrow$ **10 / 10** | 1/1 natural failure resolved cleanly |
| **Meridian v1** | 7 / 10 (70.0%) | 95.3 | **98.9** | 70.0% (7 runs) | **40.0%** (4 runs) | 3 $\rightarrow$ **6 / 10** | 3/7 failing runs fully clean; 5/7 improved; 1 worsened |

### Detailed Natural Repair Analysis

#### A. Northstar Natural Repair
- **Experiment-Level Mean**: Initial mean score across all 10 runs was **98.75 / 100**; final mean score was **98.80 / 100** ($\Delta = +0.05$).
- **Clean Runs Skipped**: 9 of 10 initial completions were already clean (0 hard failures) and appropriately skipped repair.
- **The Repaired Run (`003`)**: Run `003` was the sole run with a hard failure (`FCF_NOPAT_ERROR` across all 5 forecast years, initial score: 98.00). In response to the diagnostic feedback, the model corrected the NOPAT schedule and recomputed downstream cash flows, achieving a repaired score of **98.50 with 0 hard failures**.
- **Sample Limitation**: While repair succeeded on the observed failure ($1/1$, 100%), the small natural failing denominator ($n=1$) limits broad statistical inference on Northstar without the controlled benchmark.

#### B. Meridian Natural Repair
- **Experiment-Level Mean**: Initial mean score was **95.26 / 100**; final mean score was **98.87 / 100** ($\Delta = +3.61$ across all 10 runs; $+5.15$ on the 7 repaired runs).
- **Hard-Failure Transition**: Hard-failure rate dropped from **70.0% (7/10) to 40.0% (4/10)**; clean runs doubled from **3/10 (30%) to 6/10 (60%)**.
- **Multi-Category Resolution**: Resolved 16 diagnostic instances across 10 categories. On Run `008` (which initially exhibited 26 hard failures across 8 categories), repair lifted score from $72.35 \rightarrow 98.00$.
- **Residual & New Errors**: 3 runs exhibited persistent D&A calculation issues (`MARGIN_DA_INCONSISTENCY`), and 2 runs introduced secondary errors during revision (Run `005` introduced an SBC omission; Run `008` introduced a minor UFCF formula discrepancy).
- **Core Conclusion**: Natural repair materially improves financial models, but repair is not infallible, underscoring the requirement to re-grade repaired outputs.

---

## 7. Synthesis: Controlled Repair Benchmark

To test repair reliability across isolated, standardized failure modes, the benchmark evaluated 20 total corrupted fixtures (10 Northstar, 10 Meridian):

| Fixture Class | Northstar (`c01`–`c10`) | Meridian (`m01`–`m10`) | Combined Total | Combined Success Rate |
|---|:---:|:---:|:---:|:---:|
| **Local Errors** | 3 / 3 clean (100%) | 2 / 2 clean (100%) | 5 / 5 clean | **100.0%** |
| **Propagating Errors** | 7 / 7 clean (100%) | 7 / 8 clean (87.5%)* | 14 / 15 clean | **93.3%** |
| **Total Controlled Fixtures** | **10 / 10 clean (100%)** | **9 / 10 clean (90.0%)** | **19 / 20 clean** | **95.0%** |
| **Target Diagnostic Resolution** | **10 / 10 (100.0%)** | **10 / 10 (100.0%)** | **20 / 20 resolved** | **100.0%** |

*\*Note on Meridian propagating repair: Meridian fixture `m05` (SBC omission) resolved its target diagnostic, but introduced a secondary `MARGIN_EBIT_INCONSISTENCY` during forecast recalculation (partial repair, score 97.7).*

### Cross-Case Controlled Generalization
Across both industrial manufacturing and high-growth B2B SaaS cases:
- Models successfully updated multi-tier cascading schedules (Base Revenue $\rightarrow$ Margins $\rightarrow$ NOPAT $\rightarrow$ UFCF $\rightarrow$ DCF EV $\rightarrow$ Net Debt $\rightarrow$ Equity Value $\rightarrow$ Share Price).
- Zero ground-truth numbers or target formula values were leaked in the diagnostic prompts.
- Deterministic diagnostic feedback provided sufficient structural signal for frontier reasoning models to correct severe financial modeling defects.

---

## 8. Cross-Case Comparison: Northstar vs. Meridian

| Dimension | Northstar Components (`northstar-v1`) | Meridian Cloud Systems (`meridian-v1`) | Cross-Case Implication |
|---|---|---|---|
| **Industry & Model** | Industrial manufacturing; capex-heavy; working capital intensive | B2B enterprise SaaS; high gross margins; negative working capital | Evaluates whether invariant architecture handles distinct operational profiles |
| **Profitability Profile** | Positive historical & projected GAAP EBIT; stable EBITDA | Negative / emerging GAAP EBIT; massive non-cash SBC add-back | Tests GAAP vs. non-GAAP reconciliation robustness |
| **Capital Structure** | Net Debt ($\$325\text{M}$ debt, $\$95\text{M}$ cash); Convertible notes | Net Cash ($\$0\text{M}$ debt, $\$200\text{M}$ cash); Diluted options | Tests bidirectional equity bridge sign handling |
| **Discounting Convention**| Year-End discounting convention ($t = 1..5$) | Mid-Year discounting convention ($t = 0.5..4.5$) | Tests explicit vs. horizon terminal value timing mechanics |
| **Comps Methodology** | 8.2x NTM EV / EBITDA (median: 8.20x) | EV / NTM Revenue (median: 6.35x; N/M FCF peer exclusion) | Tests multiple-to-metric alignment and outlier handling |
| **Controlled Repair Result**| **10 / 10 Clean (100.0%)** | **9 / 10 Clean (90.0%)** | **Supports cross-case generalization of the repair architecture across these two synthetic cases** |

---

## 9. Summary: What We Learned

1. **More Reasoning Helps, But Is Not Enough**: Reasoning tokens reduce calculation errors and tighten score variance, but models still suffer from systematic domain blind spots.
2. **Structure Improves Consistency, But Can Hardcode Bias**: Multi-stage workflows eliminate omissions, but prompts must guide reconciliation from sources rather than dictating single-case formulas.
3. **Internal Consistency Is Not Financial Correctness**: Fully reconciled financial models can still be economically invalid.
4. **Deterministic Graders Provide Crucial Localization**: Rule-based evaluators expose hidden errors and isolate failure modes without human grading latency.
5. **One Repair Pass Resolves Most Explicitly Diagnosed Errors**: Targeted compiler-like feedback resolved 100% of controlled target errors across 20 distinct financial failure modes.
6. **Repaired Outputs Must Always Be Re-Graded**: Repair can occasionally introduce secondary discrepancies; closing the loop requires re-verification.
7. **Cross-Case Benchmarking Prevents Premature Optimization**: Expanding beyond a single synthetic case exposed hidden prompt assumptions and supported architectural robustness across tested profiles.

---

## 10. Benchmark Limitations & Threats to Validity

To maintain rigorous scientific standards, the following limitations must be recognized:

1. **Two Synthetic Cases ($N=2$)**: Findings are demonstrated on Northstar and Meridian. While they represent opposite operating models (industrial vs SaaS), they do not cover distress restructuring, complex M&A tax structures, or banking regulatory capital.
2. **Single Primary Model Condition**: Quantitative benchmarks reflect `deepseek-v4-flash` under high reasoning effort. Cross-provider comparisons across other frontier models may exhibit different baseline failure profiles.
3. **Small Sample Sizes ($N=10$)**: 10-trial baseline experiments are calibrated to identify architectural failure modes rather than establish tight population confidence intervals.
4. **Controlled Fixture Artificiality**: The 20 corrupted fixtures test deliberate, isolated failure modes. Real-world human models often contain compound, noisy errors.
5. **Grader Horizon**: Graders evaluate encoded financial invariants; a clean 100.0 score denotes **zero detected invariant violations**, not an endorsement of investment thesis or valuation judgment.
6. **Prompt Evolution**: The evolution from `structured_v1` to `structured_v2` altered prompt structure between early and late experiments; historical comparisons are documented accordingly.

---

## 11. Results Provenance & Artifact Index

All reported metrics are verifiable via their artifact bundles:

| Case | Milestone | Experiment Directory |
|---|---|---|
| **Northstar** | **M1 Direct (Thinking Off)** | [`results/northstar-v1/milestone-1/m1-direct-...-20260822_191350`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/northstar-v1/milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350) |
| **Northstar** | **M1 Direct (Thinking High)** | [`results/northstar-v1/milestone-1/m1-direct-...-20260822_192143`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/northstar-v1/milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143) |
| **Northstar** | **M2 Structured (Thinking High)** | [`results/northstar-v1/milestone-2/m2-structured-...-20260822_210042`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/northstar-v1/milestone-2/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042) |
| **Northstar** | **M3 Natural Repair** | [`results/northstar-v1/milestone-3/m3-repair-...-20260822_231546`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/northstar-v1/milestone-3/m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546) |
| **Northstar** | **M3B Controlled Repair** | [`results/northstar-v1/milestone-3b/m3b-controlled-repair-...-20260823_123803`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/milestone-3b/m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803) |
| **Meridian** | **M4C Direct (Thinking Off)** | [`results/meridian-v1/milestone-4c-direct/m1-direct-...-20260823_161149`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/meridian-v1/milestone-4c-direct/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260823_161149) |
| **Meridian** | **M4C Direct (Thinking High Reprocessed)** | [`results/meridian-v1/milestone-4c-direct/m1-direct-...-20260823_162206`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/meridian-v1/milestone-4c-direct/m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260823_162206) |
| **Meridian** | **M4D Structured (v1 Historical)** | [`results/meridian-v1/milestone-4d-structured/m2-structured-...-20260823_185724`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/meridian-v1/milestone-4d-structured/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260823_185724) |
| **Meridian** | **M4D Structured (v2 Generalized)** | [`results/meridian-v1/milestone-4d-structured/m2-structured-...-20260823_200609`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/meridian-v1/milestone-4d-structured/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260823_200609) |
| **Meridian** | **M4E Natural Repair** | [`results/meridian-v1/milestone-4e-repair/m3-repair-...-20260823_212253`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/meridian-v1/milestone-4e-repair/m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_212253) |
| **Meridian** | **M4E Controlled Repair** | [`results/meridian-v1/milestone-4e-controlled-repair/m3b-controlled-repair-...-20260824_000733`](file:///Users/xq/Documents/GitHub/investment-banking-ai-eval/results/meridian-v1/milestone-4e-controlled-repair/m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260824_000733) |

---

## Quick Navigation

- Previous: **[Chapter 09 — Controlled Repair Benchmark](09_controlled_repair_benchmark.md)**
- Meridian Benchmark Design: **[Chapter 12 — Meridian Benchmark Case](12_meridian_benchmark.md)**
- Benchmark Root: **[README.md](../README.md)**
