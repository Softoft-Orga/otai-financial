from __future__ import annotations

from pathlib import Path

from otai_forecast.config import (
    ALL_SCENARIOS,
    OPTIMIZER_KNOT_CONFIG,
    OPTIMIZER_NUM_KNOTS,
    RUN_BASE_DECISION,
    SCENARIO_ASSUMPTIONS,
    WARM_START_KNOTS,
    build_base_decisions,
)
from otai_forecast.decision_optimizer import (
    choose_best_decisions_by_market_cap,
    run_simulation_df,
)
from otai_forecast.export import export_scenarios, export_simple_budget
from otai_forecast.models import Assumptions, MonthlyDecision, ScenarioAssumptions
from otai_forecast.optimization_storage import (
    assumptions_hash,
    load_optimization,
    save_optimization,
)

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


def run(
        *,
        use_existing_results: bool = False,
        scenarios: list[ScenarioAssumptions] | None = None,
) -> None:
    scenario_results = []

    for scenario in (scenarios or ALL_SCENARIOS):
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
                knot_config=OPTIMIZER_KNOT_CONFIG,
                max_evals=1000,
                warm_start_knots=WARM_START_KNOTS,
            )
            save_optimization(
                assumptions,
                decisions,
                df,
                base_dir=OPTIMIZATION_DIR,
                scenario_assumptions=ALL_SCENARIOS,
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
    # export_scenarios(
    #    scenario_results,
    #    out_path="../data/OTAI_Simulation_Report.xlsx",
    #)

    # Also save the dashboard plot separately
    # if scenario_results:
    #   plot_enhanced_dashboard(
    #      scenario_results[0]["df"],
    #     save_path="OTAI_Simulation_Plots.png",
    # )

    # Export simplified 12-month budget for Conservative (Without Investment)
    conservative_no_inv = next(
        (s for s in scenario_results if "Conservative" in s["name"] and "Without" in s["name"]),
        None,
    )
    if conservative_no_inv is not None:
        df_24 = conservative_no_inv["df"].head(24)
        export_simple_budget(
            df_24,
            conservative_no_inv["assumptions"],
            out_path="../data/OTAI_Simple_Budget.xlsx",
        )


if __name__ == "__main__":
    run(
        use_existing_results=False,
        scenarios=[SCENARIO_ASSUMPTIONS["conservative_no_inv"]],
    )
