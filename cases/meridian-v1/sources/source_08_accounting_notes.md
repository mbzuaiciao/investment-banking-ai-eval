# Meridian Cloud Systems, Inc. — Valuation & Accounting Policy Notes

**Valuation Date**: June 30, 2026  
**Auditor**: Deloitte & Touche LLP  

---

## 1. DCF Discounting Timing Convention

- **Explicit Forecast Period (2026E–2030E)**:
  Because subscription revenues, upfront annual customer billings, and operating cash flows occur continuously throughout the calendar year, the valuation model specifies a **Mid-Year Discounting Convention**:
  
  $$\text{Discount Factor}_t = \frac{1}{(1 + \text{WACC})^{t - 0.5}} \quad \text{for year index } t \in \{1, 2, 3, 4, 5\}$$
  
  - **2026E ($t=1$)**: Discount Factor = $(1 + \text{WACC})^{-0.5}$
  - **2027E ($t=2$)**: Discount Factor = $(1 + \text{WACC})^{-1.5}$
  - **2028E ($t=3$)**: Discount Factor = $(1 + \text{WACC})^{-2.5}$
  - **2029E ($t=4$)**: Discount Factor = $(1 + \text{WACC})^{-3.5}$
  - **2030E ($t=5$)**: Discount Factor = $(1 + \text{WACC})^{-4.5}$

- **Terminal Value Horizon Discounting**:
  The perpetual-growth terminal value is established at the end of the 5-year forecast period (December 31, 2030, $t = 5.0$).
  The present value of the Terminal Value is discounted from the 5.0-year horizon:
  
  $$\text{PV(Terminal Value)} = \frac{\text{Terminal Value}_{2030}}{(1 + \text{WACC})^{5.0}}$$
  
  *Note: Mid-year discounting of explicit annual FCFs does not mean the terminal value uses 4.5 years; the terminal value perpetuity resides at horizon $t = 5.0$.*

---

## 2. Capitalization of Internal-Use Software (ASC 350-40)

- Software development expenditures meeting capitalization criteria under ASC 350-40 are capitalized on the balance sheet as intangible software assets and amortized over a 3-year useful life.
- **Cash Flow Presentation**: Total capital investments equal **5.0% of revenue** (comprising 1.5% for physical PP&E capex and 3.5% for capitalized internal software).
- **Double Counting Rule**: Capitalized software is already excluded from operating expenses (capitalized on balance sheet); it must not be expensed in GAAP EBIT and then deducted again in capital investment schedules.

---

## 3. Perpetual Growth Rate ($g$) & Terminal WACC

- **Terminal Growth Rate ($g$)**: **3.0%** per annum.
- **Terminal FCF**: $\text{UFCF}_{2030} \times (1 + 0.030)$.
- **Terminal Value at Horizon**: $\text{Terminal FCF} / (\text{WACC} - 0.030)$.
