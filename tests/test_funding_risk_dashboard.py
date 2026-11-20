import unittest
from funding_risk_dashboard import analyse, render_html, load_csv

class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"instrument": "Sample", "face_millions": "100",
                      "coupon_percent": "4", "yield_percent": "4", "years": "10"}]

    def test_portfolio_par_and_shock(self):
        x = analyse(self.rows)
        self.assertAlmostEqual(x["total_market_value_millions"], 100, places=5)
        self.assertLess(x["portfolio_value_yield_up_millions"], 100)
        self.assertGreater(x["portfolio_value_yield_down_millions"], 100)
        self.assertGreater(x["portfolio_dv01_millions_per_bp"], 0)

    def test_multiple_instruments(self):
        x = analyse(self.rows + [{**self.rows[0], "instrument": "Second", "face_millions": "200"}])
        self.assertAlmostEqual(x["total_market_value_millions"], 300, places=5)

    def test_html_escapes_names(self):
        x = analyse([{**self.rows[0], "instrument": "<script>alert(1)</script>"}])
        rendered = render_html(x)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            analyse([])
        with self.assertRaises(ValueError):
            analyse([{**self.rows[0], "years": "2.5"}])

    def test_example(self):
        x = analyse(load_csv("examples/illustrative_funding_portfolio.csv"))
        self.assertEqual(len(x["securities"]), 4)

if __name__ == "__main__":
    unittest.main()
