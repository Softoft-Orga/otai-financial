from __future__ import annotations

import unittest

from otai_forecast.config import ALL_SCENARIOS, DEFAULT_ASSUMPTIONS, SCENARIO_ASSUMPTIONS
from otai_forecast.models import ScenarioAssumptions


class TestScenarioAssumptions(unittest.TestCase):
    def test_scenario_assumptions_defined(self) -> None:
        self.assertGreaterEqual(len(ALL_SCENARIOS), 5)
        names = [scenario.name for scenario in ALL_SCENARIOS]
        self.assertEqual(len(names), len(set(names)))
        for scenario in ALL_SCENARIOS:
            self.assertIsInstance(scenario, ScenarioAssumptions)
            self.assertIsNotNone(scenario.assumptions)

    def test_realistic_scenario_matches_default(self) -> None:
        realistic = next(
            scenario
            for scenario in ALL_SCENARIOS
            if scenario.name == "Realistic (Without Investment)"
        )
        self.assertEqual(
            realistic.assumptions.model_dump(),
            DEFAULT_ASSUMPTIONS.model_dump(),
        )


if __name__ == "__main__":
    unittest.main()
