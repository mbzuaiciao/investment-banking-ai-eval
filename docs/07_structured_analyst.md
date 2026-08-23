# Chapter 07 — Milestone 2: Structured Analyst

In Milestone 1, we established the **Direct Analyst Baseline** to answer a fundamental question: *How reliably can a frontier model complete a multi-step investment banking valuation when given only the raw source packet and a target schema?*

Milestone 2 takes the next step on our experimental ladder:

> **Research Hypothesis**: Does imposing an explicit, stage-by-stage financial analysis workflow reduce critical valuation errors relative to the direct analyst baseline, while holding the model, case packet, and single-call constraint constant?

---

## 1. The Experimental Ladder

To build trustworthy financial AI, we must isolate what improves performance at each layer of system complexity:

```text
Milestone 0: Deterministic Benchmark
   └── Ground-truth DCF/Comps, 10 Python graders, 0 LLM calls

Milestone 1: Direct Analyst Baseline
   └── Raw source packet → Single prompt → Direct JSON submission

Milestone 2: Structured Analyst (This Milestone)
   └── Raw source packet → 8-Stage structured reasoning workflow → Single JSON submission

Milestone 3 (Future): Tool-Augmented & Verifier Loops
   └── Code execution, Python sandboxes, deterministic grader feedback loops
```

### The Milestone 2 Experimental Control

To ensure a valid scientific comparison between Milestone 1 and Milestone 2:
1. **Identical Case Data**: Both modes read the exact same 4 markdown source files in `cases/northstar-v1/sources/`.
2. **Identical Target Schema**: Both modes produce the exact same canonical `Submission` JSON format.
3. **Single Completion Constraint**: Exactly **one LLM call per trial**. No retries, no second-pass repair, no multi-agent debates, and no grader feedback.
4. **Matched Model Settings**: Both modes run against the identical model and reasoning configuration (e.g. `deepseek-v4-flash` with `--thinking on --reasoning-effort high`).

The **only variable** is the prompt structure: direct schema request vs. 8-stage explicit financial reasoning.

---

## 2. The 8-Stage Financial Analysis Workflow

Direct prompting frequently leads models to calculate terminal values without discounting, confuse quarterly run-rates with full-year revenue, or misapply capital structure bridges.

The Structured Analyst prompt guides the model through an explicit 8-stage financial workflow:

```text
Stage 1: Source Extraction & Fact Provenance
   │   (Classify direct facts vs derived vs analyst assumptions)
   ▼
Stage 2: Assumption Ledger
   │   (Explicitly state all growth, margin, WACC, and TV inputs)
   ▼
Stage 3: 5-Year Forecast Schedules (2026E–2030E)
   │   (Revenue, EBITDA, EBIT, NOPAT, Capex, ΔNWC, UFCF)
   ▼
Stage 4: WACC Derivation
   │   (Ke via CAPM, Kd after-tax, target capital structure weights)
   ▼
Stage 5: Terminal Value Calculation & PV Discounting
   │   (Gordon Growth TV at horizon AND discount factor at t=5)
   ▼
Stage 6: Enterprise Value & Equity Bridge
   │   (EV = Sum PV(UFCF) + PV(TV); Equity = EV - Net Debt; Share Price)
   ▼
Stage 7: Comparable Companies Analysis (Trading Comps)
   │   (Exclude N/M peers from median; disclose fiscal year mismatches)
   ▼
Stage 8: Final Invariant Pre-Submission Self-Check
   │   (12-point internal consistency checklist before emitting JSON)
   ▼
Canonical Submission JSON
```

### Why Each Stage Exists

