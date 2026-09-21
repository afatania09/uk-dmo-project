"""Analyse a dated DMO D8B future-redemptions table (GBP millions)."""

import argparse
import csv
import json
from pathlib import Path


def read_profile(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        expected = {"financial_year", "conventional_gbp_millions", "index_linked_gbp_millions", "total_gbp_millions"}
        if not reader.fieldnames or not expected <= set(reader.fieldnames):
            raise ValueError("D8B CSV requires year, conventional, index-linked and total columns")
        rows = []
        for line, row in enumerate(reader, 2):
            try:
                year = row["financial_year"]
                start, end = map(int, year.split("-"))
                if end != start + 1:
                    raise ValueError("invalid financial year")
                values = [int(row[key].replace(",", "")) for key in ("conventional_gbp_millions", "index_linked_gbp_millions", "total_gbp_millions")]
                if min(values) < 0 or values[0] + values[1] != values[2]:
                    raise ValueError("negative or inconsistent amounts")
                if rows and start != rows[-1]["start"] + 1:
                    raise ValueError("years must be consecutive and unique")
                rows.append({"financial_year": year, "start": start, "conventional": values[0], "index_linked": values[1], "total": values[2]})
            except (ValueError, AttributeError, TypeError) as exc:
                raise ValueError(f"CSV line {line}: {exc}") from exc
    if not rows:
        raise ValueError("empty profile")
    return rows


def summary(rows):
    total = sum(r["total"] for r in rows)
    linked = sum(r["index_linked"] for r in rows)
    peak = max(rows, key=lambda r: r["total"])
    return {
        "units": "GBP millions", "financial_years": len(rows),
        "total_scheduled_redemptions": total,
        "index_linked_share_percent": round(100 * linked / total, 2),
        "peak_year": peak["financial_year"], "peak_year_redemptions": peak["total"],
        "first_five_years_redemptions": sum(r["total"] for r in rows[:5]),
        "first_five_years_share_percent": round(100 * sum(r["total"] for r in rows[:5]) / total, 2),
    }


def chart(rows, path):
    """Dependency-free bar chart retaining zero-redemption financial years."""
    height = 400
    width = max(920, 90 + 16 * len(rows))
    maximum = max(r["total"] for r in rows) or 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="55" y="30" font-family="sans-serif" font-size="18">DMO future gilt redemptions, 21 September 2026 (£m)</text>',
             f'<line x1="55" y1="330" x2="{width-25}" y2="330" stroke="#333"/>']
    step = (width - 100) / len(rows)
    for i, row in enumerate(rows):
        x = 60 + i * step
        base = 330
        for field, colour in (("conventional", "#165d85"), ("index_linked", "#eb9c35")):
            h = 255 * row[field] / maximum
            parts.append(f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{max(2,step-2):.1f}" height="{h:.1f}" fill="{colour}"/>')
            base -= h
        if i % 5 == 0:
            parts.append(f'<text x="{x:.1f}" y="347" font-family="sans-serif" font-size="10" transform="rotate(45 {x:.1f} 347)">{row["financial_year"]}</text>')
    parts += ['<rect x="55" y="365" width="12" height="12" fill="#165d85"/><text x="73" y="376" font-family="sans-serif" font-size="12">Conventional</text>',
              '<rect x="180" y="365" width="12" height="12" fill="#eb9c35"/><text x="198" y="376" font-family="sans-serif" font-size="12">Index-linked</text>', '</svg>']
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv_file", type=Path)
    p.add_argument("--output", type=Path, default=Path("outputs"))
    args = p.parse_args()
    rows = read_profile(args.csv_file)
    args.output.mkdir(parents=True, exist_ok=True)
    chart(rows, args.output / "dmo_redemptions.svg")
    result = summary(rows)
    (args.output / "dmo_redemptions_summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
