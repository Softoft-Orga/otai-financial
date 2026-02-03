from __future__ import annotations

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.decision_optimizer import (
    choose_best_decisions_by_market_cap,
)
from otai_forecast.export import export
from otai_forecast.models import MonthlyDecision
from otai_forecast.plots import plot_enhanced_dashboard


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

    decisions, df = choose_best_decisions_by_market_cap(a, base_decisions, num_knots=9, knot_low=0, knot_high=10,
                                                        max_evals=10_000)

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
