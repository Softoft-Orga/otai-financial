from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from otai_forecast.config import DEFAULT_ASSUMPTIONS, SCENARIO_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision
from otai_forecast.optimization_storage import (
    assumptions_hash,
    load_optimization,
    save_optimization,
)


class TestOptimizationStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.assumptions = DEFAULT_ASSUMPTIONS
        self.decisions = [
            MonthlyDecision(
                ads_budget=0.0,
                seo_budget=0.0,
                dev_budget=0.0,
                partner_budget=0.0,
                outreach_budget=0.0,
            )
        ]

    def _make_df(self, market_cap: float, cash: float) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "market_cap": [market_cap],
                "cash": [cash],
            }
        )

    def test_assumptions_hash_stable(self) -> None:
        baseline = assumptions_hash(self.assumptions)
        self.assertEqual(baseline, assumptions_hash(self.assumptions))

        updated = self.assumptions.model_copy(update={"starting_cash": 50_000.0})
        self.assertNotEqual(baseline, assumptions_hash(updated))

    def test_save_optimization_keeps_best(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base_dir = Path(td)
            first_df = self._make_df(market_cap=100.0, cash=10.0)
            assumption_key = save_optimization(
                self.assumptions,
                self.decisions,
                first_df,
                base_dir=base_dir,
                scenario_assumptions=SCENARIO_ASSUMPTIONS,
            )

            lower_df = self._make_df(market_cap=90.0, cash=12.0)
            save_optimization(
                self.assumptions,
                self.decisions,
                lower_df,
                base_dir=base_dir,
                scenario_assumptions=SCENARIO_ASSUMPTIONS,
            )
            payload = load_optimization(base_dir, assumption_key)
            self.assertIsNotNone(payload)
            self.assertEqual(payload["summary"]["end_market_cap"], 100.0)

            higher_df = self._make_df(market_cap=120.0, cash=15.0)
            save_optimization(
                self.assumptions,
                self.decisions,
                higher_df,
                base_dir=base_dir,
                scenario_assumptions=SCENARIO_ASSUMPTIONS,
            )
            payload = load_optimization(base_dir, assumption_key)
            self.assertIsNotNone(payload)
            self.assertEqual(payload["summary"]["end_market_cap"], 120.0)
