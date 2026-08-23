# Chapter 09 — Milestone 3B: Controlled Repair Benchmark

In **Milestone 3**, we tested whether a frontier model could repair naturally occurring errors during generation trials. However, when evaluating strong models with structured reasoning (e.g. `deepseek-v4-flash` with high reasoning effort), initial failure rates are low (e.g. only 1 out of 10 trials emitted a hard failure).

While low baseline error rates are desirable, a single failure trial is insufficient to characterize how reliably a model repairs different **classes** of financial errors.

**Milestone 3B** introduces a controlled evaluation harness to answer a stronger research question:

> **Research Question**: Given a known financial failure mode and deterministic diagnostic feedback, can the model reliably repair the error in exactly one revision without introducing new errors?

---

## 1. Isolating Repair from Generation

| Milestone | Initial Starting State | Denominator | Core Isolation |
|---|---|---|---|
| **Milestone 3 (Random Repair)** | Uncontrolled initial generation | Natural model errors (~1–2 per 10 runs) | Evaluates end-to-end multi-turn pipeline |
| **Milestone 3B (Controlled Repair)** | 10 Deliberately corrupted fixtures | Deterministic set of 10 error classes | **Isolates repair capability from initial generation quality** |

By using the benchmark's standardized corrupted fixtures as controlled starting states, every trial tests a specific financial failure mode with guaranteed denominator coverage.

---

## 2. The 10 Controlled Repair Scenarios

The benchmark exercises 10 distinct error modes across 7 error categories and 2 propagation difficulty tiers:

| ID | Fixture Name | Target Diagnostic | Category | Difficulty | Description |
|:---:|---|---|---|:---:|---|
| `c01` | Quarterly Revenue Confusion | `REV_QUARTERLY_CONFUSION` | Valuation | Propagating | Uses Q2 quarterly revenue ($281.0M) instead of FY2025A base ($1,000.0M). |
| `c02` | Terminal Value Not Discounted | `TV_NOT_DISCOUNTED` | Valuation | Propagating | Adds undiscounted horizon TV directly to Enterprise Value without discounting. |
| `c03` | Cash Subtracted in Bridge | `EQ_BRIDGE_CASH_REVERSED` | Accounting Bridge | Propagating | Subtracts cash from gross debt in equity bridge (adding to net debt). |
| `c04` | Debt Omitted from Bridge | `EQ_BRIDGE_DEBT_OMITTED` | Accounting Bridge | Propagating | Omits net debt deduction, equating Enterprise Value directly to Equity Value. |
| `c05` | N/M Peer Coerced to Zero | `COMPS_NM_COERCED_ZERO` | Comps | Local | Coerces negative EBITDA peer multiple to 0.0x instead of excluding from median. |
| `c06` | Fabricated Guidance | `SF_GUIDANCE_FABRICATED` | Source Fidelity | Local | Classifies analyst revenue growth assumption as direct management guidance. |
| `c07` | EBITDA Inconsistency | `MARGIN_EBIT_INCONSISTENCY` | Arithmetic | Propagating | EBIT forecast does not equal EBITDA minus D&A across forecast periods. |
| `c08` | Capex Double Counted | `FCF_CAPEX_DOUBLE_COUNTED` | Formula | Propagating | Capex subtracted twice in the Unlevered Free Cash Flow forecast schedule. |
| `c09` | Headline / Schedule Mismatch | `CONSISTENCY_HEADLINE_DCF` | Consistency | Local | Headline DCF valuation outputs do not match underlying detailed DCF schedules. |
| `c10` | Pre-Tax Cost of Debt in WACC | `WACC_PRETAX_DEBT` | Formula | Propagating | Uses pre-tax cost of debt in WACC without applying corporate interest tax shield. |

---

## 3. Controlled Repair Lifecycle

Each controlled trial executes exactly **one model revision call**:

```text
                  Northstar Source Packet
                             │
                             ▼
              Load Corrupted Fixture (c01–c10)
                             │
                             ▼
                Deterministic Python Graders
                             │
                             ▼
            Verify Target Diagnostic is Emitted
             (Fails loudly on benchmark drift)
                             │
                             ▼
             Build Invariant Feedback Prompt
              (Strict zero gold-leakage policy)
                             │
                             ▼
             One Model Revision Call (1 Shot)
                             │
                             ▼
                     Repaired Submission
                             │
                             ▼
                Deterministic Python Graders
                             │
                             ▼
            Audit Target Resolution & Regressions
```

