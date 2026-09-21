"""Enumerate illustrative issuance mixes and compare cost with redemption concentration.

No forecast probabilities or market yield inputs are inferred from the DMO D8B stock table.
"""

import argparse
import csv
import json
from pathlib import Path

from d8b_analysis import read_profile
from issuance_scenarios import evaluate


TENORS = (2, 5, 10, 30)


def load_yields(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or ()) != {"tenor_years", "yield_percent"}:
            raise ValueError("Yield CSV must have tenor_years,yield_percent")
        result = {}
        for row in reader:
            tenor, rate = int(row["tenor_years"]), float(row["yield_percent"])
            if tenor in result or tenor not in TENORS or not 0 <= rate <= 100:
                raise ValueError("Duplicate, unsupported tenor or invalid yield")
            result[tenor] = rate / 100
    if set(result) != set(TENORS):
        raise ValueError(f"Need one yield per tenor: {TENORS}")
    return result


def allocations(step_percent):
    if step_percent <= 0 or 100 % step_percent:
        raise ValueError("Step must be a positive whole-number divisor of 100")
    n = 100 // step_percent
    for a in range(n + 1):
        for b in range(n - a + 1):
            for c in range(n - a - b + 1):
                yield tuple(x / n for x in (a, b, c, n - a - b - c))


def combined_redemptions(stock, shares, financing_millions, issue_fy_start, horizon):
    """Add original new principal at maturity, without forecasting further stock changes."""
    by_year = {r["start"]: r["total"] for r in stock}
    series = []
    for start in range(issue_fy_start + 1, issue_fy_start + horizon + 1):
        incremental = sum(financing_millions * share for tenor, share in zip(TENORS, shares)
                          if issue_fy_start + tenor == start)
        series.append({"financial_year": f"{start}-{start+1}",
                       "snapshot_redemptions_gbp_millions": by_year.get(start, 0),
                       "new_issuance_redemptions_gbp_millions": round(incremental, 3),
                       "combined_gbp_millions": round(by_year.get(start, 0) + incremental, 3)})
    return series


def assess(stock, yields, shares, financing_millions=100000, issue_fy_start=2026, horizon=10,
           shock_bp=200):
    legs = {tenor: (share, yields[tenor]) for tenor, share in zip(TENORS, shares)}
    initial = evaluate(legs, financing_millions, horizon)
    shocked = evaluate(legs, financing_millions, horizon, shock_bp)
    series = combined_redemptions(stock, shares, financing_millions, issue_fy_start, horizon)
    return {
        "shares": shares,
        "initial_coupon_gbp_millions_per_year": round(financing_millions * initial["weighted_initial_yield_percent"] / 100, 3),
        "weighted_average_maturity_years": initial["weighted_average_maturity_years"],
        "original_principal_due_within_five_years_gbp_millions": initial["original_principal_maturing_within_five_years_gbp_millions"],
        "horizon_base_coupons_gbp_millions": initial["cumulative_coupon_over_horizon_gbp_millions"],
        "horizon_shock_coupons_gbp_millions": shocked["cumulative_coupon_over_horizon_gbp_millions"],
        "peak_combined_redemptions_gbp_millions": max(r["combined_gbp_millions"] for r in series),
        "peak_combined_year": max(series, key=lambda r: r["combined_gbp_millions"])["financial_year"],
    }


def pareto(rows, cost_key, risk_key):
    """Minimize both dimensions; retain equal-coordinate candidates."""
    return [r for r in rows if not any(
        (s[cost_key] <= r[cost_key] and s[risk_key] <= r[risk_key]) and
        (s[cost_key] < r[cost_key] or s[risk_key] < r[risk_key]) for s in rows)]


