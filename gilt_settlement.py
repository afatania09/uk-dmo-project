"""Date-aware conventional fixed-rate gilt valuation prototype.

Semiannual coupon schedule, Actual/Actual period fraction, dirty/clean price,
accrued interest, YTM and finite-difference risk. Calendar-day settlement only.
No ex-dividend, holidays, tax, index-linking or market conventions certification.
"""
import argparse
import calendar
import datetime as dt
import json
import math

def add_months(date, months, anchor_day=None):
    total = date.year * 12 + date.month - 1 + months
    year, month = divmod(total, 12)
    month += 1
    day = min(anchor_day or date.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)

def coupon_schedule(settlement, maturity):
    if not settlement < maturity:
        raise ValueError("Settlement must precede maturity")
    dates = [maturity]
    cursor = maturity
    while cursor > settlement:
        cursor = add_months(cursor, -6, maturity.day)
        dates.append(cursor)
        if len(dates) > 300:
            raise ValueError("Maturity too far away")
    dates.reverse()
    return dates

def value(settlement, maturity, coupon_percent, yield_percent, face=100):
    if not isinstance(settlement, dt.date) or not isinstance(maturity, dt.date):
        raise ValueError("Dates must be datetime.date")
    if not all(math.isfinite(x) for x in (coupon_percent, yield_percent, face)):
        raise ValueError("Numeric inputs must be finite")
    if face <= 0 or coupon_percent < 0 or yield_percent <= -200:
        raise ValueError("Invalid face, coupon or semiannual yield")
    dates = coupon_schedule(settlement, maturity)
    previous, next_coupon = dates[0], dates[1]
    fraction_elapsed = (settlement - previous).days / (next_coupon - previous).days
    coupon = face * coupon_percent / 200
    accrued = coupon * fraction_elapsed
    y = yield_percent / 200
    flows = []
    for n, payment_date in enumerate(dates[1:], 1):
        periods = n - fraction_elapsed
        cash = coupon + (face if payment_date == maturity else 0)
        pv = cash / (1 + y) ** periods
        flows.append((payment_date.isoformat(), periods, cash, pv))
    dirty = sum(x[3] for x in flows)
    return {"clean_price": dirty - accrued, "dirty_price": dirty,
            "accrued_interest": accrued, "previous_coupon": previous.isoformat(),
            "next_coupon": next_coupon.isoformat(), "cashflows": flows}

def solve_yield(settlement, maturity, coupon_percent, clean_price, face=100):
    if not math.isfinite(clean_price) or clean_price <= 0:
        raise ValueError("Clean price must be positive")
    lo, hi = -199.9, 100.0
    def f(y):
        return value(settlement, maturity, coupon_percent, y, face)["clean_price"]
    while f(hi) > clean_price:
        hi = hi * 2 + 200
        if hi > 1e9:
            raise ValueError("Cannot bracket yield")
    for _ in range(150):
        mid = (lo + hi) / 2
        if f(mid) > clean_price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def settlement_risk(settlement, maturity, coupon_percent, yield_percent, face=100, shock_bp=100):
    if not math.isfinite(shock_bp) or shock_bp < 0 or yield_percent - shock_bp / 100 <= -200:
        raise ValueError("Invalid shock")
    base = value(settlement, maturity, coupon_percent, yield_percent, face)
    up = value(settlement, maturity, coupon_percent, yield_percent + shock_bp / 100, face)
    down = value(settlement, maturity, coupon_percent, yield_percent - shock_bp / 100, face)
    step = .01
    p_down = value(settlement, maturity, coupon_percent, yield_percent - step, face)["dirty_price"]
    p_up = value(settlement, maturity, coupon_percent, yield_percent + step, face)["dirty_price"]
    dv01 = (p_down - p_up) / 2
    duration = dv01 / base["dirty_price"] / .0001
    return {k: base[k] for k in ("clean_price", "dirty_price", "accrued_interest",
                                 "previous_coupon", "next_coupon")} | {
        "modified_duration": duration, "dv01": dv01,
        "clean_price_yield_up": up["clean_price"],
        "clean_price_yield_down": down["clean_price"], "shock_bp": shock_bp}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--settlement", required=True, help="YYYY-MM-DD")
    parser.add_argument("--maturity", required=True, help="YYYY-MM-DD")
    parser.add_argument("--coupon-percent", type=float, required=True)
    parser.add_argument("--yield-percent", type=float, required=True)
    parser.add_argument("--face", type=float, default=100)
    parser.add_argument("--shock-bp", type=float, default=100)
    args = parser.parse_args()
    print(json.dumps(settlement_risk(dt.date.fromisoformat(args.settlement),
                                     dt.date.fromisoformat(args.maturity),
                                     args.coupon_percent, args.yield_percent,
                                     args.face, args.shock_bp), indent=2))

if __name__ == "__main__":
    main()
