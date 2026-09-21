"""Compare illustrative fixed-rate conventional gilt issuance strategies."""

import argparse
import csv
import json
from pathlib import Path


TENORS = (2, 5, 10, 30)


def load_strategies(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or ()) != {"strategy", "tenor_years", "share", "yield_percent"}:
            raise ValueError("Expected strategy,tenor_years,share,yield_percent")
        strategies = {}
        for line, row in enumerate(reader, 2):
            try:
                name = row["strategy"].strip()
                tenor, share, annual_yield = int(row["tenor_years"]), float(row["share"]), float(row["yield_percent"])
                if not name or tenor not in TENORS or not 0 <= share <= 1 or not 0 <= annual_yield <= 100:
                    raise ValueError("invalid strategy, tenor, share or yield")
                if tenor in strategies.setdefault(name, {}):
                    raise ValueError("duplicate tenor in strategy")
                strategies[name][tenor] = (share, annual_yield / 100)
            except (ValueError, AttributeError, TypeError) as exc:
                raise ValueError(f"CSV line {line}: {exc}") from exc
    if not strategies:
        raise ValueError("No strategies found")
    for name, legs in strategies.items():
        if abs(sum(share for share, _ in legs.values()) - 1) > 1e-9:
            raise ValueError(f"Strategy {name!r} shares must add to 1")
    return strategies


def evaluate(legs, financing_millions, horizon, rollover_shock_bp=0):
    """Par issuance; annual coupons; same-tenor rollover at shocked initial yield."""
    if financing_millions <= 0 or horizon < 1:
        raise ValueError("Financing and horizon must be positive")
    if any(rate + rollover_shock_bp / 10000 < 0 for _, rate in legs.values()):
        raise ValueError("Shocked rollover yield must not be negative")
    weighted_yield = sum(share * rate for share, rate in legs.values())
    annual = []
    for year in range(1, horizon + 1):
        coupon = 0.0
        for tenor, (share, initial_rate) in legs.items():
            # Rollover occurs at maturity, after that year's original coupon.
            previous_rollovers = (year - 1) // tenor
            rate = initial_rate + (rollover_shock_bp / 10000 if previous_rollovers else 0)
            coupon += financing_millions * share * rate
        annual.append(coupon)
    return {
        "weighted_initial_yield_percent": round(weighted_yield * 100, 4),
        "weighted_average_maturity_years": round(sum(tenor * share for tenor, (share, _) in legs.items()), 3),
        "original_principal_maturing_within_five_years_gbp_millions": round(financing_millions * sum(share for tenor, (share, _) in legs.items() if tenor <= 5), 3),
        "cumulative_coupon_over_horizon_gbp_millions": round(sum(annual), 3),
        "annual_coupon_gbp_millions": [round(x, 3) for x in annual],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("strategies_csv", type=Path)
    p.add_argument("--financing-millions", type=float, default=100000)
    p.add_argument("--horizon", type=int, default=10)
    p.add_argument("--rollover-shock-bp", type=float, default=200)
    p.add_argument("--output", type=Path, default=Path("outputs"))
    args = p.parse_args()
    scenarios = load_strategies(args.strategies_csv)
    result = {
        "assumptions": {"financing_gbp_millions": args.financing_millions, "horizon_years": args.horizon,
                        "rollover_shock_bp": args.rollover_shock_bp, "coupon_frequency": "annual simplified",
                        "yield_source": "illustrative inputs; not observed gilt yields"},
        "strategies": {name: {"base": evaluate(legs, args.financing_millions, args.horizon),
                              "rollover_shock": evaluate(legs, args.financing_millions, args.horizon, args.rollover_shock_bp)}
                       for name, legs in scenarios.items()},
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "strategy_comparison.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
