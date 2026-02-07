from __future__ import annotations

import argparse
from pathlib import Path

from otai_forecast.config import (
    OPTIMIZER_KNOT_HIGHS,
    OPTIMIZER_KNOT_LOWS,
    OPTIMIZER_NUM_KNOTS,
    RUN_BASE_DECISION,
    SCENARIO_ASSUMPTIONS,
    build_base_decisions,
)
from otai_forecast.decision_optimizer import (
    choose_best_decisions_by_market_cap,
    run_simulation_df,
)
from otai_forecast.export import export_scenarios
from otai_forecast.models import Assumptions, MonthlyDecision, ScenarioAssumptions
from otai_forecast.optimization_storage import (
    assumptions_hash,
    load_optimization,
    save_optimization,
)
from otai_forecast.plots import plot_enhanced_dashboard

OPTIMIZATION_DIR = Path(__file__).resolve().parent.parent / "data" / "optimizations"


def _scenario_name_from_payload(
    payload: dict,
    default_name: str,
) -> str:
    raw_scenarios = payload.get("assumption_scenarios")
    if not isinstance(raw_scenarios, list):
        return default_name
    for scenario in raw_scenarios:
        if not isinstance(scenario, dict):
            continue
        try:
            scenario_obj = ScenarioAssumptions(**scenario)
        except Exception:
            continue
        if assumptions_hash(scenario_obj.assumptions) == payload.get("assumption_hash"):
            return scenario_obj.name
    return default_name


def _load_payload_results(payload: dict) -> tuple[Assumptions, list[MonthlyDecision]]:
    assumptions = Assumptions(**payload["assumptions"])
    decisions = [MonthlyDecision(**decision) for decision in payload["decisions"]]
    return assumptions, decisions


def run(*, use_existing_results: bool = False) -> None:
    scenario_results = []

    for scenario in SCENARIO_ASSUMPTIONS:
        assumptions = scenario.assumptions
        assumption_key = assumptions_hash(assumptions)
        payload = load_optimization(OPTIMIZATION_DIR, assumption_key)

        if use_existing_results:
            if payload is None:
                raise FileNotFoundError(
                    f"No stored optimization found for {scenario.name} ({assumption_key})."
                )
            assumptions, decisions = _load_payload_results(payload)
        else:
            # Create simple constant decisions - optimizer will find the optimal values
            base_decisions = build_base_decisions(assumptions.months, RUN_BASE_DECISION)

            decisions, df = choose_best_decisions_by_market_cap(
                assumptions,
                base_decisions,
                num_knots=OPTIMIZER_NUM_KNOTS,
                knot_lows=OPTIMIZER_KNOT_LOWS,
                knot_highs=OPTIMIZER_KNOT_HIGHS,
                max_evals=1_000,
            )
            save_optimization(
                assumptions,
                decisions,
                df,
                base_dir=OPTIMIZATION_DIR,
                scenario_assumptions=SCENARIO_ASSUMPTIONS,
            )

        df = run_simulation_df(assumptions, decisions)
        scenario_name = (
            _scenario_name_from_payload(payload, scenario.name)
            if payload
            else scenario.name
        )

        scenario_results.append(
            {
                "name": scenario_name,
                "df": df,
                "assumptions": assumptions,
                "decisions": decisions,
            }
        )

    # Export the complete report with all plots
    export_scenarios(
        scenario_results,
        out_path="../data/OTAI_Simulation_Report.xlsx",
    )

    # Also save the dashboard plot separately
    if scenario_results:
        plot_enhanced_dashboard(
            scenario_results[0]["df"],
            save_path="OTAI_Simulation_Plots.png",
        )


if __name__ == "__main__":
    run(use_existing_results=False)
