# Chapter 04 — Learning from the Corrupted Fixtures

> **"A useful benchmark does not only contain correct examples. It contains deliberately incorrect examples that prove the evaluator can identify specific failure classes."**

This chapter is a hands-on laboratory. In `examples/corrupted/`, we maintain 10 deliberately corrupted submissions. Each fixture represents one classic error mode made by human junior analysts and generative AI models.

---

## 1. Overview of the 10 Corrupted Fixtures

| Fixture Directory | Error Injected | Expected Diagnostic Code | Primary Grader |
|---|---|---|---|
| **[`c01_quarterly_revenue`](#1-c01_quarterly_revenue)** | Q2 standalone (\$281mm) used as annual | `REV_QUARTERLY_CONFUSION` | `revenue_forecast` |
| **[`c02_tv_not_discounted`](#2-c02_tv_not_discounted)** | TV added at face value without discounting | `TV_NOT_DISCOUNTED` | `terminal_value` |
| **[`c03_cash_subtracted`](#3-c03_cash_subtracted)** | Cash added to gross debt (cash reversed) | `EQ_BRIDGE_CASH_REVERSED` | `equity_bridge` |
| **[`c04_debt_omitted`](#4-c04_debt_omitted)** | Net debt set to zero in equity bridge | `EQ_BRIDGE_DEBT_OMITTED` | `equity_bridge` |
| **[`c05_nm_peer_zero`](#5-c05_nm_peer_zero)** | Negative EBITDA peer coerced to 0.0x | `COMPS_NM_COERCED_ZERO` | `comps` |
| **[`c06_fabricated_guidance`](#6-c06_fabricated_guidance)** | Claiming management stated exactly 8% | `SF_GUIDANCE_FABRICATED` | `source_fidelity` |
| **[`c07_ebitda_inconsistency`](#7-c07_ebitda_inconsistency)** | EBIT ≠ EBITDA − D&A | `MARGIN_EBIT_INCONSISTENCY` | `margin_forecast` |
| **[`c08_capex_double_counted`](#8-c08_capex_double_counted)** | Capex duplicated in UFCF derivation | `FCF_CAPEX_DOUBLE_COUNTED` | `free_cash_flow` |
| **[`c09_headline_mismatch`](#9-c09_headline_mismatch)** | Headline equity value ≠ equity bridge | `CONSISTENCY_HEADLINE_DCF` | `consistency` |
| **[`c10_pretax_wacc`](#10-c10_pretax_wacc)** | Pre-tax debt cost used without tax shield | `WACC_PRETAX_DEBT` | `wacc` |

---

## 2. Deep Dive: Fixture by Fixture

Let's test each fixture using the `ib-eval grade` CLI:

---

### 1. `c01_quarterly_revenue`
- **The Mistake**: 2026E annual revenue is set to \$281.0mm (Northstar's Q2 standalone revenue).
- **Financial Impact**: Undervalues the company by more than 70% by forecasting from a single quarter instead of the \$1,000.0mm full-year annual base.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c01_quarterly_revenue
  ```
- **Observed Diagnostic**: `[CRITICAL] REV_QUARTERLY_CONFUSION: 2026E revenue (281.0) is close to Q2 standalone revenue (281.0). Possible quarterly/annual confusion.`

---

### 2. `c02_tv_not_discounted`
- **The Mistake**: The model computes terminal value at horizon $T=5$ (\$2,003.78mm) and adds it directly to enterprise value without applying the 5-year discount factor ($0.641554$).
- **Financial Impact**: Overvalues Enterprise Value by +\$718.25mm (+42% error!).
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c02_tv_not_discounted
  ```
- **Observed Diagnostic**: `[CRITICAL] TV_NOT_DISCOUNTED: Terminal value appears NOT discounted to valuation date. PV(TV) = TV / (1 + WACC)^5 = 2003.7826 × 0.641554 = 1285.5341, not 2003.7826.`

---

### 3. `c03_cash_subtracted`
- **The Mistake**: Net debt is calculated as $\text{Gross Debt} + \text{Cash} = \$420 + \$95 = \$515\text{mm}$ instead of $\text{Gross Debt} - \text{Cash} = \$325\text{mm}$.
- **Financial Impact**: Destroys \$190.0mm of equity value (\$3.17/share) by treating cash as a liability.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c03_cash_subtracted
  ```
- **Observed Diagnostic**: `[CRITICAL] EQ_BRIDGE_CASH_REVERSED: Cash appears to have been ADDED to gross debt rather than subtracted. Net debt = gross_debt − cash = 420.0 − 95.0 = 325.0, not 515.0.`

---

### 4. `c04_debt_omitted`
- **The Mistake**: The equity bridge omits net debt entirely, setting Net Debt = \$0 and equating Equity Value directly to Enterprise Value.
- **Financial Impact**: Overstates equity value by \$325.0mm by pretending the company has zero debt obligations.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c04_debt_omitted
  ```
- **Observed Diagnostic**: `[CRITICAL] EQ_BRIDGE_DEBT_OMITTED: Net debt in equity bridge is ~0. Debt may be entirely omitted.`

---

### 5. `c05_nm_peer_zero`
- **The Mistake**: Evergreen Controls has negative EBITDA. The candidate coerces its multiple from `N/M` to `0.0x` and calculates median across `[0.0, 7.3, 7.9, 8.5, 9.2]`.
- **Financial Impact**: Artificially depresses the peer median multiple from 8.20x to 7.90x, reducing comps equity value by \$55.0mm.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c05_nm_peer_zero
  ```
- **Observed Diagnostic**: `[CRITICAL] COMPS_NM_COERCED_ZERO: Evergreen Controls has negative EBITDA and should be marked N/M (None), not coerced to zero.`

---

### 6. `c06_fabricated_guidance`
- **The Mistake**: In the provenance table, the candidate marks `revenue_growth/2026E` as a `direct` fact with note: *"Management guided to 8% growth."*
- **Financial Impact**: Epistemic fabrication. Management only stated qualitative "high single digits." While 8.0% is a defensible assumption, claiming management stated 8.0% misrepresents source truth to clients.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c06_fabricated_guidance
  ```
- **Observed Diagnostic**: `[CRITICAL] SF_GUIDANCE_FABRICATED: revenue_growth/2026E classified as 'direct' — management only provided qualitative guidance ('high single digits'); exact % is an analyst assumption.`

---

### 7. `c07_ebitda_inconsistency`
- **The Mistake**: In 2026E, EBITDA is \$183.60mm and D&A is \$43.20mm, but EBIT is manually keyed as \$155.40mm (an unexplained \$15.0mm discrepancy).
- **Financial Impact**: Breaks fundamental accounting reconciliation: $\text{EBIT} \equiv \text{EBITDA} - \text{D&A}$.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c07_ebitda_inconsistency
  ```
- **Observed Diagnostic**: `[CRITICAL] MARGIN_EBIT_INCONSISTENCY: EBIT = EBITDA − D&A: 183.60 − 43.20 = 140.40 ≠ 155.40`

---

### 8. `c08_capex_double_counted`
- **The Mistake**: Due to confusing "capital investment" (guidance) with "capex" (cash flow statement), the model deducts Capex twice (\$97.20mm instead of \$48.60mm).
- **Financial Impact**: Depresses 2026E UFCF from \$90.30mm down to \$41.70mm, materially distorting DCF valuation.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c08_capex_double_counted
  ```
- **Observed Diagnostic**: `[CRITICAL] FCF_CAPEX_DOUBLE_COUNTED: Capex appears double-counted: submitted 97.2000, expected 48.6000 (4.5% of revenue).`

---

### 9. `c09_headline_mismatch`
- **The Mistake**: The underlying DCF model computes an equity value of \$1,387.97mm (\$23.13/share), but the executive headline table reports \$1,578.00mm (\$26.30/share).
- **Financial Impact**: Cross-artifact inconsistency. A pitchbook where the cover slide contradicts the appendix financial model will mislead clients and destroy credibility.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c09_headline_mismatch
  ```
- **Observed Diagnostic**: `[CRITICAL] CONSISTENCY_HEADLINE_DCF: Headline DCF equity (1578.00) ≠ equity bridge (1387.97)`

---

### 10. `c10_pretax_wacc`
- **The Mistake**: The WACC calculation uses pre-tax cost of debt ($K_d = 6.2\%$) directly, omitting the corporate tax shield: $K_{d,\text{after-tax}} = 6.2\% \times (1 - 0.25) = 4.65\%$.
- **Financial Impact**: Inflates WACC from $9.2832\%$ to $9.6242\%$, over-discounting future cash flows and reducing DCF Enterprise Value by \$55.0mm.
- **Run the Grader**:
  ```bash
  uv run ib-eval grade examples/corrupted/c10_pretax_wacc
  ```
- **Observed Diagnostic**: `[CRITICAL] WACC_PRETAX_DEBT: Pre-tax cost of debt used without tax adjustment. Kd_at = Kd × (1 − t) = 0.062 × 0.75 = 0.046500, not 0.062.`

---

## 3. Hands-On Exercise: Try It Yourself

Want to test your understanding? Try corrupting a submission yourself:

1. **Create a scratch copy** of the gold submission:
   ```bash
   mkdir -p /tmp/my_test_submission
   cp examples/gold_submission/submission.json /tmp/my_test_submission/
   ```
2. **Edit `/tmp/my_test_submission/submission.json`**:
   - For example, change `wacc_inputs.tax_rate` to `0.0`, or change `equity_bridge.diluted_shares` to `120.0`.
3. **Predict before grading**:
   - Which grader will fail?
   - What diagnostic code do you expect?
4. **Run the grader**:
   ```bash
   uv run ib-eval grade /tmp/my_test_submission/
   ```
5. Compare the observed diagnostic against your prediction!

---

## Next Steps

Now that you've seen how specific errors are diagnosed, proceed to **[Chapter 05 — Milestone 1: Direct Analyst Baseline](05_direct_analyst_baseline.md)** to see how we evaluate frontier LLMs across repeated trials.
