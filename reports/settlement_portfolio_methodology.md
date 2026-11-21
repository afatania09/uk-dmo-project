# Settlement-aware funding-risk dashboard

From the repository root:

```bash
python settlement_portfolio.py examples/illustrative_settlement_portfolio.csv --settlement 2026-11-21 --output outputs/settlement_portfolio
```

Open `outputs/settlement_portfolio/index.html` in a browser. The script also writes `summary.json`.

This extends the previous annual-coupon funding-risk dashboard using `gilt_settlement.settlement_risk` for every instrument. Each CSV row specifies a maturity date, coupon, yield and face value in **millions**. Clean, dirty, accrued, shocked prices and DV01 are summed across positions; portfolio modified duration is dirty-market-value weighted. A single common settlement date is applied to all securities.

**Scope:** Synthetic annual yield assumptions and conventional fixed-rate **semiannual** coupon proxies. This is not a live gilt inventory or a UK DMO forecast. The pricing prototype does not yet support ex-dividend entitlements, irregular coupons, settlement holidays, instrument-specific calendars, or curve bootstrapping. The older `funding_risk_dashboard.py` remains as a separate annual-coupon baseline for comparison; do not mix its outputs with the settlement-aware portfolio.
