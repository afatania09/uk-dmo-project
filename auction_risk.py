"""Portfolio auction allocation stress test using illustrative yield assumptions.

This is a marginal issuance comparison, not an official DMO pricing or policy model.
"""
import argparse
import csv
import json
import math
from pathlib import Path
from strategy_frontier import TENORS, load_yields

def analyse(mix, yields, financing_millions=10000, bid_cover=1.5, tail_bp=2.0,
            parallel_shock_bp=100):
    if set(mix) != set(TENORS) or set(yields) != set(TENORS):
        raise ValueError("Exactly the supported tenors must be provided")
    if any(not math.isfinite(float(v)) or v < 0 for v in mix.values()):
        raise ValueError("Allocation weights must be finite and nonnegative")
    if abs(sum(mix.values()) - 1) > 1e-9 or financing_millions <= 0:
        raise ValueError("Weights must sum to one and financing must be positive")
    if not all(math.isfinite(v) for v in (financing_millions, bid_cover, tail_bp, parallel_shock_bp)):
        raise ValueError("Nonfinite stress input")
    if bid_cover <= 0 or tail_bp < 0 or parallel_shock_bp < 0:
        raise ValueError("Invalid bid-cover or yield stress")
    # Transparent simplifying assumption: weaker cover creates a larger yield concession.
    concession_bp = tail_bp / bid_cover
    rows = []
    for tenor in TENORS:
        principal = financing_millions * mix[tenor]
        base = yields[tenor]
        effective = base + concession_bp / 10000
        rows.append({"tenor_years": tenor, "principal_gbp_millions": round(principal, 3),
                     "base_yield_percent": round(base * 100, 4),
                     "stressed_yield_percent": round((effective + parallel_shock_bp / 10000) * 100, 4),
                     "annual_base_coupon_gbp_millions": round(principal * base, 4),
                     "annual_stressed_coupon_gbp_millions": round(principal * (effective + parallel_shock_bp / 10000), 4)})
    return {"assumptions": {"financing_gbp_millions": financing_millions,
             "bid_cover_proxy": bid_cover, "auction_tail_bp": tail_bp,
             "parallel_shock_bp": parallel_shock_bp,
             "yield_concession_bp": concession_bp,
             "note": "Bid-cover to concession formula is deliberately hypothetical; no empirical calibration."},
            "rows": rows,
            "base_annual_coupon_gbp_millions": round(sum(r["annual_base_coupon_gbp_millions"] for r in rows), 4),
            "stressed_annual_coupon_gbp_millions": round(sum(r["annual_stressed_coupon_gbp_millions"] for r in rows), 4)}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("yield_csv", type=Path)
    p.add_argument("--financing-millions", type=float, default=10000)
    p.add_argument("--bid-cover", type=float, default=1.5)
    p.add_argument("--tail-bp", type=float, default=2)
    p.add_argument("--shock-bp", type=float, default=100)
    p.add_argument("--output", type=Path, default=Path("outputs/auction_risk.json"))
    a = p.parse_args()
    mix = {2: 0.25, 5: 0.25, 10: 0.25, 30: 0.25}
    result = analyse(mix, load_yields(a.yield_csv), a.financing_millions,
                     a.bid_cover, a.tail_bp, a.shock_bp)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
