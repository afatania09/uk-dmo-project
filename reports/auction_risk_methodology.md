# Illustrative auction funding-cost stress

This extends the issuance frontier and Monte Carlo scenarios with a **transparent hypothetical auction concession** sensitivity. It is not an empirical estimate of UK gilt auction pricing.

Run:

```bash
python auction_risk.py examples/illustrative_yields.csv --bid-cover 1.5 --tail-bp 2 --shock-bp 100
python -m unittest discover -s tests -v
```

An equal-weight allocation across 2, 5, 10 and 30-year proxy tenors is the CLI baseline. For each tenor, principal multiplied by `base yield + parallel shock + (tail/bid cover)` gives annual stressed **coupon-equivalent financing cost** (not the contractual coupon of an actual issued gilt). This simplification ignores auction prices, dirty-price settlement, accrued interest, actual coupon rates, reopening mechanics, market liquidity, DV01, convexity and market-implied stochastic dynamics. Inputs in `examples/illustrative_yields.csv` are synthetic, not live gilt curves.

The purpose is to isolate and discuss funding-cost sensitivity and decision trade-offs; the bid-cover formula must be empirically estimated before any investment or policy use.
