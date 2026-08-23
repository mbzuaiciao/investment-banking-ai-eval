# Chapter 11 — Milestone 4A: Second Case Design (Meridian Cloud Systems, Inc.)

This document specifies the design of **Meridian Cloud Systems, Inc.**, the second evaluation case for `investment-banking-ai-eval`.

---

## 1. Executive Summary

Milestones 0 through 3B established that structured financial workflows and deterministic compiler-like feedback materially improved language model reliability on the **Northstar Components, Inc.** valuation case.

However, Northstar represents a specific corporate profile: a mature, profitable industrial manufacturing company with positive Free Cash Flow, net debt, tangible PP&E capex, and standard EV/EBITDA trading comps.

To test whether the evaluation harness, structured analyst workflow, and deterministic feedback repair represent a **generalizable financial intelligence framework** rather than an overfitted solution tailored to Northstar, **Milestone 4** introduces a second, fundamentally different financial case:

> **Core Research Question**: Do the structured workflow, domain invariants, and deterministic-feedback repair architecture continue to improve reliability on a materially different financial case without being redesigned specifically for Northstar?

---

## 2. Why Meridian? (The Generalization Hypothesis)

A valuation architecture that only works when a company has positive EBITDA and net debt is of limited utility in modern investment banking.

**Meridian Cloud Systems, Inc.** is designed as a synthetic, mid-sized B2B SaaS (Software-as-a-Service) and enterprise cloud infrastructure provider. It introduces the complex analytical, accounting, and valuation mechanics typical of high-growth subscription technology companies.

### The Generalization Ladder:

