# Data provenance and reuse

`dmo_d8b_2026-09-21.csv` transcribes the complete 47 financial-year table in the UK Debt Management Office's [Future Redemptions (D8B) report](https://www.dmo.gov.uk/umbraco/surface/PDFReport/GetDataExport?reportCode=D8B), **Data Date: 21-Sep-2026**. Units are £ million. The original report's conventional, index-linked and total fields are kept as displayed; commas in thousands were removed. Every row is checked to satisfy `conventional + index-linked = total`, and the 47 financial years are consecutive. Please use the original report for its notes and check for later revisions.

The DMO's [terms of use](https://www.dmo.gov.uk/terms-of-use/) state that, unless otherwise noted, its website information is Crown copyright and may be reused under the [Open Government Licence](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). **Contains public sector information licensed under the Open Government Licence v3.0.** The repository's MIT licence applies to its original code, not as a replacement for the source data's licence.

The yields in `examples/illustrative_yields.csv` and both named issuance strategies in `examples/illustrative_issuance_strategies.csv` are invented scenario inputs, not DMO data or a dated market yield series.
