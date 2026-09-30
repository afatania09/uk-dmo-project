"""Reproducible Monte Carlo rollover-cost scenarios for illustrative gilt mixes.

The model is educational: it is not calibrated to market-implied probabilities.
"""

import argparse
import csv
import json
import math
import random
from pathlib import Path

from issuance_scenarios import load_strategies


def quantile(values, probability):
    if not values or not 0 <= probability <= 1:
        raise ValueError("Invalid quantile input")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (position - lower) * (ordered[upper] - ordered[lower])


def simulate_path(rng, horizon, persistence, long_run_shift, annual_volatility):
    """Annual parallel yield-curve shift, in decimal rate units."""
    shift = 0.0
    result = [shift]
    for _ in range(horizon):
        shift = (long_run_shift + persistence * (shift - long_run_shift)
                 + annual_volatility * rng.gauss(0, 1))
        result.append(shift)
    return result


def path_coupon_cost(legs, financing_millions, horizon, shifts, rate_floor=0.0):
    """Coupons on a fixed principal cohort, rerated only when each leg rolls."""
    total = 0.0
    annual = []
    for year in range(1, horizon + 1):
        coupon = 0.0
        for tenor, (share, base_rate) in legs.items():
            last_rollover = ((year - 1) // tenor) * tenor
            rate = max(rate_floor, base_rate + shifts[last_rollover])
            coupon += financing_millions * share * rate
        annual.append(coupon)
        total += coupon
    return total, annual


def run_simulation(strategies, simulations=5000, seed=20260930,
                   financing_millions=100000, horizon=30, persistence=0.75,
                   long_run_shift_bp=0, annual_volatility_bp=100,
                   rate_floor_percent=0):
    if simulations < 100 or financing_millions <= 0 or horizon < 1:
        raise ValueError("Need at least 100 simulations and positive financing/horizon")
    if not 0 <= persistence < 1 or annual_volatility_bp < 0:
        raise ValueError("Persistence must be in [0,1); volatility non-negative")
    rng = random.Random(seed)
    totals = {name: [] for name in strategies}
    # Common random paths make pairwise strategy comparisons less noisy.
    for _ in range(simulations):
        shifts = simulate_path(rng, horizon, persistence,
                               long_run_shift_bp / 10000,
                               annual_volatility_bp / 10000)
        for name, legs in strategies.items():
            total, _ = path_coupon_cost(legs, financing_millions, horizon,
                                        shifts, rate_floor_percent / 100)
            totals[name].append(total)
    results = {}
    for name, values in totals.items():
        results[name] = {
            "mean_cumulative_coupon_gbp_millions": round(sum(values) / len(values), 3),
            "p05_gbp_millions": round(quantile(values, 0.05), 3),
            "median_gbp_millions": round(quantile(values, 0.50), 3),
            "p95_gbp_millions": round(quantile(values, 0.95), 3),
            "tail_width_p95_minus_median_gbp_millions": round(
                quantile(values, 0.95) - quantile(values, 0.50), 3),
        }
    return {
        "assumptions": {
            "simulations": simulations, "seed": seed,
            "financing_gbp_millions": financing_millions,
            "horizon_years": horizon, "ar1_persistence": persistence,
            "long_run_parallel_shift_bp": long_run_shift_bp,
            "annual_parallel_shift_volatility_bp": annual_volatility_bp,
            "rate_floor_percent": rate_floor_percent,
            "probability_calibration": "illustrative; not fitted to market or historical data",
            "cost_measure": "undiscounted annual coupons on constant principal",
        },
        "strategies": results,
    }


def write_chart(result, path):
    rows = result["strategies"]
    names = list(rows)
    maximum = max(v["p95_gbp_millions"] for v in rows.values()) or 1
    width, height = 820, 130 + 90 * len(names)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="185" y="30" font-family="sans-serif" font-size="18">30-year cumulative coupon distribution (£m)</text>',
             '<text x="185" y="50" font-family="sans-serif" font-size="11">Illustrative AR(1) parallel-rate scenarios; bars show p05–p95 and median</text>']
    for i, name in enumerate(names):
        y = 90 + 80 * i
        v = rows[name]
        scale = 570 / maximum
        x05, x50, x95 = (185 + v[k] * scale for k in
                         ("p05_gbp_millions", "median_gbp_millions", "p95_gbp_millions"))
        parts += [f'<text x="20" y="{y+5}" font-family="sans-serif" font-size="13">{name}</text>',
                  f'<line x1="{x05:.2f}" y1="{y}" x2="{x95:.2f}" y2="{y}" stroke="#4f7993" stroke-width="12"/>',
                  f'<circle cx="{x50:.2f}" cy="{y}" r="6" fill="#b84622"/>',
                  f'<text x="{x95+7:.2f}" y="{y+4}" font-family="sans-serif" font-size="10">p95 {v["p95_gbp_millions"]:,.0f}</text>']
    parts.append('</svg>')
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def load_proxy_strategy(remit_path, yield_path):
    """Map DMO short/medium/long allocated conventional amounts to 2/10/30y."""
    from remit_analysis import read_remit
    remit = {r["sector"]: r["total"] for r in read_remit(remit_path)}
    with open(yield_path, newline="", encoding="utf-8-sig") as handle:
        yields = {int(r["tenor_years"]): float(r["yield_percent"]) / 100
                  for r in csv.DictReader(handle)}
    total = sum(remit[s] for s in ("short_conventional",
                                   "medium_conventional_including_green",
                                   "long_conventional"))
    return {2: (remit["short_conventional"] / total, yields[2]),
            10: (remit["medium_conventional_including_green"] / total, yields[10]),
            30: (remit["long_conventional"] / total, yields[30])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("strategies_csv", type=Path)
    parser.add_argument("--remit-csv", type=Path)
    parser.add_argument("--yield-csv", type=Path)
    parser.add_argument("--simulations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--volatility-bp", type=float, default=100)
    parser.add_argument("--persistence", type=float, default=0.75)
    parser.add_argument("--output", type=Path, default=Path("outputs/monte_carlo"))
    args = parser.parse_args()
    strategies = load_strategies(args.strategies_csv)
    if bool(args.remit_csv) != bool(args.yield_csv):
        parser.error("--remit-csv and --yield-csv must be supplied together")
    if args.remit_csv:
        strategies["2026-27 allocated conventional proxy"] = load_proxy_strategy(
            args.remit_csv, args.yield_csv)
    result = run_simulation(strategies, args.simulations, args.seed,
                            horizon=args.horizon,
                            persistence=args.persistence,
                            annual_volatility_bp=args.volatility_bp)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "simulation_summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_chart(result, args.output / "simulation_distribution.svg")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