```text
               CASE GENERALIZATION ARCHITECTURE
┌─────────────────────────────────────────────────────────────┐
│ Case 1: Northstar Components (Industrial / Mature)          │
│ • Positive EBITDA & FCF      • Inventory/Receivables NWC    │
│ • Net Debt Bridge            • EV / EBITDA Trading Comps    │
│ • End-of-Year Discounting    • Physical PP&E Capex          │
├─────────────────────────────────────────────────────────────┤
│ Case 2: Meridian Cloud Systems (B2B SaaS / Growth)          │
│ • Emerging / Near-Zero EBITDA• Deferred Revenue Cash Source │
│ • Net Cash Bridge            • EV / NTM Revenue Comps       │
│ • Mid-Year Discounting       • Capitalized Software & SBC   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Northstar vs. Meridian: Comparative Dimension Matrix

| Financial Dimension | Northstar Components, Inc. (Case 1) | Meridian Cloud Systems, Inc. (Case 2) | Analytical Challenge for AI |
|---|---|---|---|
| **Industry & Model** | Traditional industrial manufacturing | B2B Subscription Enterprise SaaS | Revenue recognition vs. billings/ARR dynamics |
| **Revenue Scale & Growth** | \$1,000.0M base; high single-digit (8.0%) | \$760.0M base; high-teens growth (18.0%–20.0%) | Decelerating growth curve modeling (20% $\rightarrow$ 8%) |
| **Profitability & Margins** | Strong GAAP EBITDA margin (18.0%) | GAAP Operating Loss; Adj. EBITDA near 11% | GAAP Operating Loss vs. Non-GAAP Adjusted EBITDA |
| **Cash Generation (FCF)** | Consistently positive and stable | Initially low/negative; back-weighted | Operating leverage & margin expansion schedule |
| **Capital Structure** | Net Debt (\$325.0M net debt: \$420M Debt − \$95M Cash) | **Net Cash** (\$280M Cash vs. \$80M Debt = +\$200M) | Equity Bridge sign inversion: $Equity = EV + Net Cash$ |
| **Capital Expenditures** | Tangible machinery & plant PP&E | Low physical capex + **Capitalized Software** | Differentiating capitalized R&D from cash opex |
| **Working Capital Engine** | Cash consumed by Inventory & Receivables | **Deferred Revenue** (contract liabilities) | Cash collected in advance creates positive cash flow |
| **Compensation Structure** | Conventional cash payroll | **Significant Stock-Based Compensation (SBC)** | Modeling SBC dilution vs. valuation cash deduction |
| **Discounting Convention** | End-of-Year ($t = 1, 2, 3, 4, 5$) | **Mid-Year Convention** ($t = 0.5, 1.5, 2.5, 3.5, 4.5$) | Applying fractional exponents to discount cash flows |
| **Peer Valuation Multiples** | EV / LTM & NTM EBITDA | **EV / NTM Revenue** (and secondary EV / FCF) | Selecting revenue multiples for low-EBITDA peers |

---

## 4. Proposed Company Profile: Meridian Cloud Systems, Inc.

### Corporate Overview
- **Fictional Company**: Meridian Cloud Systems, Inc. ("Meridian")
- **Sector**: Enterprise Software / Cloud Infrastructure
- **Core Product**: Hybrid Cloud Observability & Database Virtualization Platform
- **Revenue Model**: Multi-year subscription contracts (annual and quarterly upfront billing)
- **Valuation Date**: June 30, 2026 (CY2026 mid-year cutoff)
- **Reporting Units**: USD millions (\$M), except per-share metrics

### Key Operational Metrics
- **Annual Recurring Revenue (ARR)**: \$880.0M at FY2025 year-end (growing 22.2% YoY)
- **GAAP Revenue**: \$760.0M in FY2025 (growing 16.9% YoY)
- **Gross Retention Rate**: 94.0%
- **Net Dollar Expansion Rate (NDR)**: 114.0%
- **Gross Margin**: 75.0% (Hosting infrastructure, third-party APIs, and customer support)
- **Rule of 40 Metric**: 16.9% Revenue Growth + 11.2% Adj. EBITDA Margin = 28.1% (Targeting >40% by 2028E)

---

## 5. Historical Financial Design (2023A–2025A)

The historical financial schedules are designed to be internally consistent, exhibiting typical SaaS accounting relationships:

### Summary Historical Income Statement (\$M)

| Line Item | 2023A | 2024A | 2025A | Accounting / Finance Notes |
|---|---:|---:|---:|---|
| **Subscription Revenue** | 495.0 | 598.0 | 706.8 | ~93% of total revenue |
| **Professional Services Revenue** | 55.0 | 52.0 | 53.2 | Low-margin implementation services |
| **Total Revenue** | **550.0** | **650.0** | **760.0** | +18.2% (2024), +16.9% (2025) |
| Cost of Revenue (Subscription) | (118.8) | (137.5) | (155.5) | AWS/Azure hosting & support |
| Cost of Revenue (Services) | (52.2) | (48.0) | (48.0) | Implementation headcount |
| **Gross Profit** | **379.0** | **464.5** | **556.5** | **73.2% (2024) $\rightarrow$ 73.2% (2025)** |
| Research & Development (R&D) | (165.0) | (188.5) | (212.8) | 28.0% of revenue |
| Sales & Marketing (S&M) | (209.0) | (240.5) | (273.6) | 36.0% of revenue |
| General & Administrative (G&A) | (66.0) | (74.8) | (83.6) | 11.0% of revenue |
| **GAAP Operating Income (EBIT)** | **(61.0)** | **(39.3)** | **(13.5)** | **GAAP Operating Loss** |
| *Addback: Stock-Based Comp (SBC)* | 66.0 | 78.0 | 91.2 | 12.0% of revenue (non-cash) |
| *Addback: D&A / Amortization* | 12.0 | 14.0 | 16.0 | PP&E depreciation + software amort |
| **Adjusted EBITDA** | **17.0** | **52.7** | **93.7** | **Margin: 3.1% $\rightarrow$ 8.1% $\rightarrow$ 12.3%** |

### Historical Cash Flow & Balance Sheet Highlights (\$M)

| Metric | 2023A | 2024A | 2025A | Commentary |
|---|---:|---:|---:|---|
| **Capitalized Internal Software** | (18.0) | (22.0) | (26.0) | Capitalized on balance sheet as intangible asset |
| **Physical PP&E Capex** | (8.0) | (9.0) | (10.0) | Laptops, office equipment, data servers |
| **Total Capital Investments** | **(26.0)** | **(31.0)** | **(36.0)** | Combined cash outflow |
| **Change in Deferred Revenue ($\Delta$DR)** | +42.0 | +55.0 | +65.0 | Upfront billings collected before recognition |
| **Cash & Cash Equivalents** | 190.0 | 230.0 | **280.0** | Significant cash liquidity |
| **Total Debt (Convertible Notes)** | 80.0 | 80.0 | **80.0** | 2.50% coupon senior convertible notes |
| **Net Cash (Cash − Debt)** | **+110.0** | **+150.0** | **+200.0** | **Net Cash Capital Structure** |
| Basic Common Shares Outstanding | 76.0 | 78.0 | 80.0 | Millions of shares |
| Diluted Shares Outstanding | 84.0 | 86.0 | **88.0** | Includes in-the-money options & unvested RSUs |

---

## 6. Forecast Design (2026E–2030E)

The forecast models a textbook SaaS transition from hyper-growth investment to mature cash generation:

```text
Decelerating Revenue Growth:
2026E (+20.0%) → 2027E (+17.0%) → 2028E (+14.0%) → 2029E (+11.0%) → 2030E (+8.0%)

