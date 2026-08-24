# Milestone 4B — Meridian Benchmark Implementation

This document provides the benchmark specification, accounting mechanisms, gold parameters, and validation report for **Meridian Cloud Systems, Inc.** (`meridian-v1`), the second valuation benchmark in `ib-eval`.

---

## 1. Executive Summary

Milestone 4B implements an offline benchmark for enterprise B2B SaaS software and cloud infrastructure valuation. Where Northstar represents traditional manufacturing with positive EBITDA, net debt, and end-of-year discounting, Meridian tests financial AI models against high revenue growth, non-cash stock-based compensation (SBC), contract liability working capital dynamics (deferred revenue), net cash balances ($EV + NetCash$), and mid-year cash flow discounting.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MERIDIAN V1 BENCHMARK SUMMARY                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ Case ID: meridian-v1              Valuation Date: June 30, 2026             │
│ Industry: Enterprise B2B SaaS     Base Revenue: $760.0M (2025A)             │
│ DCF EV: $1,375.92M                Equity Bridge: $1,375.92M + $200.0M Cash  │
│ DCF Equity Value: $1,575.92M      Implied Share Price: $17.91 / share       │
│ Comps EV: $5,791.20M (6.35x Rev)  Comps Share Price: $68.08 / share         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Benchmark Architecture & Source Packet

The complete benchmark packet resides in `cases/meridian-v1/`:

| File | Type | Purpose |
|---|:---:|---|
| `case.yaml` | Metadata | Case identity, corporate profile, deliberate trap documentation |
| `rubric.yaml` | Evaluation | 10 modular grader configs, weights, tolerances, diagnostic codes |
| `sources/source_01_company_profile.md` | Source Packet | Overview, ARR ($880.0M) vs GAAP revenue ($760.0M), client retention |
| `sources/source_02_historical_financials.md` | Source Packet | 3-year income statement, gross margins, operating expenses, cash flows |
| `sources/source_03_management_guidance.md` | Source Packet | 2026E guidance (18%–22% revenue growth, ~14.0% Adj EBITDA margin) |
| `sources/source_04_capital_structure.md` | Source Packet | $280M Cash, $80M Convertible Debt (Net Cash +$200M), 88M Diluted Shares |
| `sources/source_05_stock_based_compensation.md` | Source Packet | ASC 718 non-cash SBC schedule (12% down to 7% of revenue) |
| `sources/source_06_deferred_revenue.md` | Source Packet | ASC 606 contract liabilities ($385M DR), -5.0% NWC cash inflow dynamics |
| `sources/source_07_peer_comps.md` | Source Packet | 6 enterprise peers, EV / NTM Revenue multiples (6.35x median), N/M FCF |
| `sources/source_08_accounting_notes.md` | Source Packet | ASC 350-40 software capex (5.0%), Mid-Year DCF timing, t=5.0 TV horizon |
| `ground_truth/generate_gold.py` | Ground Truth | Programmatic DCF & Comps engine generating 100/100 gold submission |

---

## 3. Financial Mechanics & Domain Invariants

### 1. Revenue vs. ARR Disambiguation
- **Trap**: Compounding forward revenue from FY2025 ending ARR ($880.0M) instead of base GAAP revenue ($760.0M).
- **Rule**: $2026\text{E Revenue} = \$760.0\text{M} \times (1 + 0.20) = \$912.0\text{M}$.
- **Diagnostic Code**: `REV_ARR_CONFUSION`.

### 2. Stock-Based Compensation & GAAP EBIT Reconciliation
- **Invariant**: $\text{GAAP EBIT} = \text{Adjusted EBITDA} - \text{SBC} - \text{D\&A}$.
- **2026E Illustration**: $\$127.68\text{M (Adj. EBITDA)} - \$100.32\text{M (SBC)} - \$18.24\text{M (D\&A)} = \$9.12\text{M (GAAP EBIT)}$.
- **Diagnostic Code**: `SBC_EBITDA_INCONSISTENCY`.

### 3. Capitalized Software & Cash Flow Presentation
- **Invariant**: Capital expenditures include both physical PP&E (1.5% of revenue) and capitalized internal-use software under ASC 350-40 (3.5% of revenue), totaling 5.0% of revenue.
- **Trap**: Deducting capitalized software in operating expenses and deducting it again in capital investments.
- **Diagnostic Code**: `FCF_SOFTWARE_DOUBLE_COUNTED`.

### 4. Deferred Revenue & Working Capital Inflow
- **Invariant**: Net Operating Working Capital is negative (-5.0% of revenue) because upfront customer billings create substantial deferred revenue liabilities.
- **Cash Flow Rule**: As revenue grows, $-\Delta\text{NWC} > 0$ yields a **source of operating cash flow**.
- **Diagnostic Code**: `WC_DEFERRED_REV_REVERSED`.

### 5. Mid-Year Cash Flow Discounting vs. Terminal Horizon
- **Explicit Forecast Period**: Cash flows are discounted using fractional exponents reflecting continuous intra-year collection:
  $$DF_t = (1 + \text{WACC})^{-(t - 0.5)} \quad \text{for } t \in \{1, 2, 3, 4, 5\}$$
