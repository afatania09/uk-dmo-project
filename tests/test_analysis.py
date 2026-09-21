import tempfile
import unittest
from pathlib import Path

from d8b_analysis import read_profile, summary
from issuance_scenarios import evaluate, load_strategies


class AnalysisTests(unittest.TestCase):
    def test_dmo_snapshot_totals(self):
        rows = read_profile("data/dmo_d8b_2026-09-21.csv")
        s = summary(rows)
        self.assertEqual(len(rows), 47)
        self.assertEqual(s["total_scheduled_redemptions"], 2407274)
        self.assertEqual(s["peak_year"], "2029-2030")

    def test_dmo_rejects_bad_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("financial_year,conventional_gbp_millions,index_linked_gbp_millions,total_gbp_millions\n2027-2028,2,3,4\n")
            with self.assertRaisesRegex(ValueError, "inconsistent"):
                read_profile(path)

    def test_rollover_shock_only_after_maturity(self):
        legs = load_strategies("examples/illustrative_issuance_strategies.csv")["shorter"]
        base = evaluate(legs, 100000, 10)
        shocked = evaluate(legs, 100000, 10, 200)
        self.assertEqual(base["annual_coupon_gbp_millions"][0], shocked["annual_coupon_gbp_millions"][0])
        self.assertEqual(base["annual_coupon_gbp_millions"][1], shocked["annual_coupon_gbp_millions"][1])
        self.assertAlmostEqual(shocked["annual_coupon_gbp_millions"][2] - base["annual_coupon_gbp_millions"][2], 700)


if __name__ == "__main__":
    unittest.main()