### Benchmark Drift Protection
Before generating the repair prompt, the harness grades the initial corrupted fixture and verifies that its expected diagnostic code is emitted. If benchmark changes or schema modifications ever cause a fixture not to emit its intended diagnostic, the harness raises a `BenchmarkDriftError` and halts immediately.

---

## 4. Key Evaluation Metrics

### 1. Controlled Repair Success Rate (Primary Metric)
$$\text{Controlled Repair Success Rate} = \frac{\text{Fixtures with Target Diagnostic Resolved AND } 0 \text{ Hard Failures Remaining}}{\text{Total Fixtures Attempted}}$$

### 2. Target Diagnostic Resolution Rate
$$\text{Target Resolution Rate} = \frac{\text{Fixtures where Target Diagnostic Disappeared}}{\text{Total Fixtures Attempted}}$$

> **Important Distinction**: A model may successfully fix the targeted error (e.g. apply tax shield to cost of debt in WACC) but introduce an arithmetic error in the subsequent share price calculation. Target resolution tracks local correction; Controlled Repair Success tracks end-to-end model integrity.

### 3. New Error Introduction Rate (Regression / Cascade Metric)
$$\text{New Error Introduction Rate} = \frac{\text{Fixtures where Repair Introduced } \ge 1 \text{ New Diagnostic}}{\text{Total Fixtures Attempted}}$$

---

## 5. Local vs. Propagating Repair Analysis

A key research insight from Milestone 3B is the distinction in repair difficulty:

- **Local Repairs** (`c05`, `c06`, `c09`): Affect only 1–2 isolated fields without altering other financial schedules (e.g. changing provenance classification from `direct` to `analyst_assumption`, or aligning headline summary numbers).
- **Propagating Repairs** (`c01`, `c02`, `c03`, `c04`, `c07`, `c08`, `c10`): Upstream corrections that cascade through the entire valuation model. For example, correcting a WACC formula requires recalculating all 5 discount factors, PV(UFCF), PV(TV), Enterprise Value, Net Debt, Equity Value, and Implied Share Price.

The benchmark report groups and compares repair success rates across these two tiers.

---

## 6. Running the Controlled Repair Benchmark

### Targeted 3-Fixture Smoke Test (Propagating Repairs)
Exercises WACC, Capex, and Terminal Value discounting:

```bash
uv run ib-eval repair-benchmark \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --thinking on \
  --reasoning-effort high \
  --fixtures c02,c08,c10 \
  --execute
```

### Full 10-Fixture Benchmark

```bash
uv run ib-eval repair-benchmark \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --thinking on \
  --reasoning-effort high \
  --fixtures all \
  --execute
```

> **Default Output Directory**: Controlled repair runs automatically save under `results/milestone-3b/`. Use `--output <custom_dir>` to specify an alternative directory.

---

## 7. Artifact Organization

Every trial preserves both initial corrupted inputs and repaired outputs in its own subfolder:

```text
results/
└── milestone-3b/
    └── m3b-controlled-repair-deepseek-deepseek-v4-flash-thinking-high-20260822_190000/
        ├── config.json
        ├── summary.json
        ├── summary.md
        ├── c01/
        │   ├── initial_submission.json
        │   ├── initial_grade.json
        │   ├── repair_prompt.txt
        │   ├── repair_raw_response.txt
        │   ├── repaired_submission.json
        │   ├── repaired_grade.json
        │   └── metadata.json
        ├── c02/
        ├── c03/
        └── ...
```

---

## 8. Statistical Framing

With 10 controlled fixtures, this benchmark provides **deterministic coverage across known classes of investment-banking failure modes**, rather than population-level statistical inference. It provides an objective baseline for measuring single-revision repair robustness.

---

## Quick Navigation

- Previous: **[Chapter 08 — Deterministic Feedback Repair](08_deterministic_feedback_repair.md)**
- Next: **[Chapter 06 — Where This Can Go](06_where_this_can_go.md)**
- Benchmark Root: **[README.md](../README.md)**
