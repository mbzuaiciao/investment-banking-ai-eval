# Investment Banking AI Eval

> **The benchmark does not ask only whether an AI produced the right valuation.
> It asks whether the financial process producing that valuation is defensible.**

A deterministic, typed evaluation harness for assessing AI systems on
investment-banking financial analysis tasks. Built around the fictional
**Northstar Components, Inc.** case.

---

## Tutorial / Learning Guide

New to the project? Start with the step-by-step learning lab:
👉 **[docs/README.md](docs/README.md)**

The tutorial covers both the core investment-banking concepts (DCF math, WACC derivation, trading comps, net debt bridges) and the AI-evaluation architecture (deterministic grading, diagnostic taxonomy, baseline experiments).

---

## Experimental Results

Empirical results across Milestones 1–3B on the Northstar benchmark:

| Experiment | Workflow Configuration | Sample Size | Parse Success | Mean Score | Hard-Failure Rate | Key Empirical Result |
|---|---|:---:|:---:|:---:|:---:|---|
| **M1 Direct (Thinking Off)** | Zero reasoning; direct prompt | 10 runs | 90% (9/10) | 90.5 | 100% *(of parsed)* | Broad formula & arithmetic failures; 0% pass on FCF & TV |
| **M1 Direct (Thinking High)** | High reasoning; direct prompt | 10 runs | 100% (10/10) | 97.2 | 100% | Core arithmetic improved; systematic TV discounting error on 10/10 runs |
| **M2 Structured Workflow** | High reasoning; 8-stage decomposition | 10 runs | 100% (10/10) | 99.0 | 30% | TV discounting defect eliminated (100% pass); hard failures reduced to 30% |
| **M3 Feedback Repair** | Structured prompt + conditional repair | 10 runs | 100% (10/10) | 98.8 *(final)* | 0% *(final)* | 9 clean runs skipped; 1/1 natural failure cleanly repaired ($n=1$) |
| **M3B Controlled Repair** | 10 Corrupted fixtures + 1-shot repair | 10 fixtures | 100% (10/10) | 100.0 *(final)* | 0% *(final)* | 10/10 target errors resolved; 0 regressions across local & propagating tiers |

### Key Findings at a Glance:
1. **Reasoning alone does not eliminate systematic defects**: Extended thinking lifted mean score to 97.2 but still produced valuation-breaking TV discounting errors on 100% of direct prompt runs.
2. **Explicit domain workflow eliminates structural omissions**: Decomposing analysis into 8 financial stages lifted TV pass rates from 0% to 100% and reduced hard failures to 30%.
3. **Deterministic invariant feedback enables 1-shot self-repair**: Invariant diagnostics without gold leakage cleanly repaired residual errors in live generation and across all 10 controlled failure modes.
4. **Aggregate scores conceal valuation-breaking flaws**: Models scoring in the high 90s still embedded $200M+ enterprise value errors.

📖 **Read the full research synthesis & methodology**: **[Chapter 10 — Experimental Results & Research Synthesis](docs/10_results_and_findings.md)**  
📂 **Inspect raw experiment artifacts**: **[results/README.md](results/README.md)**

---

## What this benchmark evaluates

Investment banking analysis involves a chain of decisions: selecting source
data, interpreting qualitative guidance, building a financial model, and
translating that model into a valuation conclusion.

Each step can fail in distinct ways:

| Failure type | Example |
|---|---|
| **Arithmetic error** | NOPAT = EBIT × (1 + tax) instead of × (1 − tax) |
| **Formula error** | WACC computed without the tax shield on debt |
| **Accounting inconsistency** | EBIT ≠ EBITDA − D&A |
| **Source error** | Q2 quarterly revenue used as full-year annual revenue |
| **Provenance fabrication** | Claiming management stated exactly 8% growth |
| **Valuation error** | Terminal value not discounted to present value |
| **Cross-artifact inconsistency** | Headline share price differs from model output |

An AI that fluently writes financial prose can still commit every one of
these errors. This benchmark evaluates whether the *financial process* is
correct, not whether the output reads well.

---

## Why financial correctness differs from fluent financial writing

