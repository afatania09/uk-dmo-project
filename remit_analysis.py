"""Validate and summarize the DMO's revised 2026-27 financing remit."""

import argparse
import csv
import json
from pathlib import Path


EXPECTED_SECTORS = {
    "short_conventional", "medium_conventional_including_green",
    "long_conventional", "index_linked", "unallocated",
}


def read_remit(path):
    required = {"instrument", "sector", "auction_gbp_bn", "syndication_gbp_bn",
                "unallocated_gbp_bn", "total_gbp_bn", "share_total_percent"}
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or set(reader.fieldnames) != required:
            raise ValueError(f"Expected columns: {sorted(required)}")
        rows = []
        for line, raw in enumerate(reader, 2):
            try:
                sector = raw["sector"].strip()
                auction, syndication, unallocated, total, share = (
                    float(raw[k]) for k in ("auction_gbp_bn", "syndication_gbp_bn",
                                            "unallocated_gbp_bn", "total_gbp_bn",
                                            "share_total_percent")
                )
                if raw["instrument"] != "gilt" or sector not in EXPECTED_SECTORS:
                    raise ValueError("unexpected instrument or sector")
                if min(auction, syndication, unallocated, total, share) < 0:
                    raise ValueError("negative amount")
                if abs(auction + syndication + unallocated - total) > 0.051:
                    raise ValueError("distribution methods do not add to total")
                rows.append({"sector": sector, "auction": auction,
                             "syndication": syndication, "unallocated": unallocated,
                             "total": total, "share": share})
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f"CSV line {line}: {exc}") from exc
    sectors = [r["sector"] for r in rows]
    if len(rows) != 5 or set(sectors) != EXPECTED_SECTORS or len(set(sectors)) != 5:
        raise ValueError("Remit must contain each of the five sectors exactly once")
    if abs(sum(r["total"] for r in rows) - 246.2) > 0.051:
        raise ValueError("Gilt sales total must be £246.2bn")
    return rows


def summarize(rows):
    by_sector = {r["sector"]: r for r in rows}
    conventional = sum(by_sector[s]["total"] for s in (
        "short_conventional", "medium_conventional_including_green",
        "long_conventional"))
    allocated = conventional + by_sector["index_linked"]["total"]
    auction = sum(r["auction"] for r in rows)
    syndication = sum(r["syndication"] for r in rows)
    return {
        "data_date": "2026-04-23",
        "net_financing_requirement_gbp_bn": 251.2,
        "planned_gilt_sales_gbp_bn": round(sum(r["total"] for r in rows), 1),
        "treasury_bill_net_contribution_gbp_bn": 5.0,
        "planned_green_gilt_sales_gbp_bn": 12.0,
        "allocated_conventional_gbp_bn": round(conventional, 1),
        "allocated_index_linked_gbp_bn": by_sector["index_linked"]["total"],
        "initially_unallocated_gbp_bn": by_sector["unallocated"]["total"],
        "auction_gbp_bn": round(auction, 1),
        "syndication_gbp_bn": round(syndication, 1),
        "allocated_conventional_mix_percent": {
            "short": round(100 * by_sector["short_conventional"]["total"] / conventional, 2),
            "medium": round(100 * by_sector["medium_conventional_including_green"]["total"] / conventional, 2),
            "long": round(100 * by_sector["long_conventional"]["total"] / conventional, 2),
        },
        "allocated_share_of_total_gilt_sales_percent": round(100 * allocated / 246.2, 2),
    }


def write_chart(rows, path):
    labels = ["Short conventional", "Medium conventional", "Long conventional",
              "Index-linked", "Initially unallocated"]
    values = [r["total"] for r in rows]
    colours = ["#195f85", "#2f7fa4", "#63a5bd", "#e49a36", "#8a9299"]
    width, height = 840, 430
    maximum = max(values) or 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="65" y="32" font-family="sans-serif" font-size="18">Revised 2026–27 planned gilt sales (£bn)</text>',
             '<text x="65" y="52" font-family="sans-serif" font-size="11">DMO financing remit revision, 23 April 2026</text>',
             '<line x1="65" y1="350" x2="810" y2="350" stroke="#333"/>']
    for i, (label, value, colour) in enumerate(zip(labels, values, colours)):
        x = 90 + i * 140
        bar_height = 250 * value / maximum
        parts += [f'<rect x="{x}" y="{350-bar_height:.2f}" width="82" height="{bar_height:.2f}" fill="{colour}"/>',
                  f'<text x="{x+41}" y="{340-bar_height:.2f}" text-anchor="middle" font-family="sans-serif" font-size="13">{value:.1f}</text>',
                  f'<text x="{x+41}" y="370" text-anchor="middle" font-family="sans-serif" font-size="10">{label}</text>']
    parts.append('</svg>')
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    result = summarize(read_remit(args.csv_file))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "remit_summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_chart(read_remit(args.csv_file), args.output / "remit_composition.svg")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
