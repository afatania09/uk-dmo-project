"""Portfolio dashboard using semiannual settlement-aware gilt proxies."""
import argparse
import csv
import datetime as dt
import html
import json
import math
from pathlib import Path
from gilt_settlement import settlement_risk

REQUIRED = ("instrument", "maturity_date", "face_millions", "coupon_percent", "yield_percent")

def analyse(rows, settlement_date, shock_bp=100):
    if not isinstance(settlement_date, dt.date):
        raise ValueError("Settlement date required")
    if not math.isfinite(shock_bp) or shock_bp < 0 or shock_bp >= 10000:
        raise ValueError("Invalid shock")
    securities = []
    for row in rows:
        name = str(row["instrument"]).strip()
        if not name:
            raise ValueError("Instrument name required")
        maturity = dt.date.fromisoformat(row["maturity_date"])
        face = float(row["face_millions"])
        if not math.isfinite(face) or face <= 0:
            raise ValueError("Face must be finite and positive")
        coupon = float(row["coupon_percent"])
        yld = float(row["yield_percent"])
        # Valuation with face in millions means prices, accrued and DV01 are in £m.
        r = settlement_risk(settlement_date, maturity, coupon, yld, face, shock_bp)
        securities.append({"instrument": name, "maturity_date": maturity.isoformat(),
                           "face_millions": face, "coupon_percent": coupon,
                           "yield_percent": yld, **r})
    if not securities:
        raise ValueError("Portfolio is empty")
    total = sum(s["dirty_price"] for s in securities)
    def weighted(key):
        return sum(s["dirty_price"] * s[key] for s in securities) / total
    return {"methodology": "Illustrative semiannual settlement-aware fixed-rate bond proxies; not executable UK gilt prices",
            "settlement_date": settlement_date.isoformat(), "shock_bp": shock_bp,
            "total_face_millions": sum(s["face_millions"] for s in securities),
            "total_dirty_market_value_millions": total,
            "total_clean_market_value_millions": sum(s["clean_price"] for s in securities),
            "total_accrued_interest_millions": sum(s["accrued_interest"] for s in securities),
            "portfolio_modified_duration": weighted("modified_duration"),
            "portfolio_dv01_millions_per_bp": sum(s["dv01"] for s in securities),
            "portfolio_clean_value_yield_up_millions": sum(s["clean_price_yield_up"] for s in securities),
            "portfolio_clean_value_yield_down_millions": sum(s["clean_price_yield_down"] for s in securities),
            "securities": securities}

def load_csv(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or any(k not in reader.fieldnames for k in REQUIRED):
            raise ValueError("Missing required columns: " + ", ".join(REQUIRED))
        return list(reader)

def render_html(result):
    metrics = (("Dirty market value (£m)", "total_dirty_market_value_millions"),
               ("Accrued interest (£m)", "total_accrued_interest_millions"),
               ("Modified duration", "portfolio_modified_duration"),
               ("DV01 (£m/bp)", "portfolio_dv01_millions_per_bp"),
               ("Clean value, yields up (£m)", "portfolio_clean_value_yield_up_millions"),
               ("Clean value, yields down (£m)", "portfolio_clean_value_yield_down_millions"))
    cards = "".join("<article class='card'><small>" + html.escape(label) +
                    "</small><strong>" + f"{result[key]:,.4f}" + "</strong></article>"
                    for label, key in metrics)
    cols = ("instrument", "maturity_date", "face_millions", "coupon_percent",
            "yield_percent", "clean_price", "dirty_price", "accrued_interest",
            "modified_duration", "dv01")
    heads = ("Instrument", "Maturity", "Face (£m)", "Coupon (%)", "Yield (%)",
             "Clean (£m)", "Dirty (£m)", "Accrued (£m)", "Duration", "DV01 (£m/bp)")
    rows = "".join("<tr>" + "".join("<td>" + html.escape(
        f"{s[k]:,.5f}" if isinstance(s[k], float) else str(s[k])) + "</td>"
        for k in cols) + "</tr>" for s in result["securities"])
    return """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Illustrative gilt settlement portfolio</title><style>body{margin:0;background:#f2f5fa;color:#172a42;font:16px system-ui}
main{max-width:1300px;margin:auto;padding:30px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:24px 0}
.card{background:#fff;padding:18px;border-radius:12px;display:grid;gap:12px;border:1px solid #dce3ec}
small{color:#54677e}strong{font-size:1.35rem}.scroll{overflow-x:auto;background:#fff;border-radius:12px}
table{border-collapse:collapse;width:100%}th,td{padding:12px;text-align:left;border-bottom:1px solid #e4e9ef;white-space:nowrap}
th{background:#e7edf5}.warning{padding:14px;background:#fff0cc;border-left:4px solid #a96b0e}</style><main>
<h1>Settlement-aware gilt portfolio</h1><p>Settlement: """ + html.escape(result["settlement_date"]) + " · Parallel yield shock: " + html.escape(str(result["shock_bp"])) + """ bp</p>
<p class="warning">Synthetic conventional fixed-rate bond proxies only. Ex-dividend periods, settlement business days, stubs and market-specific conventions are not modelled. Not trading prices.</p>
<div class="cards">""" + cards + """</div><div class="scroll"><table><thead><tr>""" + "".join("<th>" + html.escape(h) + "</th>" for h in heads) + "</tr></thead><tbody>" + rows + "</tbody></table></div></main></html>"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file")
    parser.add_argument("--settlement", required=True)
    parser.add_argument("--shock-bp", type=float, default=100)
    parser.add_argument("--output", default="outputs/settlement_portfolio")
    args = parser.parse_args()
    result = analyse(load_csv(args.csv_file), dt.date.fromisoformat(args.settlement), args.shock_bp)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "index.html").write_text(render_html(result), encoding="utf-8")
    print("Wrote", out / "summary.json", "and", out / "index.html")

if __name__ == "__main__":
    main()