Expanding Adjusted EBITDA Margin:
2026E (14.0%)  → 2027E (17.0%)  → 2028E (20.0%)  → 2029E (23.0%)  → 2030E (26.0%)
```

### Key Forecast Schedules:
1. **Revenue Forecast**: Base FY2025 revenue (\$760.0M) compounds at projected growth rates reaching \$1,489.1M in 2030E.
2. **Gross Margin**: Expands from 73.2% to 76.0% as multi-tenant cloud optimization yields server cost efficiencies.
3. **Operating Expenses**: S&M scales down from 36.0% to 26.0% of revenue as direct enterprise sales motions mature; R&D scales from 28.0% to 20.0%.
4. **GAAP NOPAT Derivation**:
   - $\text{GAAP EBIT} = \text{Adjusted EBITDA} - \text{SBC} - \text{D\&A}$
   - Corporate Tax Shield applied only when cumulative taxable income is positive (accounting for NOL carryforwards).
5. **Unlevered Free Cash Flow (UFCF)**:
   $$\text{UFCF} = \text{NOPAT} + \text{D\&A} + \text{SBC} - \text{Physical Capex} - \text{Capitalized Software} - \Delta\text{NWC (incl. } \Delta\text{Deferred Revenue)}$$
   *(Note: SBC is added back to cash flow because it is non-cash, while dilution is captured in the diluted share denominator).*

---

## 7. DCF Methodology & SaaS Complications

### Mid-Year Discounting Convention
Unlike Northstar's end-of-year discounting convention, Meridian specifies a **mid-year discounting convention** to reflect continuous cash collection across subscription billing cycles:

$$\text{Discount Factor}_t = \frac{1}{(1 + \text{WACC})^{t - 0.5}} \quad \text{for } t \in \{1, 2, 3, 4, 5\}$$

- **Period 1 (2026E)**: $t = 0.5 \implies DF_1 = (1 + \text{WACC})^{-0.5}$
- **Period 2 (2027E)**: $t = 1.5 \implies DF_2 = (1 + \text{WACC})^{-1.5}$
- **Period 3 (2028E)**: $t = 2.5 \implies DF_3 = (1 + \text{WACC})^{-2.5}$
- **Period 4 (2029E)**: $t = 3.5 \implies DF_4 = (1 + \text{WACC})^{-3.5}$
- **Period 5 (2030E)**: $t = 4.5 \implies DF_5 = (1 + \text{WACC})^{-4.5}$

### Terminal Value Mechanics
- **Gordon Growth Model**: $\text{Terminal Value}_{2030} = \frac{\text{Terminal FCF}_{2031}}{\text{WACC} - g} = \frac{\text{UFCF}_{2030} \times (1 + g)}{\text{WACC} - g}$
- **Terminal Growth Rate ($g$)**: 3.0% (Aligned with long-term enterprise IT spending growth)
- **Terminal Horizon Discounting**:
  $$\text{PV(TV)} = \frac{\text{Terminal Value}_{2030}}{(1 + \text{WACC})^{5.0}}$$
  
> [!NOTE]
> **Terminal Horizon Discounting vs. Explicit FCF Mid-Year Timing**:
> Mid-year discounting of explicit annual FCFs ($t = 0.5, 1.5, 2.5, 3.5, 4.5$) does not imply that the terminal value automatically uses the same 4.5-year exponent. The benchmark convention explicitly places the perpetuity at the end of the final forecast year ($t = 5.0$). Therefore, $\text{PV(TV)} = \text{TV} / (1 + \text{WACC})^{5.0}$. Treat this as a convention-dependent invariant whose correctness depends on the case specification.

---

## 8. Capital Structure, WACC, and Net Cash Bridge

### WACC Derivation
- **Risk-Free Rate ($R_f$)**: 4.25% (10-Year U.S. Treasury)
- **Equity Risk Premium (ERP)**: 5.50%
- **Levered Beta ($\beta$)**: 1.25 (Reflecting software volatility)
- **Cost of Equity ($K_e$)**: $4.25\% + (1.25 \times 5.50\%) = 11.125\%$
- **Pre-Tax Cost of Debt ($K_d$)**: 5.50% (Convertible note yield)
- **Marginal Tax Rate ($t$)**: 21.0%
- **After-Tax Cost of Debt**: $5.50\% \times (1 - 0.21) = 4.345\%$
- **Capital Structure Weights**: Target 95.0% Equity / 5.0% Debt
- **Blended WACC**: $(0.95 \times 11.125\%) + (0.05 \times 4.345\%) = 10.786\%$

### The Net Cash Equity Bridge
Because Meridian possesses **\$280.0M of Cash** and only **\$80.0M of Gross Debt**, Net Debt is negative (\$80.0M − \$280.0M = −\$200.0M).

$$\text{Equity Value} = \text{Enterprise Value} + \text{Cash} - \text{Debt} = \text{Enterprise Value} + \$200.0\text{M}$$

$$\text{Implied Share Price} = \frac{\text{Equity Value}}{\text{Diluted Shares Outstanding (88.0M)}}$$

> [!IMPORTANT]
> **Net Cash Inversion Trap**: If an AI model blindly applies Northstar's formula ($\text{Equity Value} = \text{EV} - \text{Net Debt}$ with a positive debt value), it will subtract cash instead of adding it, depressing the valuation by \$400.0M (\$4.55/share).

---

## 9. Trading Comparables Universe (B2B SaaS Peers)

Meridian is evaluated against 6 synthetic enterprise software peers:

| Peer Company | Business Focus | NTM Rev Growth | NTM Adj. EBITDA Margin | NTM FCF Margin | EV / NTM Revenue | EV / NTM FCF | Analytical Notes |
|---|---|---:|---:|---:|---:|---:|---|
| **Aether Data, Inc.** | Cloud database infrastructure | 22.0% | 14.0% | 12.0% | 7.5x | 62.5x | Direct peer (Premium multiple) |
| **Vanguard SaaS Corp.** | Enterprise workflow automation | 18.0% | 16.0% | 15.0% | 6.2x | 41.3x | Core peer (Target comp) |
| **Kestrel Systems** | Infrastructure monitoring | 15.0% | 18.0% | 16.0% | 5.4x | 33.8x | Mature SaaS peer |
| **Strata Platform** | Developer tooling | 28.0% | (5.0%) | **(8.0%)** | 8.8x | **N/M** | **Negative FCF Trap** |
| **Nimbus Cloudworks** | Legacy migration software | 8.0% | 22.0% | 18.0% | 3.5x | 19.4x | Low-growth outlier |
| **Helix Enterprise** | Security observability | 19.0% | 12.0% | 10.0% | 6.5x | 65.0x | Core peer |

### Multiple Selection Rules:
1. **Primary Valuation Metric**: **EV / NTM Revenue** (Median of the 6-peer comp set).
2. **Secondary Metric**: **EV / NTM FCF** (Excluding Strata Platform's negative FCF as `N/M` rather than coercing to 0.0x).
3. **Application**: Apply Median EV/NTM Revenue multiple to Meridian's projected 2026E Revenue (\$912.0M).

---

## 10. Source Packet Design (8 Documents)

The synthetic source bundle will be organized in `cases/meridian-v1/sources/`:

1. **`source_01_company_profile.md`**: Executive summary, business model, subscription pricing tiers, customer count, Net Retention (114%), and ARR trajectory.
2. **`source_02_historical_financials.md`**: GAAP Income Statement, Balance Sheet, and Cash Flow Statement for 2023A–2025A.
3. **`source_03_management_guidance.md`**: 2026E outlook: "Targeting 19%–21% revenue growth", "Adjusted EBITDA margin expansion of ~150–200 bps", and "Capex investments around \$35M–\$40M inclusive of capitalized software".
4. **`source_04_capital_structure.md`**: Cash balances, 2.50% convertible notes due 2029, basic common share count (80.0M), options/RSU dilution table (8.0M dilutive shares).
5. **`source_05_stock_based_compensation.md`**: Historical and expected SBC schedule as a % of revenue (12.0% declining to 8.0% long-term).
6. **`source_06_deferred_revenue.md`**: Billings schedule, contract liabilities balance, and working capital cash flow implications.
7. **`source_07_peer_comps.md`**: Financial data and valuation multiples for the 6 enterprise SaaS peers.
8. **`source_08_accounting_notes.md`**: Detailed notes specifying the **mid-year discounting convention**, capitalization of internal software under ASC 350-40, and tax rate assumptions.

---

## 11. The 10 Deliberate SaaS Modeling Traps

Meridian embeds 10 deliberate ambiguity traps designed to test whether an AI analyst reasons from first principles:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. ARR vs. GAAP Revenue Confusion                                           │
│    • Management cites "ARR reached $880M (+22.2%)"                          │
│    • Trap: Using $880M as the base for 2026E revenue rather than $760M GAAP │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Deferred Revenue Cash Flow Sign Error                                    │
│    • Deferred revenue increases by +$65M in 2025A                           │
│    • Trap: Treating increasing working capital liability as a use of cash   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Capitalized Software Double Counting                                     │
│    • Source discloses $10M physical capex and $26M capitalized software     │
│    • Trap: Deducting capitalized software as both opex and capex in UFCF    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Net Cash Equity Bridge Inversion                                         │
│    • Company has $280M cash and $80M debt ($200M Net Cash)                  │
│    • Trap: Subtracting $200M from EV instead of adding it                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. Stock-Based Compensation (SBC) Inconsistency                             │
│    • Adjusted EBITDA adds back $91.2M SBC; GAAP EBIT includes SBC           │
│    • Trap: Omitting SBC from GAAP EBIT or double-counting in UFCF bridge    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 6. Basic vs. Diluted Share Count Selection                                 │
│    • 80.0M Basic vs. 88.0M Diluted shares                                   │
│    • Trap: Dividing Equity Value by basic shares, inflating share price 10% │
├─────────────────────────────────────────────────────────────────────────────┤
│ 7. Mid-Year vs. Year-End Discounting Convention                             │
│    • Accounting notes mandate Mid-Year convention                           │
│    • Trap: Using integer discount powers (t=1..5) instead of fractional     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 8. Non-Meaningful (N/M) Peer Multiple Coercion                              │
│    • Strata Platform has negative FCF (EV/FCF = N/M)                        │
│    • Trap: Setting multiple to 0.0x and skewing peer median calculation     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 9. Primary SaaS Multiple Selection                                          │
│    • Peer set reports EV/Revenue, EV/EBITDA, and EV/FCF                     │
│    • Trap: Selecting EV/EBITDA when company/peers are near breakeven        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 10. Guideline Guidance Misclassification                                    │
│     • Management guides "approximately 20% revenue growth"                  │
│     • Trap: Classifying explicit 20% point assumption as direct source fact │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Candidate Error Taxonomy & Diagnostics

Proposed new machine-readable diagnostic codes for Milestone 4:

| Diagnostic Code | Severity | Description | Evaluation Rule |
|---|---|---|---|
| `REV_ARR_CONFUSION` | Critical | Base revenue confused with ending ARR | `base_revenue == 760.0` (not `880.0`) |
| `WC_DEFERRED_REV_REVERSED` | Critical | Deferred revenue increase subtracted from cash | $\Delta\text{DR} > 0 \implies \text{Cash Inflow}$ |
| `FCF_SOFTWARE_DOUBLE_COUNTED` | Critical | Capitalized software deducted twice in UFCF | Deducted in investments, not opex |
| `EQ_BRIDGE_NET_CASH_REVERSED` | Critical | Net cash subtracted from EV instead of added | $\text{Equity} = \text{EV} + \text{Net Cash}$ |
| `SBC_EBITDA_INCONSISTENCY` | Critical | Adjusted EBITDA does not equal GAAP EBIT + SBC + D&A | $\text{Adj EBITDA} = \text{EBIT} + \text{SBC} + \text{D\&A}$ |
| `SHARES_BASIC_USED` | Critical | Basic shares used instead of fully diluted shares | $\text{Denominator} == 88.0\text{M}$ |
| `DCF_MIDYEAR_CONVENTION_ERROR` | Critical | End-of-year integer powers used instead of mid-year | $DF_t = (1 + WACC)^{-(t - 0.5)}$ |
| `COMPS_NM_FCF_COERCED_ZERO` | Critical | Negative FCF multiple coerced to 0.0x | Strata excluded from FCF median |
| `COMPS_WRONG_PRIMARY_MULTIPLE` | Warning | EV/EBITDA selected as primary SaaS valuation multiple | EV/NTM Revenue must be primary |
| `SF_GUIDANCE_FABRICATED` | Warning | 20.0% growth classified as direct source fact | Classified as `analyst_assumption` |

---

## 13. Domain-Invariant Classification

In accordance with the benchmark's core philosophy, evaluators are strictly partitioned across three tiers:

```text
1. Deterministic Invariants (Strict Machine Grading & One-Shot Repair)
   • NOPAT = GAAP EBIT × (1 - Tax Rate)
   • Adjusted EBITDA = GAAP EBIT + SBC + D&A
   • Mid-Year Discounting: DF_t = 1 / (1 + WACC)^(t - 0.5)
   • Equity Value = EV + Cash - Debt (Net Cash)
   • Implied Share Price = Equity Value / Diluted Shares
   • Comps Median Calculation (excluding N/M)

