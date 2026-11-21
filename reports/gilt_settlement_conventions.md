# Conventional gilt settlement pricing prototype

Run:

```bash
python gilt_settlement.py --settlement 2026-11-21 --maturity 2036-09-07 --coupon-percent 4.25 --yield-percent 4.5
```

Unlike the existing annual-coupon `gilt_pricing.py`, this module generates a backwards six-month coupon calendar from maturity, prices each future cash flow using semiannual yield compounding and fractional coupon periods, calculates accrued coupon interest on an actual-days/actual-coupon-period basis, and reports clean/dirty prices, yield inversion and finite-difference DV01.

**Scope warning:** This is a **conventional fixed-rate educational prototype**, not a certified UK gilt pricing library. In particular it omits UK gilt ex-dividend entitlement rules, settlement business days, holiday adjustments, irregular first/last coupons, accrued-interest rounding, actual gilt-specific coupon schedules, market yield quotation nuances, index-linked principal/coupon adjustments and strips. It assumes a regular semiannual schedule anchored to maturity and simple Actual/Actual coupon-period accrual. Results must not be represented as executable gilt prices.

## Next technical gates

- Validate against independent published gilt price examples and market convention references.
- Model ex-dividend periods and correct coupon entitlement.
- Support issuance/first coupon dates and stub periods.
- Integrate instrument-level dates into the portfolio dashboard and add a calibrated zero-coupon curve.
