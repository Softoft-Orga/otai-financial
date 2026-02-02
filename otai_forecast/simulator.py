from __future__ import annotations

from dataclasses import dataclass

from .compute import run_simulation, run_simulation_rows
from .models import Assumptions, MonthlyCalculated, MonthlyDecisions


@dataclass
class Simulator:
    a: Assumptions
    decisions: MonthlyDecisions

    def run(self) -> list[MonthlyCalculated]:
        return run_simulation(self.a, self.decisions)

    def run_rows(self) -> list[dict]:
        return run_simulation_rows(self.a, self.decisions)


def simulate(a: Assumptions, decisions: MonthlyDecisions) -> list[MonthlyCalculated]:
    return run_simulation(a, decisions)


def simulate_rows(a: Assumptions, decisions: MonthlyDecisions) -> list[dict]:
    return run_simulation_rows(a, decisions)
