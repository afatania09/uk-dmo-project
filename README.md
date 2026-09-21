# UK Sovereign Debt Strategy

An independent, reproducible analysis of the UK gilt maturity profile. This repository starts with a narrow, auditable question: **how much nominal gilt principal is scheduled to redeem in each UK financial year?**

## Current capability

`gilt_profile.py` accepts a saved CSV export of the UK Debt Management Office (DMO) **Gilts in Issue (D1A)** report, validates the key fields, and produces:

- `maturity_profile.csv`: nominal amounts outstanding by financial year and gilt type;
- `maturity_profile.svg`: a chart of the same amounts;
- `summary.json`: input date, total nominal outstanding, gilt count and weighted average years to maturity.

The DMO [Gilts in Issue page](https://www.dmo.gov.uk/data/gilt-market/gilts-in-issue/) describes D1A as a snapshot containing redemption dates and nominal amounts outstanding. It also distinguishes the separate [future redemptions report (D8B)](https://www.dmo.gov.uk/data/), which reports amounts in **market hands**. Our D1A profile is therefore a schedule of gross nominal outstanding, **not** a forecast of cash financing needs, market-held redemptions, inflation-adjusted redemption payments, or a DMO policy recommendation.

## Run

Requires Python 3.10+ and only the standard library.

1. Visit the DMO [Gilts in Issue report](https://www.dmo.gov.uk/data/datareport?reportCode=D1A), select a reporting date, export the table as CSV, and save it locally. Review the [DMO terms](https://www.dmo.gov.uk/terms-of-use/) before redistribution.
2. Check the CSV headers. The importer accepts common DMO headings or a normalized file with `gilt_name,redemption_date,nominal_outstanding_millions` and optionally `isin,gilt_type`.
3. Run:

```bash
python gilt_profile.py path/to/gilts.csv --as-of 2026-09-21 --output outputs
python -m unittest discover -s tests -v
```

Amounts must be in **£ millions nominal**. A DMO export with different units must be converted before use. The example file under `examples/` is **synthetic** and demonstrates the workflow only:

```bash
python gilt_profile.py examples/synthetic_gilts.csv --as-of 2026-09-21 --output outputs
```

`--as-of` must match the date selected in the DMO report. The tool does not infer or verify a snapshot date from the CSV. It rejects negative amounts, duplicate ISINs, missing fields, and redemption dates on or before the selected date. Financial years run from 1 April to 31 March. A maturity on 31 March 2027 falls in 2026-27; one on 1 April 2027 falls in 2027-28.

## Interpretation and next steps

The initial D1A chart measures concentration of scheduled gross nominal redemptions, not refinancing risk on its own. The D8B table below supplies a separate market-hands perspective. A later model should reconcile these series and distinguish nominal and index-linked cash flows, government holdings, buybacks, and the wider financing remit before making policy claims.

## DMO future redemptions: dated snapshot

The repository also contains a transcription of all 47 financial-year rows of the DMO [Future Redemptions (D8B) report](https://www.dmo.gov.uk/umbraco/surface/PDFReport/GetDataExport?reportCode=D8B) **dated 21 September 2026**: `data/dmo_d8b_2026-09-21.csv`. The report begins in **2027-28**; no inference is made here about 2026-27. Its totals are net of government holdings, subject to the DMO's note that holdings are updated after month-end. For index-linked gilts, the reported redemption amounts do not equal the full inflation-uplifted nominal amounts: part of the uplift enters the financing calculation elsewhere. This is a snapshot, and future issuance will change the profile. See the original DMO report for its detailed notes.

```bash
python d8b_analysis.py data/dmo_d8b_2026-09-21.csv --output outputs
```

This produces a stacked chart and JSON summary. In the dated snapshot, total scheduled redemptions across the **listed years** are £2,407.274 billion. The largest listed year is 2029-30 (£165.944 billion); 30.9% of the listed total falls in its first five years. These are sums of reported figures, not an estimate of the government's total financing requirement.

## Illustrative issuance comparison

```bash
python issuance_scenarios.py examples/illustrative_issuance_strategies.csv \
  --financing-millions 100000 --horizon 10 --rollover-shock-bp 200 --output outputs
```

The example compares two **hypothetical** ways to issue £100 billion of fixed-rate conventional debt. The CSV's yields are invented assumptions, not observed market rates. Issuance occurs at par; coupons are modelled annually; maturing principal is rolled into the same tenor at its input yield plus the specified shock. The shock applies only *after* each leg's first maturity, and the model holds rollover yields constant thereafter. It excludes issue discounts, issuance capacity, liquidity effects, taxes, inflation, demand and future changes in the DMO financing remit.

| Example strategy | Initial yield | Weighted maturity | Original principal due within five years | Ten-year coupons, no shock | Ten-year coupons, +200bp on rollover |
|---|---:|---:|---:|---:|---:|
| Shorter | 4.165% | 7.45 years | £70bn | £41.65bn | £50.75bn |
| Longer | 4.390% | 16.20 years | £30bn | £43.90bn | £47.50bn |

The no-shock comparison charges £2.25bn more coupons over ten years for the longer example. Under the **assumed** rollover shock, it charges £3.25bn less. These simplified coupon totals are scenario accounting, not expected present-value costs or an optimal issuance recommendation. The D8B snapshot is not automatically added to the hypothetical issuance in this comparison; doing so would mix observed stock and invented yields without a defensible calibration.

Next: ingest an actual DMO D1A export, reconcile its gross maturity schedule against the D8B market-hands totals, and source dated yield inputs before assessing real strategy trade-offs.

This project is independent and has no affiliation with the DMO or HM Treasury. It is research software, not financial or policy advice.
