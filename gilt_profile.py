"""Validate a DMO D1A-style CSV and plot nominal gilt maturities."""

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date, datetime
from html import escape
from pathlib import Path


def key(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


ALIASES = {
    "name": ("giltname", "nameofgilt", "gilt", "stockname"),
    "maturity": ("redemptiondate", "maturitydate", "redemption"),
    "amount": ("nominaloutstandingmillions", "nominalamountinissuemillion", "nominalamountinissuem", "nominalamountoutstandingmillion", "nominalamountoutstandingm", "nominalamountinissue", "nominalamountoutstanding"),
    "isin": ("isin", "isincode"),
    "type": ("gilttype", "type"),
}


def parse_date(raw):
    for pattern in ("%d-%b-%Y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw.strip(), pattern).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognised date: {raw!r}")


def columns(headers):
    found = {}
    for field, aliases in ALIASES.items():
        matches = [h for h in headers if key(h) in aliases]
        if len(matches) > 1:
            raise ValueError(f"Ambiguous {field} columns: {matches}")
        if matches:
            found[field] = matches[0]
    missing = {"name", "maturity", "amount"} - found.keys()
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}. Found: {headers}")
    return found


def load(path, as_of):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV has no header")
        col = columns(reader.fieldnames)
        records, seen = [], set()
        for row_number, row in enumerate(reader, 2):
            try:
                name = row[col["name"]].strip()
                maturity = parse_date(row[col["maturity"]])
                amount = float(row[col["amount"]].replace(",", "").replace("£", "").strip())
                isin = row[col["isin"]].strip() if "isin" in col else ""
                kind = row[col["type"]].strip() if "type" in col else ("index-linked" if "index-linked" in name.lower() else "conventional")
                if not name or not 0 <= amount < float("inf") or maturity <= as_of:
                    raise ValueError("empty name, invalid amount, or matured gilt")
                if isin and isin in seen:
                    raise ValueError(f"duplicate ISIN {isin}")
                seen.add(isin) if isin else None
                records.append((name, maturity, amount, kind.lower()))
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f"CSV row {row_number}: {exc}") from exc
    if not records:
        raise ValueError("CSV contains no gilts")
    return records


def financial_year(day):
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def write_outputs(records, as_of, output):
    output.mkdir(parents=True, exist_ok=True)
    amounts = defaultdict(float)
    for _, maturity, amount, kind in records:
        amounts[(financial_year(maturity), kind)] += amount
    years = sorted({year for year, _ in amounts})
    kinds = sorted({kind for _, kind in amounts})
    with (output / "maturity_profile.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["financial_year", "gilt_type", "nominal_outstanding_gbp_millions"])
        for year in years:
            for kind in kinds:
                if (year, kind) in amounts:
                    writer.writerow([year, kind, f"{amounts[year, kind]:.3f}"])
    total = sum(item[2] for item in records)
    summary = {
        "as_of": as_of.isoformat(), "units": "GBP millions nominal", "gilt_count": len(records),
        "total_nominal_outstanding_gbp_millions": round(total, 3),
        "weighted_average_years_to_maturity": round(sum(a * (d - as_of).days / 365.25 for _, d, a, _ in records) / total, 3) if total else None,
        "source": "User-supplied DMO D1A-style snapshot; date and units must be checked against original export",
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    bars = [sum(amounts[year, kind] for kind in kinds) for year in years]
    top = max(bars) or 1
    width = max(700, 90 + 55 * len(years))
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="430" viewBox="0 0 {width} 430">',
                '<rect width="100%" height="100%" fill="white"/>',
                '<text x="50" y="30" font-family="sans-serif" font-size="18">Nominal gilt maturities by UK financial year (£m)</text>',
                '<line x1="55" y1="350" x2="' + str(width - 15) + '" y2="350" stroke="#333"/>']
    for i, (year, value) in enumerate(zip(years, bars)):
        x, height = 65 + 55 * i, 280 * value / top
        elements.extend([f'<rect x="{x}" y="{350-height:.2f}" width="38" height="{height:.2f}" fill="#176a96"/>',
                         f'<text x="{x}" y="370" font-family="sans-serif" font-size="10" transform="rotate(45 {x} 370)">{escape(year)}</text>'])
    elements.append('</svg>')
    (output / "maturity_profile.svg").write_text("\n".join(elements) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--as-of", required=True, type=date.fromisoformat, help="DMO snapshot date, YYYY-MM-DD")
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    print(json.dumps(write_outputs(load(args.csv_file, args.as_of), args.as_of, args.output), indent=2))


if __name__ == "__main__":
    main()
