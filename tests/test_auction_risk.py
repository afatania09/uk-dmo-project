import unittest

from auction_risk import analyse

class AuctionRiskTests(unittest.TestCase):
    def setUp(self):
        self.mix = {2: .25, 5: .25, 10: .25, 30: .25}
        self.yields = {2: .03, 5: .035, 10: .04, 30: .045}

    def test_base_and_stress(self):
        report = analyse(self.mix, self.yields, financing_millions=100,
                         bid_cover=2, tail_bp=4, parallel_shock_bp=100)
        self.assertAlmostEqual(report["base_annual_coupon_gbp_millions"], 3.75)
        self.assertAlmostEqual(report["stressed_annual_coupon_gbp_millions"], 4.77)
        self.assertEqual(len(report["rows"]), 4)

    def test_invalid_allocation(self):
        with self.assertRaises(ValueError):
            analyse({2: 1}, self.yields)

    def test_weak_cover_increases_cost(self):
        strong = analyse(self.mix, self.yields, bid_cover=3)["stressed_annual_coupon_gbp_millions"]
        weak = analyse(self.mix, self.yields, bid_cover=1)["stressed_annual_coupon_gbp_millions"]
        self.assertGreater(weak, strong)

if __name__ == "__main__":
    unittest.main()
