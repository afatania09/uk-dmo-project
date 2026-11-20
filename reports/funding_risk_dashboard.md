# Funding risk dashboard

Reproduce the illustrative portfolio from the repository root:

```bash
python funding_risk_dashboard.py examples/illustrative_funding_portfolio.csv --output outputs/funding_risk
```

Open `outputs/funding_risk/index.html` in a browser. The dashboard is a **standalone static HTML file** and does not require a server. The adjacent `summary.json` provides machine-readable results.

## Inputs and interpretation

CSV: `instrument,face_millions,coupon_percent,yield_percent,years`. Market value is the discounted present value of annual cash flows in **millions**. Portfolio duration and convexity are market-value weighted; DV01 is additive. The shock is a parallel yield change for each synthetic bond proxy, not a calibrated curve or auction model.

**Limitations:** No semiannual UK gilt coupons, day-count conventions, accrued interest, index linkage, tax, liquidity premia, stochastic curve calibration or real UK DMO issuance forecast. This tool is an educational risk exhibit only. For live gilts, replace proxy pricing with a date-aware clean/dirty pricing engine and source-controlled market data.