2. Convention-Dependent Invariants (Tolerance Ranges & Explicit Schema Tags)
   • Half-year terminal value discounting vs. full-year horizon discounting
   • Treatment of capitalized software in PP&E vs. Intangible asset schedules
   • Multi-year tax NOL valuation allowance burn schedules

3. Professional Judgment / Rubric Review (Non-Deterministic)
   • Peer group selection boundaries (pure-play observability vs. broad infra)
   • Terminal growth rate selection (2.5% vs. 3.0% vs. 3.5%)
   • Long-term sustainable SaaS operating margin equilibrium (24% vs. 28%)
```

---

## 14. Grader Reuse & Parameterization Analysis

To evaluate whether the benchmark architecture is truly modular, we analyze the degree of code reuse across all 10 graders:

| Grader | Architecture Status | Modification Required for Meridian (Case 2) |
|---|:---:|---|
| `source_fidelity` | **Direct Reuse (1/10)** | Zero code changes. Parameterized via case sources and metadata. |
| `revenue_forecast` | **Direct Reuse (2/10)** | Zero code changes. Evaluates growth bounds against case metadata. |
| `wacc` | **Direct Reuse (3/10)** | Zero code changes. Evaluates CAPM and capital structure weights via case config. |
| `enterprise_value` | **Direct Reuse (4/10)** | Zero code changes. Sums PV(UFCF) + PV(TV) deterministically. |
| `consistency` | **Direct Reuse (5/10)** | Zero code changes. Verifies headline matches model schedules. |
| `terminal_value` | **Parameterized (6/10)** | Parameterized to support `mid_year` ($t=0.5..4.5$) vs `end_of_year` ($t=1..5$) and $t=5.0$ TV discounting. |
| `equity_bridge` | **Parameterized (7/10)** | Parameterized to support Net Cash positive balances ($\text{Equity} = \text{EV} + \text{Net Cash}$). |
| `comps` | **Extended (8/10)** | Extended to accept `EV/Revenue` as primary multiple alongside `EV/EBITDA`. |
| `margin_forecast` | **Extended (9/10)** | Extended to verify SaaS SBC addback invariant: $\text{Adj EBITDA} = \text{EBIT} + \text{SBC} + \text{D\&A}$. |
| `free_cash_flow` | **Extended (10/10)** | Extended to support capitalized software and deferred revenue working capital items. |

**Architectural Grader Reuse Breakdown**:
- **Direct Code Reuse**: **5 / 10 graders (50.0%)** execute against Meridian with zero logic modifications.
- **Parameterized / Extended**: **5 / 10 graders (50.0%)** accept configuration parameters or modular domain extensions.

---

## 15. Benchmark Overfitting Audit: Northstar-Specific Risks

We identify the following hard-coded assumptions in the existing repository that must be cleanly generalized in Milestone 4B:

1. **Equity Bridge Sign Assumption**: Grader and schemas must handle both $NetDebt > 0$ and $NetDebt < 0$ without asserting debt exceeds cash.
2. **Trading Comps Multiple Keys**: Schema and grader must allow case configuration to designate `EV_REVENUE` or `EV_EBITDA` as the headline trading comp metric.
3. **Discounting Exponents**: Terminal value and DCF helpers must read `discounting_convention` (`"mid_year"` vs `"end_of_year"`) from `case.json`.
4. **SBC & Capitalized Software Fields**: The canonical `Submission` schema should cleanly accommodate optional SaaS line items without breaking Northstar.

---

## 16. Milestone 4 Experimental Roadmap

```text
Milestone 4A: Second Case Design (This Document)
   └── Specify Meridian profile, accounting mechanics, and generalization hypotheses.