- **Terminal Value Horizon**: Perpetuity established at the end of Year 5 ($t=5.0$):
  $$\text{PV(TV)} = \frac{\text{TV}_{2030}}{(1 + \text{WACC})^{5.0}}$$
- **Diagnostic Code**: `DCF_MIDYEAR_CONVENTION_ERROR`.

### 6. The Net Cash Equity Bridge
- **Invariant**: Gross Debt ($80.0M) − Cash ($280.0M) = Net Debt (−$200.0M), representing **+$200.0M Net Cash**.
- **Equity Value**: $\text{Equity Value} = \text{Enterprise Value} - (-\$200.0\text{M}) = \text{Enterprise Value} + \$200.0\text{M}$.
- **Per-Share Denominator**: 88.0M fully diluted shares (80.0M basic shares + 8.0M options/RSUs).
- **Diagnostic Codes**: `EQ_BRIDGE_NET_CASH_REVERSED`, `SHARES_BASIC_USED`.

### 7. Trading Comparables & N/M Multiples
- **Primary Multiple**: EV / NTM Revenue (6.35x median applied to $912.0M 2026E revenue).
- **N/M Peer Rule**: Strata Platform has negative FCF (`N/M`) and must be excluded from FCF median computations rather than coerced to 0.0x.
- **Diagnostic Code**: `COMPS_NM_FCF_COERCED_ZERO`.

---

## 4. Controlled Corrupted Benchmark Fixtures

Meridian includes 10 controlled corrupted fixtures in `examples/meridian_corrupted/`:

| Fixture ID | Failure Mode | Triggered Diagnostic Code | Severity |
|---|---|---|:---:|
| `m01` | ARR ($880M) used as revenue base | `REV_ARR_CONFUSION` | Critical |
| `m02` | Deferred revenue cash inflow reversed | `WC_DEFERRED_REV_REVERSED` | Critical |
| `m03` | Capitalized software double counted | `FCF_SOFTWARE_DOUBLE_COUNTED` | Critical |
| `m04` | Net cash subtracted from EV | `EQ_BRIDGE_NET_CASH_REVERSED` | Critical |
| `m05` | Non-cash SBC omitted from GAAP EBIT | `SBC_EBITDA_INCONSISTENCY` | Critical |
| `m06` | Basic shares (80M) used instead of 88M diluted | `SHARES_BASIC_USED` | Critical |
| `m07` | Terminal Value discounted at t=4.5 instead of 5.0 | `DCF_MIDYEAR_CONVENTION_ERROR` | Critical |
| `m08` | Strata negative FCF multiple coerced to 0.0x | `COMPS_NM_FCF_COERCED_ZERO` | Critical |
| `m09` | Management guidance verbatim point claim in notes | `SF_GUIDANCE_FABRICATED` | Critical |
| `m10` | Pre-tax debt yield used in WACC | `WACC_PRETAX_DEBT` | Critical |

---

## 5. Grader Reuse & Architectural Generalization

All 10 graders in `src/ib_eval/graders/` evaluate both Northstar and Meridian submissions seamlessly:

- **5 / 10 Graders (50.0%) Directly Reused**: `source_fidelity`, `revenue_forecast`, `wacc`, `enterprise_value`, `consistency`.
- **5 / 10 Graders (50.0%) Parameterized / Extended**: `terminal_value`, `equity_bridge`, `comps`, `margin_forecast`, `free_cash_flow`.

### Design Principle: Parsing vs. Grading Boundary
- **Parsing Validates Representability**: Structural validation ensures types, enums, and required fields exist without rejecting candidate models for mathematically incorrect inputs.
- **Graders Validate Financial Correctness**: Deterministic financial rules (WACC weights, equity bridge reconciliation, EBITDA arithmetic) are evaluated by deterministic graders, ensuring that financially erroneous submissions remain gradeable and emit clear diagnostic codes.

### Structured Workflow Generalization (`structured_v2`)
- **Audit Finding**: The initial `structured_v1` prompt hardcoded Northstar-specific equations (`EBIT_t = EBITDA_t - DA_t` and `Median Multiple * Target EBITDA`). On Meridian, where EBITDA is Adjusted EBITDA, this induced a 10/10 `SBC_EBITDA_INCONSISTENCY` hard-failure rate.
- **Generalization**: `structured_v2` guides the model to reconcile reported profitability to GAAP EBIT using source-defined bridges and apply the primary multiple to the matching target metric, preserving benchmark purity without hardcoding Meridian values.

Regression testing verifies that:
1. `uv run ib-eval grade examples/gold_submission/submission.json` $\rightarrow$ **100.0 / 100 (A+)**, 0 hard failures.
2. `uv run ib-eval grade examples/meridian_gold_submission/submission.json` $\rightarrow$ **100.0 / 100 (A+)**, 0 hard failures.
3. 212 / 212 unit tests pass in under 2 seconds.
