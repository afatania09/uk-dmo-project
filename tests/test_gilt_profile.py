import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from gilt_profile import financial_year, load, write_outputs


class ProfileTests(unittest.TestCase):
    def test_financial_year_boundary_and_aggregation(self):
        as_of = date(2026, 9, 21)
        self.assertEqual(financial_year(date(2027, 3, 31)), "2026-27")
        self.assertEqual(financial_year(date(2027, 4, 1)), "2027-28")
        rows = load("examples/synthetic_gilts.csv", as_of)
        with tempfile.TemporaryDirectory() as tmp:
            result = write_outputs(rows, as_of, Path(tmp))
            with (Path(tmp) / "maturity_profile.csv").open() as handle:
                output = list(csv.DictReader(handle))
            self.assertEqual([r["financial_year"] for r in output], ["2026-27", "2027-28", "2031-32"])
            self.assertEqual(result["total_nominal_outstanding_gbp_millions"], 3500)

    def test_rejects_duplicate_isin(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("gilt_name,isin,redemption_date,nominal_outstanding_millions\nA,X,2028-01-01,1\nB,X,2029-01-01,2\n")
            with self.assertRaisesRegex(ValueError, "duplicate ISIN"):
                load(path, date(2026, 9, 21))


if __name__ == "__main__":
    unittest.main()
