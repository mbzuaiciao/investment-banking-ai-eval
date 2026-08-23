# Investment Banking AI Eval — Experiment Index

This directory contains execution artifacts, raw LLM completions, candidate submissions, and deterministic grader reports across the benchmark's experimental ladder.

For the comprehensive research synthesis, methodology, and key findings, see **[Chapter 10 — Experimental Results & Research Synthesis](../docs/10_results_and_findings.md)**.

---

## Canonical Experiment Registry

| Milestone | Experiment ID | Configuration & Purpose | Headline Metric | Artifact Directory |
|---|---|---|:---:|---|
| **M1 Direct (Thinking Off)** | `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350` | Direct prompt; zero reasoning tokens (10 runs) | Mean: **90.5** / 100<br>HF Rate: **100%** | [`results/milestone-1/..._191350`](milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350) |
| **M1 Direct (Thinking High)** | `m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143` | Direct prompt; high reasoning effort (10 runs) | Mean: **97.2** / 100<br>HF Rate: **100%** | [`results/milestone-1/..._192143`](milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143) |
| **M2 Structured Workflow** | `m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042` | Explicit 8-stage financial decomposition (10 runs) | Mean: **99.0** / 100<br>HF Rate: **30%** | [`results/milestone-2/..._210042`](milestone-2/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042) |
| **M3 Feedback Repair** | `m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546` | Structured prompt + conditional deterministic repair (10 runs) | Final: **98.8** / 100<br>Final HF: **0%** | [`results/milestone-3/..._231546`](milestone-3/m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546) |
| **M3B Controlled Repair** | `m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803` | 10 Controlled corrupted fixtures + 1-shot repair revision | Repair Success: **100%**<br>(10/10 clean) | [`results/milestone-3b/..._123803`](milestone-3b/m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803) |

---

## Directory Organization

```text
results/
├── milestone-1/       # Direct baseline experiments (thinking on vs off)
├── milestone-2/       # Structured analyst workflow experiments
├── milestone-3/       # Natural deterministic feedback repair trials
└── milestone-3b/      # Controlled repair benchmark across 10 corrupted starting states
```