| Stage | Target Failure Mode in Direct Baseline | Mechanism |
|---|---|---|
| **1. Source Extraction** | `SF_GUIDANCE_FABRICATED`<br>`SF_MISSING_PROVENANCE` | Forces explicit provenance tagging before numbers are entered into schedules. |
| **2. Assumption Ledger** | `REV_GROWTH_OUT_OF_RANGE`<br>`UNSUPPORTED_ASSUMPTION` | Prevents the model from fabricating management guidance. |
| **3. Forecast Schedules** | `REV_ARITHMETIC`<br>`FCF_UFCF_ERROR`<br>`FCF_NWC_DELTA_ERROR` | Mandates year-by-year reconciliation ($UFCF = NOPAT + D\&A - Capex - \Delta NWC$). |
| **4. WACC Derivation** | `WACC_PRETAX_DEBT`<br>`WACC_WEIGHTS_ERROR` | Explicitly computes CAPM $K_e$, after-tax $K_d \times (1 - t)$, and weight normalization. |
| **5. Terminal Value** | `TV_NOT_DISCOUNTED`<br>`TV_FORMULA_ERROR`<br>`TV_PV_ERROR` | Enforces explicit two-step calculation: $TV_{T=5} = \frac{UFCF_{2030E} \times (1+g)}{WACC - g}$ followed by $PV(TV) = \frac{TV}{(1+WACC)^5}$. |
| **6. Equity Bridge** | `EQ_BRIDGE_CASH_REVERSED`<br>`EQ_BRIDGE_DEBT_OMITTED` | Reminds the model that $Net\ Debt = Gross\ Debt - Cash$, preventing cash additions to debt. |
| **7. Trading Comps** | `COMPS_NM_COERCED_ZERO`<br>`COMPS_MEDIAN_ERROR` | Instructs the model to exclude non-meaningful ($N/M$) multiples rather than coercing them to $0.0\times$. |
| **8. Invariant Checklist** | `CONSISTENCY_HEADLINE_DCF`<br>`CONSISTENCY_SHARES` | Final self-verification check across headline and detailed model outputs. |

---

## 3. Reporting Fix: Occurrence Count vs. Run-Level Incidence

In Milestone 1, repeated diagnostics within a single run (e.g. four consecutive years of UFCF formula errors in run 1) could produce percentages over 100% when dividing total occurrences by total runs.

In Milestone 2, our reporting system separates diagnostic statistics into two distinct, rigorous metrics:

1. **Occurrence Count**: Total number of diagnostic events across all runs (e.g., `FCF_UFCF_ERROR: 36 occurrences`).
2. **Run-Level Incidence**: Number and percentage of parsed runs containing **at least one** occurrence of that diagnostic (e.g., `9 / 10 runs (90.0%)`).

This guarantees that run-level incidence is strictly bounded between $0.0\%$ and $100.0\%$ while preserving raw event volume in `summary.json` and `summary.md`.

---

## 4. Running Experiments

### Running a 3-Run Smoke Test

To verify structured analyst execution end-to-end on DeepSeek V4 (automatically outputs to `results/milestone-2/`):

```bash
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode structured \
  --thinking on \
  --reasoning-effort high \
  --runs 3 \
  --execute
```

> **Note on Output Directories**: In structured mode (`--mode structured`), results automatically default to `results/<case_id>/<stage>/` (e.g. `results/northstar-v1/milestone-2/` or `results/meridian-v1/milestone-4d-structured/`). Supplying an explicit `--output <dir>` overrides this default.

### Running the Full 10-Run Benchmark

For statistically robust evaluation (defaults to `results/northstar-v1/milestone-2/`):

```bash
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode structured \
  --thinking on \
  --reasoning-effort high \
  --runs 10 \
  --execute
```

---

## 5. Comparing Direct vs. Structured Baselines

The benchmark includes a side-by-side comparison utility (`ib-eval compare`):

```bash
uv run ib-eval compare \
  results/milestone-1/m1-direct-deepseek-deepseek_v4_flash-thinking-high-... \
  results/milestone-2/m2-structured-deepseek-deepseek_v4_flash-thinking-high-...
```

The comparison command outputs:
- **Summary Metrics Delta**: Mean score, median score, score standard deviation, parse rate, and hard-failure rate.
- **Diagnostic Run-Level Incidence Delta**: Shifts in specific failure modes (e.g., whether `TV_NOT_DISCOUNTED` dropped from 80% to 0%).
- **Grader Pass Rate Delta**: Individual pass rate improvements across all 10 deterministic graders.

---

## Quick Navigation

- Previous: **[Chapter 06 — Where This Can Go](06_where_this_can_go.md)**
- Benchmark Root: **[README.md](../README.md)**