A large language model can produce text that *sounds* like a professional
investment-banking memo — complete with appropriate hedging language, correct
terminology, and structurally coherent prose — while embedding material
computational errors.

Consider:
- A model that writes "we derive a WACC of 9.3%" but applies the pre-tax
  cost of debt (failing to apply the tax shield) will produce a subtly wrong
  discount rate that inflates the DCF enterprise value.
- A model that writes "management guided to 8% growth" when management only
  stated "high single digits" has fabricated a fact — even if 8% is a
  defensible assumption.

Deterministic graders can catch these errors mechanically; a human reading
the output might not notice.

---

## Three dimensions of correctness

This benchmark distinguishes three orthogonal dimensions:

### 1. Mathematical correctness
Is the arithmetic right? Does EBIT = EBITDA − D&A? Does UFCF equal
NOPAT + D&A − Capex − ΔNWC? Is the terminal value discounted?

These have objectively correct answers. The graders check them without tolerance.

### 2. Financial reasonableness
Are the assumptions defensible? A 2026E revenue growth rate of 8% is
reasonable given "high single digits" guidance. A rate of 20% is not.

The benchmark allows judgment differences within defensible ranges and does
not penalize reasonable assumption choices.

### 3. Evidentiary support
Is each assumption traceable to a source? Is the source correctly interpreted?
Is a qualitative statement correctly classified as such, rather than being
treated as a precise numerical commitment?

The provenance system tracks this dimension explicitly.

---

## The Northstar Components, Inc. case

**Industry**: Industrial components  
**Valuation date**: June 30, 2026  
**Units**: USD millions (except per-share values)

### Historical financials

| Metric | 2023A | 2024A | 2025A |
|---|---|---|---|
| Revenue | 820.0 | 905.0 | 1,000.0 |
| EBITDA | 131.2 | 149.3 | 165.0 |
| EBITDA margin | 16.0% | 16.5% | 16.5% |
| D&A | 32.8 | 36.2 | 40.0 |
| EBIT | 98.4 | 113.1 | 125.0 |
| Capex | 36.9 | 40.7 | 45.0 |
| NWC | 98.4 | 108.6 | 120.0 |

### Gold DCF assumptions

| Parameter | Value |
|---|---|
| 2026E revenue growth | 8.0% (analyst interpretation of "high single digits") |
| EBITDA margins | 17.0% → 18.5% (2026–2030E) |
| D&A | 4.0% of revenue |
| Capex | 4.5% of revenue |
| NWC | 12.0% of revenue |
| Tax rate | 25% |
| Risk-free rate | 4.1% |
| Beta | 1.18 |
| ERP | 5.5% |
| Pre-tax cost of debt | 6.2% |
| Equity weight | 78% |
| Debt weight | 22% |
| **WACC** | **9.2832%** |
| Terminal growth | 2.5% |

### Gold headline valuation (code-derived)

The exact values below are computed from first principles by the DCF engine.
They may differ slightly from the approximate values in the specification due
to full-precision floating-point arithmetic; the code-derived values are canonical.

Run `uv run python cases/northstar-v1/ground_truth/generate_gold.py` to see
the precise outputs.

Approximate values per spec:
- DCF enterprise value: ~$1,713mm
- DCF equity value: ~$1,388mm
- DCF implied share price: ~$23.13
- Comps NTM median: 8.2x
- Comps equity value: ~$1,180.5mm
- Comps implied share price: ~$19.68

### Deliberate source traps

The case contains eight deliberate traps that test extraction accuracy:

1. **Quarterly/YTD confusion**: Q2 revenue ($281mm) and H1 revenue ($535mm) both appear in sources
2. **EBITDA definition**: Management references "adjusted EBITDA"; historical uses GAAP EBIT + D&A
3. **High-single-digit guidance**: Management never states exactly 8%
4. **Restructuring charge**: $9mm 2025 charge may or may not be normalized
5. **Convertible debt**: $75mm convertible — treatment must be explicit
6. **N/M peer**: Evergreen Controls has negative EBITDA; must not be assigned zero
7. **Fiscal-year mismatch**: Crestline Systems has Sep 30 FY end
8. **Capex terminology**: "Capital investment" (guidance) = "purchases of PP&E" (cash flow statement)

