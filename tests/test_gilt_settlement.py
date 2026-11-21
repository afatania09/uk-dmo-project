import datetime as dt
import unittest
from gilt_settlement import add_months, coupon_schedule, value, solve_yield, settlement_risk

class SettlementTests(unittest.TestCase):
    def test_coupon_date_par(self):
        x = value(dt.date(2026, 1, 1), dt.date(2031, 1, 1), 4, 4)
        self.assertAlmostEqual(x["clean_price"], 100, places=8)
        self.assertAlmostEqual(x["accrued_interest"], 0, places=8)

    def test_between_coupon_accrual(self):
        x = value(dt.date(2026, 4, 1), dt.date(2028, 1, 1), 4, 4)
        self.assertGreater(x["accrued_interest"], 0)
        self.assertAlmostEqual(x["dirty_price"] - x["clean_price"], x["accrued_interest"])

    def test_yield_inverse(self):
        s, m = dt.date(2026, 5, 12), dt.date(2034, 7, 31)
        p = value(s, m, 3.75, 4.6)["clean_price"]
        self.assertAlmostEqual(solve_yield(s, m, 3.75, p), 4.6, places=7)

    def test_calendar_end_of_month(self):
        self.assertEqual(add_months(dt.date(2028, 8, 31), -6), dt.date(2028, 2, 29))

    def test_shock_direction(self):
        x = settlement_risk(dt.date(2026, 3, 10), dt.date(2036, 9, 10), 4, 4.5)
        self.assertLess(x["clean_price_yield_up"], x["clean_price"])
        self.assertGreater(x["clean_price_yield_down"], x["clean_price"])
        self.assertGreater(x["dv01"], 0)

    def test_invalid_settlement(self):
        with self.assertRaises(ValueError):
            coupon_schedule(dt.date(2030, 1, 1), dt.date(2030, 1, 1))

if __name__ == "__main__":
    unittest.main()
