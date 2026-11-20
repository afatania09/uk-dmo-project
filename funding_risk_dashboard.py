"""Synthetic gilt issuance portfolio risk dashboard: JSON and standalone HTML.

Inputs are annual-coupon proxy securities, NOT live UK gilt market data.
"""
import argparse
import csv
import html
import json
import math
from pathlib import Path
from gilt_pricing import price, risk

FIELDS = ("instrument", "face_millions", "coupon_percent", "yield_percent", "years")

def analyse(rows, shock_bp=100):
    if not math.isfinite(shock_bp) or shock_bp < 0 or shock_bp >= 10000:
        raise ValueError("Shock must be finite and between 0 and 10000 basis points")
    securities = []
    for row in rows:
        name = str(row["instrument"]).strip()
        if not name:
            raise ValueError("Instrument name required")
        face = float(row["face_millions"])
        coupon = float(row["coupon_percent"]) / 100
        yield_rate = float(row["yield_percent"]) / 100
        years_raw = float(row["years"])
        if not years_raw.is_integer():
            raise ValueError("Maturity years must be an integer")
        years = int(years_raw)
        r = risk(face, coupon, yield_rate, years, shock_bp)
        r.update({"instrument": name, "face_millions": face,
                  "coupon_percent": coupon * 100, "yield_percent": yield_rate * 100,
                  "years": years})
        securities.append(r)
    if not securities:
        raise ValueError("Portfolio is empty")
    total = sum(s["price_per_face"] for s in securities)
    if total <= 0:
        raise ValueError("Invalid total market value")
    def weighted(field):
        return sum(s["price_per_face"] * s[field] for s in securities) / total
    return {"methodology": "Synthetic annual-coupon bond proxies; no accrued interest or gilt settlement conventions",
            "shock_bp": shock_bp, "total_face_millions": sum(s["face_millions"] for s in securities),
            "total_market_value_millions": round(total, 5),
            "portfolio_modified_duration": round(weighted("modified_duration"), 6),
            "portfolio_convexity": round(weighted("convexity"), 6),
            "portfolio_dv01_millions_per_bp": round(sum(s["dv01_per_face"] for s in securities), 7),
            "portfolio_value_yield_up_millions": round(sum(s["price_up_shock"] for s in securities), 5),
            "portfolio_value_yield_down_millions": round(sum(s["price_down_shock"] for s in securities), 5),
            "securities": securities}

def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or any(c not in reader.fieldnames for c in FIELDS):
            raise ValueError("CSV requires columns: " + ", ".join(FIELDS))
        return list(reader)

def render_html(result):
    rows = "".join("<tr>" + "".join("<td>" + html.escape(str(s[k])) + "</td>"
                   for k in ("instrument", "face_millions", "years", "yield_percent",
                             "price_per_face", "modified_duration", "dv01_per_face")) + "</tr>"
                   for s in result["securities"])
    cards = "".join("<div class='card'><small>" + html.escape(label) +
                    "</small><strong>" + html.escape(str(result[key])) + "</strong></div>"
                    for label, key in (("Market value (£m proxy)", "total_market_value_millions"),
                                       ("Modified duration", "portfolio_modified_duration"),
                                       ("DV01 (£m/bp)", "portfolio_dv01_millions_per_bp"),
                                       ("Value after yield rise (£m)", "portfolio_value_yield_up_millions"),
                                       ("Value after yield fall (£m)", "portfolio_value_yield_down_millions")))
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Illustrative DMO Funding Risk</title><style>body{font:16px system-ui;background:#f3f6fa;color:#15263b;margin:0}
main{max-width:1150px;margin:auto;padding:32px}h1{font-size:2rem}.muted{color:#4c6076}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:25px 0}
.card{background:white;border:1px solid #d9e1eb;border-radius:12px;padding:18px;display:flex;flex-direction:column;gap:12px}
small{color:#4c6076}strong{font-size:1.4rem}.scroll{overflow-x:auto;background:white;border-radius:12px}
table{border-collapse:collapse;width:100%}th,td{padding:13px;text-align:left;border-bottom:1px solid #e0e6ee}th{background:#e7eef6}
.warning{background:#fff4d6;border-left:4px solid #c47b13;padding:14px}</style><main>
<h1>Funding-risk dashboard</h1><p class="muted">Illustrative conventional bond portfolio • Parallel yield shock: """ + html.escape(str(result["shock_bp"])) + """ bp</p>
<p class="warning">Educational annual-coupon proxies, not live UK gilt prices or UK DMO forecasts. No settlement, accrued interest or curve bootstrapping.</p>
<section class="cards">""" + cards + """</section><div class="scroll"><table><thead><tr>
<th>Instrument</th><th>Face (£m)</th><th>Years</th><th>Yield (%)</th><th>Market value (£m)</th><th>Mod. duration</th><th>DV01 (£m/bp)</th>
</tr></thead><tbody>""" + rows + """</tbody></table></div>
<p class="muted">All metrics are computed from the accompanying CSV using funding_risk_dashboard.py.</p></main></html>"""

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv_file")
    p.add_argument("--shock-bp", type=float, default=100)
    p.add_argument("--output", default="outputs/funding_risk")
    a = p.parse_args()
    result = analyse(load_csv(a.csv_file), a.shock_bp)
    output = Path(a.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output / "index.html").write_text(render_html(result), encoding="utf-8")
    print("Created", output / "summary.json", "and", output / "index.html")

if __name__ == "__main__":
    main()