def svg(rows, frontier, output, cost_key, risk_key):
    xmin, xmax = min(r[cost_key] for r in rows), max(r[cost_key] for r in rows)
    ymin, ymax = min(r[risk_key] for r in rows), max(r[risk_key] for r in rows)
    def xy(r):
        x = 85 + 675 * (r[cost_key] - xmin) / (xmax - xmin or 1)
        y = 465 - 360 * (r[risk_key] - ymin) / (ymax - ymin or 1)
        return x, y
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="860" height="570" viewBox="0 0 860 570">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="85" y="32" font-family="sans-serif" font-size="18">Illustrative issuance cost–risk trade-off</text>',
             '<text x="85" y="53" font-family="sans-serif" font-size="12">DMO stock snapshot + hypothetical £100bn issuance; illustrative yields</text>',
             '<line x1="85" y1="465" x2="760" y2="465" stroke="#333"/>',
             '<line x1="85" y1="105" x2="85" y2="465" stroke="#333"/>',
             '<text x="270" y="525" font-family="sans-serif" font-size="13">Annual initial coupon on new issuance (£m)</text>',
             f'<text x="14" y="380" font-family="sans-serif" font-size="13" transform="rotate(-90 14 380)">{"Peak combined redemptions" if risk_key.startswith("peak_") else "Cumulative shocked coupons"} (£m)</text>',
             f'<text x="85" y="485" font-family="sans-serif" font-size="11">{xmin:,.0f}</text>',
             f'<text x="730" y="485" font-family="sans-serif" font-size="11">{xmax:,.0f}</text>',
             f'<text x="30" y="110" font-family="sans-serif" font-size="11">{ymax:,.0f}</text>',
             f'<text x="30" y="465" font-family="sans-serif" font-size="11">{ymin:,.0f}</text>']
    for r in rows:
        x, y = xy(r)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.4" fill="#a5b5c2"/>')
    for r in frontier:
        x, y = xy(r)
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#b84622"/>')
    parts.append('<text x="85" y="550" font-family="sans-serif" font-size="11">Orange = nondominated points; no claim of policy optimality</text></svg>')
    output.write_text("\n".join(parts) + "\n", encoding="utf-8")


def run(stock_csv, yield_csv, output, financing_millions=100000, issue_fy_start=2026,
        horizon=10, shock_bp=200, step_percent=10, risk_metric="peak"):
    if financing_millions <= 0 or horizon < 1 or issue_fy_start < 1900:
        raise ValueError("Financing, horizon and issue year must be valid")
    stock, yields = read_profile(stock_csv), load_yields(yield_csv)
    if stock[0]["start"] > issue_fy_start + 1 or stock[-1]["start"] < issue_fy_start + horizon:
        raise ValueError("DMO snapshot does not cover all analysis years")
    rows = [assess(stock, yields, shares, financing_millions, issue_fy_start, horizon, shock_bp)
            for shares in allocations(step_percent)]
    if risk_metric not in ("peak", "shock_cost"):
        raise ValueError("risk_metric must be peak or shock_cost")
    cost = "initial_coupon_gbp_millions_per_year"
    risk = "peak_combined_redemptions_gbp_millions" if risk_metric == "peak" else "horizon_shock_coupons_gbp_millions"
    frontier = pareto(rows, cost, risk)
    output.mkdir(parents=True, exist_ok=True)
    cols = ["share_2y", "share_5y", "share_10y", "share_30y"] + [k for k in rows[0] if k != "shares"] + ["on_frontier"]
    with (output / "strategy_grid.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        ids = {id(r) for r in frontier}
        for r in rows:
            writer.writerow(dict(zip(cols[:4], r["shares"])) | {k: v for k, v in r.items() if k != "shares"} | {"on_frontier": id(r) in ids})
    svg(rows, frontier, output / "strategy_frontier.svg", cost, risk)
    report = {"assumptions": {"financing_gbp_millions": financing_millions, "issue_fy_start": issue_fy_start,
                              "horizon_years": horizon, "rollover_shock_bp": shock_bp,
                              "weight_step_percent": step_percent, "risk_metric": risk_metric,
                              "yield_source": "illustrative CSV inputs",
                              "stock_source": str(stock_csv), "stock_changes_after_snapshot": "excluded"},
              "candidate_count": len(rows), "frontier_count": len(frontier),
              "minimum_initial_coupon": min(rows, key=lambda r: (r[cost], r[risk])),
              "minimum_selected_risk": min(rows, key=lambda r: (r[risk], r[cost])),
              "frontier": sorted(frontier, key=lambda r: (r[cost], r[risk]))}
    (output / "strategy_frontier.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("stock_csv", type=Path)
    p.add_argument("yield_csv", type=Path)
    p.add_argument("--output", type=Path, default=Path("outputs"))
    p.add_argument("--financing-millions", type=float, default=100000)
    p.add_argument("--issue-fy-start", type=int, default=2026)
    p.add_argument("--horizon", type=int, default=10)
    p.add_argument("--rollover-shock-bp", type=float, default=200)
    p.add_argument("--step-percent", type=int, default=10)
    p.add_argument("--risk-metric", choices=("peak", "shock_cost"), default="peak")
    a = p.parse_args()
    result = run(a.stock_csv, a.yield_csv, a.output, a.financing_millions,
                 a.issue_fy_start, a.horizon, a.rollover_shock_bp, a.step_percent, a.risk_metric)
    print(json.dumps({k: v for k, v in result.items() if k != "frontier"}, indent=2))


if __name__ == "__main__":
    main()
