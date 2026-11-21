import datetime as dt
import unittest
from settlement_portfolio import analyse, load_csv, render_html

class SettlementPortfolioTests(unittest.TestCase):
    def setUp(self):
        self.date = dt.date(2026, 11, 21)
        self.rows = load_csv("examples/illustrative_settlement_portfolio.csv")

    def test_accounting_identity(self):
        result = analyse(self.rows, self.date)
        self.assertAlmostEqual(result["total_dirty_market_value_millions"],
                               result["total_clean_market_value_millions"] +
                               result["total_accrued_interest_millions"], places=7)
        self.assertEqual(len(result["securities"]), 4)

    def test_shock_direction(self):
        r = analyse(self.rows, self.date)
        self.assertLess(r["portfolio_clean_value_yield_up_millions"], r["total_clean_market_value_millions"])
        self.assertGreater(r["portfolio_clean_value_yield_down_millions"], r["total_clean_market_value_millions"])
        self.assertGreater(r["portfolio_dv01_millions_per_bp"], 0)

    def test_html_escaping(self):
        r = analyse([{**self.rows[0], "instrument": "<script>"}], self.date)
        self.assertIn("&lt;script&gt;", render_html(r))
        self.assertNotIn("<script>", render_html(r))

    def test_bad_maturity(self):
        with self.assertRaises(ValueError):
            analyse([{**self.rows[0], "maturity_date": "2020-01-01"}], self.date)

    def test_bad_face(self):
        with self.assertRaises(ValueError):
            analyse([{**self.rows[0], "face_millions": "-1"}], self.date)

if __name__ == "__main__":
    unittest.main()
