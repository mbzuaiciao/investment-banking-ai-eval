# Chapter 08 — Milestone 3: Deterministic Feedback Repair

In **Milestone 2**, we tested whether guiding the model through an explicit 8-stage financial workflow could prevent errors before submission.

**Milestone 3** tests a complementary reliability hypothesis:

> **Research Question**: If the model is shown machine-readable, deterministic grader diagnostics after its first attempt, can it reliably repair its own financial errors in exactly one revision?

---

## 1. The Distinction: Prevention vs. Repair

| Milestone | Strategy | Workflow | Core Question |
|---|---|---|---|
| **Milestone 2 (Structured Analyst)** | **Error Prevention** | 1 Call (Structured Prompt $\rightarrow$ Submission) | *Can structured reasoning eliminate errors before they happen?* |
| **Milestone 3 (Feedback Repair)** | **Deterministic Repair** | 2 Calls (Structured Call $\rightarrow$ Grade $\rightarrow$ Feedback $\rightarrow$ Repair Call) | *Can invariant diagnostics guide the model to fix its own errors?* |

### Why This Matters in Real Financial Systems

In enterprise financial engineering, models inevitably make errors on complex multi-schedule valuation tasks. Anticipating every possible failure mode in upfront prompt instructions is expensive, token-heavy, and fragile.

In real systems, it is often far cheaper and more reliable to:
1. Allow the analyst to produce an initial model;
2. Run fast, deterministic Python graders to verify internal arithmetic and accounting invariants;
3. Provide targeted diagnostic feedback to the model only when an invariant is violated;
4. Allow exactly one focused revision call to repair the specific discrepancies.

---

## 2. Milestone 3 Architecture & Lifecycle

Each Milestone 3 trial follows a strictly controlled two-stage execution lifecycle:

```text
                 Northstar Sources
                         │
                         ▼
        Call 1: Structured Analyst Completion
                         │
                         ▼
                 Initial Submission
                         │
                         ▼
             Deterministic Python Graders
                         │
         ┌───────────────┴───────────────┐
         │ (0 Hard Failures)             │ (≥ 1 Hard Failures)
         ▼                               ▼
    Already Clean                 Build Diagnostic
  (Skip 2nd Call)                 Feedback Prompt
         │                               │
         │                               ▼
         │                 Call 2: One Model Revision
         │                               │
         │                               ▼
         │                      Repaired Submission
         │                               │
         │                               ▼
         │                  Deterministic Python Graders
         │                               │
         └───────────────┬───────────────┘
                         │
                         ▼
             Record Both Artifacts &
         Diagnostic Transition Metrics
```

---

## 3. Strict Zero Gold-Leakage Policy

A critical requirement in benchmark evaluation is preventing the evaluation harness from leaking ground-truth answers during feedback.

If the harness provides the correct numerical answer (e.g. `Expected: 1712.97`), the experiment degenerates into testing whether the model can copy a string.

### How Milestone 3 Prevents Gold Leakage:
1. **Invariant-Only Feedback**: The repair prompt provides only the **violated mathematical/accounting rule** and the model's **own submitted number**.
2. **No Hidden Benchmark Constants**: The prompt never reveals ground-truth enterprise values, equity bridges, WACCs, or benchmark share prices.
3. **Cascade Warning**: The prompt explicitly warns the model that repairing an upstream input (e.g. UFCF or WACC) cascades into all downstream schedules and requires full recomputation.

### Example Diagnostic Block Received by the Model:

```text
- **DIAGNOSTIC**: `TV_NOT_DISCOUNTED`
  - Severity: `critical`
  - Affected Metric: `pv_terminal_value`
  - Your Submitted Value: `1290.60`
  - Violated Invariant & Correction Rule: Terminal value must be discounted back to valuation date (t=0): PV(TV) = TV / (1 + WACC)^n. Do not add undiscounted TV directly to Enterprise Value.
```

---

## 4. Full Artifact Preservation

Every trial preserves both initial and repaired outputs under its self-contained run folder:

```text
results/
└── milestone-3/
    └── m3-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_120000/
        ├── config.json
        ├── prompt.txt
        ├── run_001/
        │   ├── initial_raw_response.txt
        │   ├── initial_submission.json
        │   ├── initial_grade.json
        │   ├── repair_prompt.txt          # (if repair was attempted)
        │   ├── repair_raw_response.txt    # (if repair was attempted)
        │   ├── repaired_submission.json   # (if repair succeeded)
        │   ├── repaired_grade.json        # (if repair succeeded)
        │   ├── submission.json            # (final effective submission)
        │   ├── grade.json                 # (final effective grade)
        │   └── metadata.json
        ├── summary.json
        └── summary.md
```

---

## 5. Primary Metric: Repair Success Rate

Milestone 3 measures whether deterministic feedback successfully converts failing runs into clean runs.

$$\text{Repair Success Rate} = \frac{\text{Initially Failing Parsed Runs with } 0 \text{ Hard Failures after Repair}}{\text{Total Initially Failing Parsed Runs}}$$

### Diagnostic Transition Categories:
For each diagnostic code, the harness tracks:
- **Resolved**: Present in initial attempt, absent in repaired attempt ($\Delta = \text{Fixed}$).
- **Persistent**: Present in both initial and repaired attempts ($\Delta = \text{Unrepaired}$).
- **Newly Introduced**: Absent in initial attempt, introduced during revision ($\Delta = \text{Cascade Error}$).

---

## 6. Running Milestone 3 Experiments

### 3-Run Smoke Test (Offline Mock)

```bash
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider mock \
  --mode repair \
  --runs 3 \
  --execute
```

### 3-Run Smoke Test (DeepSeek V4 Flash)

```bash
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode repair \
  --thinking on \
  --reasoning-effort high \
  --runs 3 \
  --execute
```

### 10-Run Benchmark Experiment

```bash
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode repair \
  --thinking on \
  --reasoning-effort high \
  --runs 10 \
  --execute
```

> **Default Output Directory**: In repair mode (`--mode repair`), results automatically save to `results/milestone-3/`. Use `--output <custom_dir>` to specify an alternative path.

---

## 7. Comparing Milestone 2 vs. Milestone 3

To quantify the exact value of deterministic feedback repair over the structured single-call baseline:

```bash
uv run ib-eval compare \
  results/milestone-2/m2-structured-deepseek-deepseek-v4-flash-thinking-high-... \
  results/milestone-3/m3-repair-deepseek-deepseek-v4-flash-thinking-high-...
```

The comparison report highlights:
- Score improvements and hard-failure reduction;
- Specific diagnostic resolution rates (e.g. whether `TV_NOT_DISCOUNTED` fell from 80% to 0%);
- Latency and token overhead from the second model call.

---

## Quick Navigation

- Previous: **[Chapter 07 — Structured Analyst](07_structured_analyst.md)**
- Next: **[Chapter 06 — Where This Can Go](06_where_this_can_go.md)**
- Benchmark Root: **[README.md](../README.md)**
