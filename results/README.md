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
| **Milestone 4C (Thinking Off)** | `m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260823_161149` | Direct prompt; zero reasoning tokens (10 runs) | Parse: **90%** (9/10)<br>Mean: **84.5** / 100<br>HF Rate: **100%** | [`results/meridian-v1/milestone-4c-direct/..._161149`](meridian-v1/milestone-4c-direct/m1-direct-deepseek-deepseek-v4-flash-thinking-off-20260823_161149) |
| **Milestone 4C (Thinking High)** | `m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260823_162206` | Direct prompt; high reasoning effort (10 runs; reprocessed) | Parse: **100%** (10/10)<br>Mean: **85.5** / 100<br>HF Rate: **100%** | [`results/meridian-v1/milestone-4c-direct/..._162206`](meridian-v1/milestone-4c-direct/m1-direct-deepseek-deepseek-v4-flash-thinking-high-20260823_162206) |
| **Milestone 4D (Structured v1 — Historical)** | `m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260823_185724` | Structured prompt (v1 Northstar-hardcoded workflow; 10 runs) | Parse: **100%** (10/10)<br>Mean: **94.2** / 100<br>HF Rate: **100%** (`SBC_EBITDA_INCONSISTENCY` 10/10) | [`results/meridian-v1/milestone-4d-structured/..._185724`](meridian-v1/milestone-4d-structured/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260823_185724) |
| **Milestone 4D (Structured v2 — Generalized)** | `m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260823_200609` | Generalized 8-stage workflow (accounting bridge from sources; 10 runs) | Parse: **100%** (10/10)<br>Mean: **93.7** / 100<br>HF Rate: **100%** (SBC drops to 4/10; D&A 7/10, UFCF 6/10) | [`results/meridian-v1/milestone-4d-structured/..._200609`](meridian-v1/milestone-4d-structured/m2-structured-deepseek-deepseek-v4-flash-thinking-high-20260823_200609) |
| **Milestone 4E (Natural Repair)** | `m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_212253` | Structured v2 prompt + conditional deterministic feedback repair (10 runs) | Parse: **100%** (10/10)<br>Final Mean: **98.9** / 100<br>Final HF Rate: **40%** (Clean runs: 3 $\rightarrow$ 6) | [`results/meridian-v1/milestone-4e-repair/..._212253`](meridian-v1/milestone-4e-repair/m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260823_212253) |
| **Milestone 4E (Controlled Repair)** | `m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260824_000733` | 10 Controlled corrupted fixtures (`m01`–`m10`) + 1-shot repair revision | Parse: **100%** (10/10)<br>Target Resolution: **100%** (10/10)<br>Clean Repair: **90%** (9/10 clean, 1 partial) | [`results/meridian-v1/milestone-4e-controlled-repair/..._000733`](meridian-v1/milestone-4e-controlled-repair/m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260824_000733) |

> [!NOTE]
> **Prompt Generalization Note**: Experiment `m2-structured-...-20260823_185724` used the historical `structured_v1` prompt which hardcoded `EBIT_t = EBITDA_t - DA_t`, inducing a 10/10 SBC omission error on Meridian. This run is preserved intact as empirical evidence of prompt-induced error. Future experiments use the case-generalized `structured_v2` workflow.
