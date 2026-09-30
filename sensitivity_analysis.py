"""Run the illustrative rollover model across a rate-process assumption grid."""

import argparse
import csv
import json
from pathlib import Path

from issuance_scenarios import load_strategies
from rate_simulation import load_proxy_strategy, run_simulation


def run_grid(strategies, simulations=2000, seed=20260930, horizon=30):
    rows = []
    for persistence in (0.50, 0.75, 0.90):
        for volatility in (50, 100, 150):
            result = run_simulation(strategies, simulations=simulations,
                                    seed=seed, horizon=horizon,
                                    persistence=persistence,
                                    annual_volatility_bp=volatility)
            for name, metrics in result["strategies"].items():
                rows.append({"persistence": persistence,
                             "volatility_bp": volatility,
                             "strategy": name} | metrics)
    return rows


def summarize(rows):
    names = sorted({r["strategy"] for r in rows})
    return {name: {
        "lowest_p95_gbp_millions": min(r["p95_gbp_millions"] for r in rows if r["strategy"] == name),
        "highest_p95_gbp_millions": max(r["p95_gbp_millions"] for r in rows if r["strategy"] == name),
        "lowest_tail_width_gbp_millions": min(r["tail_width_p95_minus_median_gbp_millions"] for r in rows if r["strategy"] == name),
        "highest_tail_width_gbp_millions": max(r["tail_width_p95_minus_median_gbp_millions"] for r in rows if r["strategy"] == name),
    } for name in names}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("strategies_csv", type=Path)
    p.add_argument("--remit-csv", required=True, type=Path)
    p.add_argument("--yield-csv", required=True, type=Path)
    p.add_argument("--simulations", type=int, default=2000)
    p.add_argument("--output", type=Path, default=Path("outputs/sensitivity"))
    args = p.parse_args()
    strategies = load_strategies(args.strategies_csv)
    strategies["2026-27 allocated conventional proxy"] = load_proxy_strategy(
        args.remit_csv, args.yield_csv)
    rows = run_grid(strategies, simulations=args.simulations)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "sensitivity_grid.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    result = {"grid": {"persistence": [0.5, 0.75, 0.9],
                       "annual_volatility_bp": [50, 100, 150],
                       "simulations_per_cell": args.simulations},
              "strategy_ranges": summarize(rows)}
    (args.output / "sensitivity_summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
