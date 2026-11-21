import unittest
from gilt_pricing import price, yield_to_maturity, risk

class GiltPricingTests(unittest.TestCase):
    def test_par_bond(self):
        self.assertAlmostEqual(price(100, .04, .04, 10), 100, places=8)
        self.assertAlmostEqual(yield_to_maturity(100, 100, .04, 10), .04, places=8)

    def test_zero_coupon(self):
        self.assertAlmostEqual(price(100, 0, .05, 2), 100 / 1.05 ** 2)
        self.assertAlmostEqual(risk(100, 0, .05, 2)["macaulay_duration_years"], 2)

    def test_price_yield_inverse(self):
        for y in (.01, .07, -.005):
            p = price(100, .03, y, 7)
            self.assertAlmostEqual(yield_to_maturity(p, 100, .03, 7), y, places=7)

    def test_duration_and_shock(self):
        x = risk(100, .04, .04, 10)
        self.assertGreater(x["dv01_per_face"], 0)
        self.assertLess(x["price_up_shock"], x["price_per_face"])
        self.assertGreater(x["price_down_shock"], x["price_per_face"])

    def test_invalid(self):
        with self.assertRaises(ValueError):
            price(100, .04, -1, 10)

if __name__ == "__main__":
    unittest.main()
