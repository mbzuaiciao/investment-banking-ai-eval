# Investment Banking AI Eval — Tutorial & Learning Lab

Welcome to the **Investment Banking AI Eval** learning guide.

This lab is designed for finance professionals, AI researchers, and software engineers who want to understand how to rigorously evaluate artificial intelligence on complex financial modeling tasks.

---

## The Learning Journey

```text
00. Project Overview
       ↓
01. The Northstar Case
       ↓
02. DCF & Comps from First Principles
       ↓
03. What is an AI Eval? (Graders & Diagnostics)
       ↓
04. Failure Modes & Corrupted Fixtures
       ↓
05. Milestone 1: Direct Analyst Baseline
       ↓
06. Where This Can Go (Agentic Architecture Roadmap)
       ↓
07. Milestone 2: Structured Analyst
       ↓
08. Milestone 3: Deterministic Feedback Repair
       ↓
09. Milestone 3B: Controlled Repair Benchmark
       ↓
10. Experimental Results & Research Synthesis
       ↓
11. Milestone 4A: Second Case Design (Meridian SaaS)
       ↓
12. Milestone 4B: Meridian Benchmark Implementation
```

---

## Suggested Study Order

We recommend working through the chapters sequentially, but actively running the corrupted fixtures when you reach Chapter 04.

Read **Chapters 00–03** first to understand the case, valuation mechanics, and grader design. When you reach **Chapter 04**, do not only read the failure examples—run them. Before each run, predict which grader and diagnostic should fire, then compare your prediction with the benchmark output. This hands-on loop is the fastest way to understand how the eval architecture works.

The highest-value learning loop is:

```text
predict the failure
        ↓
run the corrupted case
        ↓
inspect the grader diagnostic
        ↓
compare the result with your prediction
```

Example command:
```bash
uv run ib-eval grade examples/corrupted/c03_cash_subtracted
```

---

## Chapter Index

| Chapter | Title | What You Will Learn | Key Concepts |
|---|---|---|---|
| **[00](00_project_overview.md)** | **[Project Overview](00_project_overview.md)** | Why fluent prose does not equal financial correctness; the 3 core dimensions of evaluation. | Mathematical vs Financial vs Evidentiary correctness; Northstar & Meridian; Milestones 0–4E |
| **[01](01_northstar_case.md)** | **[The Northstar Case](01_northstar_case.md)** | Full briefing on the synthetic case; the 8 deliberate ambiguity traps embedded in source data. | High-single-digit guidance; Q2 vs YTD trap; GAAP vs Adjusted EBITDA; Convertible debt |
| **[02](02_dcf_and_comps.md)** | **[DCF & Trading Comps](02_dcf_and_comps.md)** | Step-by-step walkthrough of valuation math from first principles with actual numbers. | Revenue projections; NOPAT; UFCF; CAPM WACC; Gordon Growth TV; Net debt bridge; Comps median |
| **[03](03_eval_and_graders.md)** | **[AI Evals & Graders](03_eval_and_graders.md)** | How deterministic grading works; why LLM judges are avoided for math; 10 grader specs. | Deterministic evaluators; Machine-readable diagnostics; Tolerances; Hard failure flags |
| **[04](04_failure_modes.md)** | **[Failure Modes Lab](04_failure_modes.md)** | Hands-on inspection of 10 deliberately corrupted submissions and how each grader catches them. | Diagnostic codes; Error taxonomy; Executable CLI verification; Interactive exercise |
| **[05](05_direct_analyst_baseline.md)** | **[Direct Analyst Baseline](05_direct_analyst_baseline.md)** | How Milestone 1 turns the benchmark into a scientific experiment measuring LLM reliability. | Zero-scaffolding baseline; Score variance; Hard-failure rates; Cost guardrails; Offline exploration |
| **[06](06_where_this_can_go.md)** | **[Where This Can Go](06_where_this_can_go.md)** | The roadmap from direct completion to verifiers, feedback loops, M&A, and full agent teams. | Structured extraction; Verifier models; Iterative repair; Accretion/dilution; LBO modeling |
| **[07](07_structured_analyst.md)** | **[Structured Analyst (M2)](07_structured_analyst.md)** | How imposing an 8-stage financial workflow reduces critical errors under single-call constraints. | 8-stage reasoning workflow; Occurrence count vs run incidence; Comparative analysis |
| **[08](08_deterministic_feedback_repair.md)** | **[Feedback Repair (M3)](08_deterministic_feedback_repair.md)** | How deterministic grader diagnostics guide models to repair their own errors in one revision. | Invariant feedback; Repair success rate; Diagnostic transitions; Zero gold leakage |
| **[09](09_controlled_repair_benchmark.md)** | **[Controlled Repair (M3B)](09_controlled_repair_benchmark.md)** | Measuring single-revision repair across 10 controlled failure modes and propagation difficulties. | Controlled starting states; Local vs propagating repairs; Regression tracking |
| **[10](10_results_and_findings.md)** | **[Results & Findings](10_results_and_findings.md)** | Canonical research synthesis across Milestones 1–4E; 4 reliability layers, cross-case empirical findings, and limitations. | Four reliability layers; Invariant verification; Score vs reliability; Cross-case generalization |
| **[11](11_meridian_case_design.md)** | **[Case Design: Meridian (M4A)](11_meridian_case_design.md)** | Architectural design specification for the second evaluation case (B2B SaaS / Net Cash). | Generalization hypothesis; SaaS accounting; Net cash bridge; Mid-year DCF; Grader reuse |
| **[12](12_meridian_benchmark.md)** | **[Meridian Benchmark (M4B)](12_meridian_benchmark.md)** | Offline benchmark implementation for Meridian Cloud Systems, accounting mechanics, and validation. | Enterprise SaaS; Mid-year discounting; Net cash bridge; SBC reconciliation; 10 corrupted fixtures |

---

## Quick Navigation

- Next: **[Chapter 00 — Project Overview](00_project_overview.md)**
- Benchmark Root: **[README.md](../README.md)**
