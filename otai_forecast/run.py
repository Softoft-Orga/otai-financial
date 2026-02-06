from __future__ import annotations

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.decision_optimizer import (
    choose_best_decisions_by_market_cap,
)
from otai_forecast.export import export
from otai_forecast.models import MonthlyDecision
from otai_forecast.plots import plot_enhanced_dashboard

OPTIMIZER_KNOT_LOWS = [0.1, 0.15, 0.2, 0.35, 0.5, 0.75, 1.0, 1.25, 1.5]
OPTIMIZER_KNOT_HIGHS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.5, 5.5, 6.5, 7.5]
OPTIMIZER_MAX_MONTHLY_MULTIPLIER_CHANGE = 0.5


def run() -> None:
    a = DEFAULT_ASSUMPTIONS

    # Create simple constant decisions - optimizer will find the optimal values
    base_decisions = [
        MonthlyDecision(
            ads_budget=1000.0,
            seo_budget=1000.0,
            dev_budget=2000.0,
            partner_budget=500.0,
            outreach_budget=1000.0,
        )
        for _ in range(a.months)
    ]

    decisions, df = choose_best_decisions_by_market_cap(
        a,
        base_decisions,
        num_knots=9,
        knot_lows=OPTIMIZER_KNOT_LOWS,
        knot_highs=OPTIMIZER_KNOT_HIGHS,
        max_monthly_multiplier_change=OPTIMIZER_MAX_MONTHLY_MULTIPLIER_CHANGE,
        max_evals=10_000,
    )

    # Export the complete report with all plots
    export(
        df,
        out_path="../data/OTAI_Simulation_Report.xlsx",
        assumptions=a,
        monthly_decisions=decisions,
    )

    # Also save the dashboard plot separately
    plot_enhanced_dashboard(df, save_path="OTAI_Simulation_Plots.png")


if __name__ == "__main__":
    run()
