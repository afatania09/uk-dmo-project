"""Fixed-rate conventional gilt clean-price, yield and interest-rate risk analytics.

Simplified annual coupon periods, settlement on a coupon date, no accrued interest.
Not suitable for actual gilt settlement or index-linked instruments.
"""
import argparse
import json
import math

def _validate(face, coupon_rate, yield_rate, years):
    if not all(math.isfinite(x) for x in (face, coupon_rate, yield_rate)):
        raise ValueError("Inputs must be finite")
    if face <= 0 or coupon_rate < 0 or yield_rate <= -1 or not isinstance(years, int) or years < 1:
        raise ValueError("Invalid face, coupon, yield or maturity")

def price(face, coupon_rate, yield_rate, years):
    _validate(face, coupon_rate, yield_rate, years)
    coupon = face * coupon_rate
    return sum(coupon / (1 + yield_rate) ** t for t in range(1, years + 1)) + face / (1 + yield_rate) ** years

def yield_to_maturity(clean_price, face, coupon_rate, years, tolerance=1e-11):
    if not math.isfinite(clean_price) or clean_price <= 0:
        raise ValueError("Price must be positive and finite")
    _validate(face, coupon_rate, 0.0, years)
    lo, hi = -0.99, 1.0
    while price(face, coupon_rate, hi, years) > clean_price:
        hi = 2 * hi + 1
        if hi > 1e8:
            raise ValueError("Unable to bracket yield")
    for _ in range(200):
        mid = (lo + hi) / 2
        if abs(price(face, coupon_rate, mid, years) - clean_price) < tolerance:
            return mid
        if price(face, coupon_rate, mid, years) > clean_price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def risk(face, coupon_rate, yield_rate, years, shock_bp=100):
    _validate(face, coupon_rate, yield_rate, years)
    if not math.isfinite(shock_bp) or shock_bp < 0:
        raise ValueError("Shock must be nonnegative")
    p = price(face, coupon_rate, yield_rate, years)
    cashflows = [face * coupon_rate] * years
    cashflows[-1] += face
    mac = sum(t * cf / (1 + yield_rate) ** t for t, cf in enumerate(cashflows, 1)) / p
    mod = mac / (1 + yield_rate)
    convexity = sum(t * (t + 1) * cf / (1 + yield_rate) ** (t + 2)
                    for t, cf in enumerate(cashflows, 1)) / p
    step = 0.0001
    dv01 = (price(face, coupon_rate, yield_rate - step, years) -
            price(face, coupon_rate, yield_rate + step, years)) / 2
    shock = shock_bp / 10000
    if yield_rate - shock <= -1:
        raise ValueError("Negative shock crosses admissible yield bound")
    return {"price_per_face": round(p, 8), "macaulay_duration_years": round(mac, 8),
            "modified_duration": round(mod, 8), "convexity": round(convexity, 8),
            "dv01_per_face": round(dv01, 8),
            "price_up_shock": round(price(face, coupon_rate, yield_rate + shock, years), 8),
            "price_down_shock": round(price(face, coupon_rate, yield_rate - shock, years), 8),
            "shock_bp": shock_bp}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--face", type=float, default=100)
    p.add_argument("--coupon-percent", type=float, default=4)
    p.add_argument("--yield-percent", type=float, default=4)
    p.add_argument("--years", type=int, default=10)
    p.add_argument("--shock-bp", type=float, default=100)
    a = p.parse_args()
    print(json.dumps(risk(a.face, a.coupon_percent / 100,
                          a.yield_percent / 100, a.years, a.shock_bp), indent=2))

if __name__ == "__main__":
    main()
