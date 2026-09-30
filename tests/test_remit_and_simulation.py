import tempfile
import unittest
from pathlib import Path

from issuance_scenarios import load_strategies
from rate_simulation import (load_proxy_strategy, path_coupon_cost, quantile,
                             run_simulation)
from remit_analysis import read_remit, summarize
from sensitivity_analysis import run_grid


class RemitTests(unittest.TestCase):
    def test_official_remit_arithmetic(self):
        rows = read_remit("data/dmo_financing_remit_2026-27_2026-04-23.csv")
        result = summarize(rows)
        self.assertEqual(result["planned_gilt_sales_gbp_bn"], 246.2)
        self.assertEqual(result["allocated_conventional_gbp_bn"], 193.4)
        self.assertAlmostEqual(sum(result["allocated_conventional_mix_percent"].values()), 100, places=1)

    def test_rejects_inconsistent_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            original = Path("data/dmo_financing_remit_2026-27_2026-04-23.csv").read_text()
            p.write_text(original.replace("95.0,0.0,0.0,95.0", "95.0,0.0,0.0,94.0"))
            with self.assertRaisesRegex(ValueError, "do not add"):
                read_remit(p)


class SimulationTests(unittest.TestCase):
    def test_quantile_interpolation(self):
        self.assertEqual(quantile([0, 10], 0.5), 5)

    def test_zero_shift_matches_fixed_coupon(self):
        legs = {2: (1.0, 0.04)}
        total, annual = path_coupon_cost(legs, 100000, 5, [0] * 6)
        self.assertEqual(total, 20000)
        self.assertEqual(annual, [4000] * 5)

    def test_seed_is_reproducible(self):
        strategies = load_strategies("examples/illustrative_issuance_strategies.csv")
        a = run_simulation(strategies, simulations=200, seed=7, horizon=10)
        b = run_simulation(strategies, simulations=200, seed=7, horizon=10)
        self.assertEqual(a, b)

    def test_longer_mix_reduces_upper_tail_under_rollover_model(self):
        strategies = load_strategies("examples/illustrative_issuance_strategies.csv")
        result = run_simulation(strategies, simulations=1000, seed=9, horizon=30)
        self.assertLess(result["strategies"]["longer"]["p95_gbp_millions"],
                        result["strategies"]["shorter"]["p95_gbp_millions"])

    def test_remit_proxy_uses_only_allocated_conventional(self):
        legs = load_proxy_strategy(
            Path("data/dmo_financing_remit_2026-27_2026-04-23.csv"),
            Path("examples/illustrative_yields.csv"))
        self.assertAlmostEqual(sum(share for share, _ in legs.values()), 1)
        self.assertEqual(set(legs), {2, 10, 30})

    def test_sensitivity_grid_has_all_cells(self):
        strategies = {"test": {2: (1.0, 0.04)}}
        rows = run_grid(strategies, simulations=100, seed=3, horizon=5)
        self.assertEqual(len(rows), 9)
        self.assertEqual({r["volatility_bp"] for r in rows}, {50, 100, 150})


if __name__ == "__main__":
    unittest.main()
