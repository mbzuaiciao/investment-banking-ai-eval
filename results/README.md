# Investment Banking AI Eval — Experiment Index

This directory contains execution artifacts, raw LLM completions, candidate submissions, and deterministic grader reports across the benchmark's experimental ladder.

For the comprehensive research synthesis, methodology, and key findings, see **[Chapter 10 — Experimental Results & Research Synthesis](../docs/10_results_and_findings.md)**.

---

## Directory Organization

Results are grouped by benchmark case first, then by experiment stage:

```text
results/
├── northstar-v1/
│   ├── milestone-1/       # Direct baseline experiments (thinking on vs off)
│   ├── milestone-2/       # Structured analyst workflow experiments
│   ├── milestone-3/       # Natural deterministic feedback repair trials
│   └── milestone-3b/      # Controlled repair benchmark across 10 corrupted starting states
│
└── meridian-v1/
    ├── milestone-4c-direct/            # Meridian direct baseline experiments
    ├── milestone-4d-structured/        # Meridian structured analyst experiments
    ├── milestone-4e-repair/            # Meridian natural deterministic feedback repair trials
    └── milestone-4e-controlled-repair/ # Meridian controlled repair benchmark (m01-m10)
```

> [!NOTE]
> Explicit `--output` paths always override the case-scoped defaults. Historical Northstar experiments may also remain located in flat `results/milestone-*` directories for legacy backward compatibility.

---

## Northstar v1 (Industrial Manufacturing Benchmark)

| Milestone | Experiment ID | Configuration & Purpose | Headline Metric | Artifact Directory |
|---|---|---|:---:|---|
| **Milestone 1 (Thinking Off)** | `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350` | Direct prompt; zero reasoning tokens (10 runs) | Mean: **90.5** / 100<br>HF Rate: **100%** | [`results/milestone-1/..._191350`](milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260822_191350) |
| **Milestone 1 (Thinking High)** | `m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143` | Direct prompt; high reasoning effort (10 runs) | Mean: **97.2** / 100<br>HF Rate: **100%** | [`results/milestone-1/..._192143`](milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260822_192143) |
| **Milestone 2 (Structured)** | `m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042` | Explicit 8-stage financial decomposition (10 runs) | Mean: **99.0** / 100<br>HF Rate: **30%** | [`results/milestone-2/..._210042`](milestone-2/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260822_210042) |
| **Milestone 3 (Repair)** | `m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546` | Structured prompt + conditional deterministic repair (10 runs) | Final: **98.8** / 100<br>Final HF: **0%** | [`results/milestone-3/..._231546`](milestone-3/m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_231546) |
| **Milestone 3B (Controlled Repair)** | `m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803` | 10 Controlled corrupted fixtures + 1-shot repair revision | Repair Success: **100%**<br>(10/10 clean) | [`results/milestone-3b/..._123803`](milestone-3b/m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_123803) |

---

## Meridian v1 (B2B SaaS Technology Benchmark)

| Milestone | Experiment ID | Configuration & Purpose | Headline Metric | Artifact Directory |
|---|---|---|:---:|---|
| **Milestone 4C (Direct Baseline)** | `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260823_152511` | Direct baseline smoke run (1 run) | Score: **83.2** / 100<br>HF Count: **21** | [`results/milestone-1/..._152511`](milestone-1/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260823_152511) |
