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

The initial chart measures concentration of scheduled redemptions, not refinancing risk on its own. Comparison against DMO D8B is the next validation step, followed by auction and yield data, scenario analysis, and an issuance cost/risk model. A later model should distinguish nominal and index-linked cash flows, government holdings, buybacks, and the wider financing remit before making policy claims.

This project is independent and has no affiliation with the DMO or HM Treasury. It is research software, not financial or policy advice.