---

## How to run the benchmark

### Prerequisites

- Python 3.12+
- `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

```bash
uv sync --all-groups
```

### Grade the gold submission

```bash
uv run ib-eval grade examples/gold_submission
```

Expected output:
```
100 / 100
```

### Grade a custom submission

```bash
uv run ib-eval grade path/to/your/submission/
```

The submission directory must contain a `submission.json` conforming to
the `Submission` schema defined in `src/ib_eval/schemas.py`.

### Run tests

```bash
uv run pytest
```

### Lint and type-check

```bash
uv run ruff check .
uv run pyright
```

### Regenerate gold submission

```bash
uv run python cases/northstar-v1/ground_truth/generate_gold.py
```

### Run all corrupted fixtures

```bash
for d in examples/corrupted/*/; do
  echo "--- $d ---"
  uv run ib-eval grade "$d" --quiet
done
```

---

## Repository structure

```
investment-banking-ai-eval/
├── pyproject.toml
├── cases/northstar-v1/
│   ├── case.yaml          # Case metadata
│   ├── rubric.yaml        # Grader weights and tolerances
│   ├── sources/           # Synthetic source documents (with traps)
│   └── ground_truth/      # Gold submission generator
├── src/ib_eval/
│   ├── cli.py             # CLI entry point
│   ├── schemas.py         # Pydantic submission schema
│   ├── dcf.py             # DCF engine (explicit formulas)
│   ├── comps.py           # Trading comps engine
│   ├── provenance.py      # Provenance helpers
│   ├── case.py            # Case/rubric loader
│   ├── scoring.py         # Aggregator
│   └── graders/           # 10 deterministic graders
├── examples/
│   ├── gold_submission/   # Perfect-score submission
│   └── corrupted/         # One fixture per error class
└── tests/                 # Comprehensive test suite
```

---

---

## Milestone 1: Direct Analyst Baseline

The **Direct Analyst Baseline** establishes an uncontrolled baseline for how reliably frontier models can complete the Northstar investment-banking case unaided.

```text
Northstar source packet
        ↓
single analyst prompt (sources + schema)
        ↓
one model completion
        ↓
submission parser
        ↓
deterministic Milestone 0 graders
        ↓
run artifacts + aggregate statistics
```

### Baseline Purity Principles

1. **Single substantive call**: No critics, verifiers, reflection stages, or multi-turn loops.
2. **Strict parse handling**: If the model output cannot be parsed into the submission schema, it is recorded as a real run failure (`parse_failure`) without automated repair prompts.
3. **Zero benchmark leakage**: The prompt contains only the case background, source documents, and the output schema. It contains no ground-truth answers, diagnostic codes, tolerances, or scoring hints.
4. **Repeated independent trials**: Because a single run is insufficient evidence of reliability, the experiment runner executes repeated trials to compute mean score, variance, hard-failure rates, and diagnostic code distributions.
5. **Parsing vs. grading abstraction boundary**: *Parsing validates representability; deterministic graders validate financial correctness.* Submissions with incorrect financial arithmetic parse successfully so deterministic graders can diagnose and classify the exact failure mode rather than conflating model errors with parser failures.

### Running the Baseline

Set your provider API key:

```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For DeepSeek
export DEEPSEEK_API_KEY="sk-..."
```

#### 1. Dry-run inspection (Cost guardrail)

By default, running without `--execute` prints the experiment configuration without making paid calls:

```bash
# OpenAI dry run
uv run ib-eval baseline --case northstar-v1 --provider openai --model <model-name> --runs 5

# DeepSeek V4 Flash (thinking disabled)
uv run ib-eval baseline --case northstar-v1 --provider deepseek --model deepseek-v4-flash --thinking off --runs 3

# DeepSeek V4 Flash (thinking enabled with high reasoning effort)
uv run ib-eval baseline --case northstar-v1 --provider deepseek --model deepseek-v4-flash --thinking on --reasoning-effort high --runs 3
```

#### 2. Execute live trials

Add `--execute` to run live trials:

```bash
# OpenAI live run
uv run ib-eval baseline --case northstar-v1 --provider openai --model <model-name> --runs 5 --execute

# DeepSeek V4 Flash (cheap direct baseline, thinking off)
uv run ib-eval baseline --case northstar-v1 --provider deepseek --model deepseek-v4-flash --thinking off --runs 3 --execute

# DeepSeek V4 Flash (thinking on)
uv run ib-eval baseline --case northstar-v1 --provider deepseek --model deepseek-v4-flash --thinking on --reasoning-effort high --runs 3 --execute

# DeepSeek V4 Pro (stronger comparison model)
uv run ib-eval baseline --case northstar-v1 --provider deepseek --model deepseek-v4-pro --thinking on --reasoning-effort high --runs 3 --execute
```

Optional parameters:
- `--mode [direct|structured]`: Experiment mode (`direct` for Milestone 1, `structured` for Milestone 2)
- `--thinking [on|off]`: Enable or disable thinking / reasoning mode
- `--reasoning-effort [low|medium|high]`: Level of reasoning effort when thinking is enabled
- `--temperature <float>`: Sampling temperature (e.g. `0.2`)
- `--seed <int>`: Random seed
- `--output <dir>`: Custom output folder (defaults to case-scoped directory: `results/<case_id>/<stage>`; explicit `--output` overrides defaults)

### Experiment Artifacts

Each experiment creates a self-contained directory under the case-scoped hierarchy:

```text
results/
└── northstar-v1/
    └── milestone-1/
        └── m1-direct-openai-<model-name>-20260821_120000/
            ├── config.json
            ├── prompt.txt
            ├── run_001/
            │   ├── raw_response.txt
            │   ├── submission.json
            │   ├── grade.json
            │   └── metadata.json
            ├── run_002/
            │   ├── raw_response.txt
            │   ├── parse_error.json
            │   └── metadata.json
            ├── summary.json
            └── summary.md
```

`summary.json` and `summary.md` aggregate:
- Completed calls, parsed runs, parse failure counts, and parse success rates;
- Mean, median, min, max, and standard deviation of benchmark scores;
- Hard-failure run counts and rates;
- Raw diagnostic occurrence counts and run-level incidence percentages (strictly bounded in [0%, 100%]);
- Grader-by-grader pass rates and mean scores.

---

## Milestone 2: Structured Analyst

The **Structured Analyst** tests the hypothesis:
> *Does imposing an explicit, stage-by-stage financial analysis workflow reduce critical errors relative to the direct baseline under an identical single-call constraint?*

```text
Northstar source packet
        ↓
8-stage financial reasoning workflow
  (Extraction → Assumptions → Forecasts → WACC → TV → Bridge → Comps → Invariant Checks)
        ↓
one model completion
        ↓
submission parser
        ↓
deterministic graders
```

### Running the Structured Analyst

Use `--mode structured` with the `baseline` command:

```bash
# DeepSeek V4 Flash 3-run smoke test (Structured mode)
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode structured \
  --thinking on \
  --reasoning-effort high \
  --runs 3 \
  --execute

# DeepSeek V4 Flash 10-run structured experiment
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode structured \
  --thinking on \
  --reasoning-effort high \
  --runs 10 \
  --output results/milestone-2 \
  --execute
```

### Comparing Direct vs. Structured Baselines

Use the built-in `compare` command to generate a side-by-side comparative analysis between any two experiment summaries:

```bash
uv run ib-eval compare \
  results/milestone-1/m1-direct-deepseek-deepseek_v4_flash-thinking-high-... \
  results/milestone-2/m2-structured-deepseek-deepseek_v4_flash-thinking-high-...
```

The report highlights deltas in mean/median scores, standard deviation, parse rates, hard-failure rates, grader pass rates, and individual diagnostic run incidence.

---

## Milestone 3: Deterministic Feedback Repair

The **Feedback Repair** experiment tests the hypothesis:
> *If the model is shown machine-readable deterministic grader diagnostics after its first attempt, can it reliably repair its own financial errors in exactly one revision?*

```text
Northstar source packet
        ↓
structured analyst (Call 1)
        ↓
initial submission → deterministic graders
        ↓
machine-readable diagnostics (Zero gold leakage)
        ↓
one repair revision (Call 2) [skipped if initial is clean]
        ↓
repaired submission → deterministic graders
```

### Running Milestone 3 Repair Experiments

Use `--mode repair` with the `baseline` command:

```bash
# DeepSeek V4 Flash 3-run smoke test (Repair mode)
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode repair \
  --thinking on \
  --reasoning-effort high \
  --runs 3 \
  --execute

# DeepSeek V4 Flash 10-run repair experiment
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --mode repair \
  --thinking on \
  --reasoning-effort high \
  --runs 10 \
  --output results/milestone-3 \
  --execute
```

### Primary Metric: Repair Success Rate

Milestone 3 tracks:
- **Repair Success Rate**: Proportion of initially failing parsed trials repaired to zero hard failures.
- **Diagnostic Transitions**: Resolved, Persistent, and Newly Introduced errors per diagnostic code.
- **Score Delta & Latency/Token Overhead**: Quantitative cost-benefit analysis of the second repair turn.

---

## Milestone 3B: Controlled Repair Benchmark

The **Controlled Repair Benchmark** isolates repair capability from initial generation quality by testing single-revision repair starting from 10 known corrupted fixtures (`c01` through `c10`).

```text
canonical Northstar case
        ↓
known corrupted submission (c01–c10)
        ↓
deterministic graders → verify target diagnostic
        ↓
invariant feedback prompt (Zero gold leakage)
        ↓
one model repair revision
        ↓
repaired submission → deterministic graders
```

### Running the Controlled Repair Benchmark

Use the dedicated `repair-benchmark` command:

```bash
# Targeted 3-fixture smoke test (Propagating repairs: TV discounting, Capex, WACC)
uv run ib-eval repair-benchmark \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --thinking on \
  --reasoning-effort high \
  --fixtures c02,c08,c10 \
  --execute

# Full 10-fixture controlled repair benchmark
uv run ib-eval repair-benchmark \
  --case northstar-v1 \
  --provider deepseek \
  --model deepseek-v4-flash \
  --thinking on \
  --reasoning-effort high \
  --fixtures all \
  --execute
```

### Metrics & Diagnostic Analysis

- **Controlled Repair Success Rate**: Proportion of fixtures repaired to zero hard failures with target resolved.
- **Target Diagnostic Resolution Rate**: Proportion of fixtures where the target diagnostic disappeared.
- **New Error Introduction Rate**: Measures regression and cascade errors introduced during repair.
- **Difficulty Analysis**: Contrasts **local repairs** (comps, provenance, headline) against **propagating repairs** (WACC, Capex, revenue base, TV discounting).

---

## Current limitations

- Two synthetic cases are currently encoded: **Northstar Components** (`northstar-v1`, industrial manufacturing) and **Meridian Cloud Systems** (`meridian-v1`, enterprise SaaS).
- No web UI or interactive dashboard.

---

## Future roadmap

- **Milestone 0**: Deterministic benchmark & grader foundation (Completed)
- **Milestone 1**: Direct analyst baseline (Completed)
- **Milestone 2**: Structured analyst workflow (Completed)
- **Milestone 3**: Deterministic feedback repair (Completed)
- **Milestone 3B**: Controlled repair benchmark (Completed)
- **Milestone 4A**: Second Case Design — Meridian SaaS (Completed)
- **Milestone 4B**: Meridian Benchmark Implementation & Parameterized Graders (Completed)
- **Milestone 4C**: Cross-case empirical baseline & repair trials (Live API)
- **Milestone 5**: Multi-agent verifier loops & iterative collaboration
- **Milestone 6**: Real-world SEC 10-K extraction & Excel workbook generation

---

## Design principles

- **Deterministic**: Graders produce the same result for the same input every time
- **Typed**: All schemas are Pydantic models; all graders are typed Python
- **Inspectable**: Every grader failure includes a diagnostic code and message
- **Tolerant where appropriate**: Judgment differences are not penalized
- **Strict where objective**: Hard failures are always reported

---

*This benchmark is an independent research project. It is not affiliated with
or endorsed by any AI company.*
