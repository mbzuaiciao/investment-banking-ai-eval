# Chapter 05 — Milestone 1: Direct Analyst Baseline

In Milestone 0, we built and verified the deterministic benchmark. In **Milestone 1**, we turn this benchmark into a live AI experiment: the **Direct Analyst Baseline**.

---

## 1. The Research Question

> **"How reliably can a frontier language model complete the Northstar investment-banking task when given only the case source packet and a direct instruction to produce a structured valuation submission?"**

To answer this, we must measure:
- **Average benchmark score**: Does the model score 60, 80, or 95?
- **Score variance**: Does the model produce consistent results across independent runs?
- **Hard-failure rate**: How often does the model commit catastrophic valuation errors (e.g. forgetting to discount terminal value or reversing cash)?
- **Diagnostic distribution**: What specific mistakes does the model make repeatedly?
- **Stochastic vs. systematic failure**: Are errors random flukes or systematic misunderstandings of corporate finance?

---

## 2. The Core Experiment Architecture

The Milestone 1 baseline is intentionally designed with **zero scaffolding**:

```text
Northstar Source Packet (4 Markdown Docs)
                  ↓
       Single Analyst Prompt
                  ↓
       One Model Completion
                  ↓
         Submission Parser
                  ↓
    Deterministic Milestone 0 Graders
                  ↓
 Run Artifacts + Aggregate Statistics
```

### Why Zero Scaffolding?
In AI research, before adding complex multi-agent teams, reflection loops, planning agents, or verifiers, you must establish an **uncontrolled baseline**:
- **No critic model**
- **No verifier model**
- **No self-reflection step**
- **No automated retry on malformed JSON**
- **No planning or dynamic task breakdown**
- **No deterministic grader feedback returned to the model**

> **Scientific Principle**: *"We must know how the model behaves unaided before we can determine whether additional agentic scaffolding genuinely improves reliability."*

---

## 3. Why Repeated Independent Trials Matter

A common trap in AI evaluation is running a single prompt, observing a 95/100 score, and declaring: *"The model has solved investment banking!"*

Large language models are probabilistic systems. A single trial tells you almost nothing about operational reliability:
- Run 1 might score **98 / 100** (clean DCF, proper provenance).
- Run 2 might score **92 / 100** (pre-tax debt cost bug in WACC).
- Run 3 might score **96 / 100** (Evergreen multiple coerced to 0.0x).
- Run 4 might produce **malformed JSON** (parse failure).

By running **10 to 20 repeated trials**, Milestone 1 generates statistically meaningful distributions:
- **Parse success rate**: $18 / 20 = 90.0\%$
- **Mean score**: $84.2 \pm 9.5$
- **Hard-failure rate**: $35.0\%$ (7 of 20 runs committed at least one critical error)
- **Top failure modes**: `SF_GUIDANCE_FABRICATED` (40%), `WACC_PRETAX_DEBT` (20%)

---

## 4. Running the Baseline Experiment

### Prerequisites & API Configuration
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="sk-..."
```

### Cost Guardrail (Dry-Run Mode)
To prevent accidental paid API calls, running without the `--execute` flag performs a dry-run:
```bash
uv run ib-eval baseline --case northstar-v1 --provider openai --model <model-name> --runs 5
```

Output:
```text
==================================================
  IB-Eval — Milestone 1: Direct Analyst Baseline  
==================================================
  Case:        northstar-v1 (Northstar Components, Inc.)
  Provider:    openai
  Model:       <model-name>
  Trials:      5
  Output Dir:  results/milestone-1
--------------------------------------------------

  [DRY-RUN / GUARDRAIL ACTIVE]
  Live provider calls were NOT executed.
  To execute live trials, re-run with the --execute flag:

    uv run ib-eval baseline --case northstar-v1 --provider openai --model <model-name> --runs 5 --output results/milestone-1 --execute
```

### Executing Live Trials
When ready, add the `--execute` flag:
```bash
uv run ib-eval baseline \
  --case northstar-v1 \
  --provider openai \
  --model <model-name> \
  --runs 5 \
  --output results/milestone-1 \
  --execute
```

---

## 5. Experiment Artifacts & Reports

Every experiment run creates a timestamped folder containing complete raw artifacts:

```text
results/
└── milestone-1/
    └── m1-direct-openai-<model-name>-20260821_120000/
        ├── config.json       # Exact model, parameters, git commit, timestamp
        ├── prompt.txt        # Exact prompt presented to the model
        ├── run_001/
        │   ├── raw_response.txt  # Raw string from model
        │   ├── submission.json   # Parsed JSON submission
        │   ├── grade.json        # Complete scoring report & diagnostics
        │   └── metadata.json     # Latency, tokens, score, hard failures
        ├── run_002/
        │   ├── raw_response.txt
        │   ├── parse_error.json  # Recorded if JSON validation fails
        │   └── metadata.json
        ├── summary.json      # Machine-readable aggregate statistics
        └── summary.md        # Human-readable Markdown summary report
```

---

## 6. Exploring Without Paid API Calls (Manual Lab)

You do not need paid API keys to study model behavior. You can run manual exploratory evaluations:

1. **View the complete analyst prompt**:
   Generate or inspect the prompt built from Northstar sources:
   ```bash
   python3 -c "from ib_eval.case import load_case; from ib_eval.baseline.prompt import build_analyst_prompt; from pathlib import Path; print(build_analyst_prompt(load_case(Path('cases/northstar-v1'))))" > /tmp/prompt.txt
   ```
2. **Paste the prompt into your preferred AI chat interface** (e.g., ChatGPT, Claude, Gemini).
3. **Copy the model's raw JSON response** and save it to a file:
   ```bash
   mkdir -p /tmp/manual_run
   # Paste model JSON into /tmp/manual_run/submission.json
   ```
4. **Grade the submission locally**:
   ```bash
   uv run ib-eval grade /tmp/manual_run/
   ```

This workflow lets you manually inspect how various models handle the Northstar case completely offline!

---

## Next Steps

Now that you understand the baseline experiment, proceed to **[Chapter 06 — Where This Can Go](06_where_this_can_go.md)** to see the future roadmap for verifiers, structured agents, and advanced financial tasks.