Milestone 4B: Benchmark Implementation (No Live Models)
   └── Implement `cases/meridian-v1/`, deterministic gold outputs, parameterized graders, and 10 corrupted fixtures.

Milestone 4C: Direct Analyst Baseline on Meridian
   └── Run 10 trials (Thinking Off) and 10 trials (Thinking High) to establish baseline reliability on SaaS.

Milestone 4D: Structured Analyst Workflow on Meridian
   └── Evaluate whether the 8-stage financial workflow eliminates SaaS structural defects without case-specific hacks.

Milestone 4E: Deterministic Feedback Repair on Meridian
   └── Test controlled repair across all 10 SaaS failure modes.
```

---

## 17. Key Generalization Metrics

To evaluate architectural generalization, Milestone 4 will measure:

1. **Grader Reuse Rate**: Proportion of existing graders that execute against Meridian without code rewrites.
2. **Workflow Reuse Rate**: Did the structured prompt workflow guide the model through SaaS valuation without rewriting the prompt structure?
3. **Cross-Case Reliability Parity**:
   - Does extended reasoning still leave systematic blind spots on SaaS (e.g. ARR confusion or Net Cash inversion)?
   - Does structured workflow reduce hard failures by $\ge 50\%$ as observed in Northstar?
   - Does deterministic feedback achieve $\ge 90\%$ repair success on SaaS failure modes?

---

## 18. Success & Falsification Criteria

### What Counts as Success:
- The benchmark harness cleanly grades both Northstar (manufacturing) and Meridian (SaaS) from the same codebase.
- Structured prompting and deterministic feedback improve reliability on Meridian without hard-coding SaaS-specific prompt templates.
- Grader extensions do not break or alter any existing Milestone 0–3B tests (100% backward compatibility).

### What Would Falsify the Generalization Hypothesis:
- If structured reasoning fails to prevent SaaS-specific errors (e.g. ARR confusion occurs in 100% of structured runs).
- If deterministic feedback cannot repair multi-schedule propagating errors (e.g. capitalized software cascade breaks 1-shot repair).
- If grading SaaS requires a completely separate codebase rather than parameterized domain invariants.

---

## 19. Design Review & Self-Audit Checklist

- [x] **1. Materially Different**: Meridian tests SaaS, Net Cash, high growth, low EBITDA, capitalized software, SBC, and mid-year discounting.
- [x] **2. Realistic Traps**: Embedded traps (ARR vs revenue, deferred revenue sign, net cash inversion) mirror common junior analyst errors.
- [x] **3. Invariant Separation**: Objective arithmetic/accounting identities are strictly isolated from valuation judgment.
- [x] **4. Clean Architecture**: Graders and workflow are designed for parameterization rather than case-specific branching.
- [x] **5. Valuation Coherence**: EV/NTM Revenue and mid-year DCF represent standard institutional technology banking practice.
- [x] **6. Falsifiability**: Clear criteria established for validating or falsifying framework generalization.

---

## Quick Navigation

- Previous: **[Chapter 10 — Experimental Results & Research Synthesis](10_results_and_findings.md)**
- Roadmap: **[Chapter 06 — Where This Can Go](06_where_this_can_go.md)**
- Benchmark Root: **[README.md](../README.md)**
