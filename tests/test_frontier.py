import tempfile
import unittest
from pathlib import Path

from d8b_analysis import read_profile
from strategy_frontier import allocations, assess, combined_redemptions, load_yields, pareto, run


class FrontierTests(unittest.TestCase):
    def setUp(self):
        self.stock = read_profile("data/dmo_d8b_2026-09-21.csv")
        self.yields = load_yields("examples/illustrative_yields.csv")

    def test_grid_size_and_sum(self):
        points = list(allocations(10))
        self.assertEqual(len(points), 286)
        self.assertTrue(all(abs(sum(p) - 1) < 1e-10 for p in points))

    def test_new_issuance_added_once_at_original_maturity(self):
        series = combined_redemptions(self.stock, (1, 0, 0, 0), 100000, 2026, 10)
        self.assertEqual(series[1]["financial_year"], "2028-2029")
        self.assertEqual(series[1]["new_issuance_redemptions_gbp_millions"], 100000)
        self.assertEqual(series[3]["new_issuance_redemptions_gbp_millions"], 0)

    def test_pareto_dominance(self):
        points = [{"cost": 1, "risk": 3}, {"cost": 2, "risk": 2},
                  {"cost": 3, "risk": 3}]
        self.assertEqual(len(pareto(points, "cost", "risk")), 2)

    def test_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(Path("data/dmo_d8b_2026-09-21.csv"),
                         Path("examples/illustrative_yields.csv"), Path(tmp))
            self.assertEqual(result["candidate_count"], 286)
            self.assertGreater(result["frontier_count"], 1)
            self.assertTrue((Path(tmp) / "strategy_frontier.svg").exists())

    def test_long_horizon_exposes_rollover_sensitivity(self):
        short = assess(self.stock, self.yields, (1, 0, 0, 0), horizon=30)
        long = assess(self.stock, self.yields, (0, 0, 0, 1), horizon=30)
        self.assertLess(short["initial_coupon_gbp_millions_per_year"], long["initial_coupon_gbp_millions_per_year"])
        self.assertGreater(short["horizon_shock_coupons_gbp_millions"], long["horizon_shock_coupons_gbp_millions"])
        self.assertEqual(long["horizon_shock_coupons_gbp_millions"], 141000)


if __name__ == "__main__":
    unittest.main()
