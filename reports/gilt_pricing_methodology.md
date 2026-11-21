# Conventional fixed-rate gilt pricing — educational prototype

Run `python gilt_pricing.py --face 100 --coupon-percent 4 --yield-percent 4 --years 10`.

The standalone module calculates discounted annual cash flows, solves yield-to-maturity by bisection, and reports Macaulay duration, modified duration, analytical convexity, central-difference DV01 and symmetric yield-shock prices. All prices are per face value in the input currency.

**Important:** UK conventional gilts generally pay coupons semi-annually. This intentionally simplified **annual-coupon** model assumes settlement on a coupon date, annual compounding, no accrued interest and no ex-dividend convention. It is **not** a UK gilt clean/dirty settlement engine and must not be used to value live gilts, strips, inflation-linked bonds or trading positions. Next phase: actual coupon calendars, day-count rules, accrued interest and curve-based discounting.
