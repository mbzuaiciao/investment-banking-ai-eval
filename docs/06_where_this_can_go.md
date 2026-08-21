# Chapter 06 — Where This Can Go

Corporate valuation is only the beginning. This chapter explores the broader research roadmap: how we move from a single-call baseline toward verified, structured financial intelligence.

---

## 1. The Experimental Progression (M0 to M5)

The benchmark is designed to systematically evaluate increasingly sophisticated agent architectures:

```text
M0: Frozen Deterministic Benchmark Foundation
                    ↓
M1: Direct Analyst Baseline (Single Call)
                    ↓
M2: Structured Analyst (Decomposed Pipeline)
                    ↓
M3: Deterministic Feedback & Self-Repair
                    ↓
M4: Independent Verifier Agent
                    ↓
M5: Full Iterative Analyst + Verifier Team
```

Let's examine the research question for each milestone:

---

### Milestone 1: Direct Analyst Baseline (Current)
- **Architecture**: One prompt, one model completion, zero scaffolding.
- **Core Research Question**:
  > *"How reliably can an unaided frontier LLM complete the end-to-end valuation task from raw text?"*

---

### Milestone 2: Structured Analyst Pipeline
- **Architecture**: Decomposing the task into explicit stages:
  1. *Extraction Agent*: extracts historicals and guidance from sources into structured data tables.
  2. *Assumption Engine*: explicit analyst assumption layer with justification and provenance tags.
  3. *Calculation Engine*: code/formula execution layer for deterministic math (WACC, DCF, comps).
  4. *Synthesis Engine*: formats final pitchbook submission.
- **Core Research Question**:
  > *"Does explicitly separating evidence extraction, assumption setting, and deterministic calculation eliminate arithmetic and accounting errors?"*

---

### Milestone 3: Deterministic Diagnostic Feedback
- **Architecture**: The model receives machine-readable error diagnostics (e.g. `[CRITICAL] TV_NOT_DISCOUNTED: Expected PV(TV) = TV / (1+WACC)^5`) and is given a single turn to correct its submission.
- **Core Research Question**:
  > *"Can an AI system reliably self-repair specific financial errors when provided with precise compiler-like diagnostics?"*

---

### Milestone 4: Independent Verifier Agent
- **Architecture**: A separate "Associate / VP" model reviews the candidate analyst's draft submission, checks for common failure modes (cash reversal, capex double-counting, Guidance fabrication), and issues feedback before final grading.
- **Core Research Question**:
  > *"Can a separate language model detect subtle financial and evidentiary errors without access to ground truth?"*

---

### Milestone 5: Iterative Analyst + Verifier Collaboration
- **Architecture**: Multi-turn collaboration between an Analyst agent and a Verifier agent, terminating when the Verifier signs off or a maximum turn budget is reached.
- **Core Research Question**:
  > *"Does iterative multi-agent verification improve final benchmark reliability enough to justify the added token cost and latency?"*

---

## 2. Expanding Financial Horizons

Beyond single-company DCF and comps modeling, this evaluation methodology naturally extends to complex investment-banking workflows:

```text
               FUTURE INVESTMENT BANKING EVALUATION MODULES
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. M&A Accretion / Dilution  │ 4. Pitchbook Cross-Artifact Consistency      │
│ 2. LBO Debt Financing Models │ 5. Real SEC 10-K / 10-Q Ingestion Pipeline   │
│ 3. Working Capital Modeling  │ 6. Spreadsheet Formula & Cell Logic Auditing │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. M&A Accretion / Dilution Modeling
- Evaluating pro-forma EPS impact, purchase price allocation, goodwill creation, transaction financing mix (cash vs. stock vs. debt), and after-tax synergy phase-in schedules.

### 2. Leveraged Buyout (LBO) Debt Schedules
- Evaluating returns (IRR, MoIC), debt amortization waterfalls (revolving credit, Term Loan A/B, senior notes, subordinated mezzanine), and cash flow sweeps.

### 3. Pitchbook Cross-Artifact Consistency
- Evaluating complete presentation decks: asserting that executive summary bullets, valuation football fields, tear sheets, and appendix schedules never contradict one another.

### 4. Real-World SEC 10-K Ingestion
- Moving beyond synthetic markdown packets to raw 200-page SEC 10-K and 10-Q Edgar filings, testing table extraction, footnote parsing, and accounting reconciliations under messy real-world conditions.

### 5. Spreadsheet Formula & Cell-Dependency Auditing
- Inspecting generated Excel (`.xlsx`) files using `openpyxl`: asserting dynamic formulas (`=SUM()`, `=NPV()`) rather than hardcoded static numbers.

---

## 3. The Grand Research Framing

At its core, this benchmark addresses a fundamental question in AI safety and enterprise reliability:

> **"What architecture is required for AI systems to perform high-stakes, consequential analytical work without human babysitting?"**

Investment banking is an ideal testing ground because it combines:
- **Exact Arithmetic**: $1 + 1$ must equal $2$; a 10 bps WACC discrepancy moves firm valuations by millions.
- **Strict Accounting Logic**: Three-statement financial models must articulate and balance.
- **Evidentiary Integrity**: Distinguishing facts in evidence from analyst speculation is paramount.
- **Qualitative Judgment**: Economic assumptions require contextual domain expertise.
- **Hierarchical Review**: Replicating the rigorous Analyst $\rightarrow$ Associate $\rightarrow$ Vice President $\rightarrow$ Managing Director review cycle.

By building rigorous, deterministic evaluations like `investment-banking-ai-eval`, we lay the empirical foundation for reliable financial intelligence.

---

## Congratulations!

You have completed the **Investment Banking AI Eval Learning Lab**.

- Return to **[Tutorial Index](README.md)**
- Explore the **[Repository Codebase](../src/ib_eval/)**
- Grade the gold submission: `uv run ib-eval grade examples/gold_submission`
- Run the baseline: `uv run ib-eval baseline --help`
