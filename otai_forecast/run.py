from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.decision_optimizer import (
    choose_best_decisions_by_market_cap,
)
from otai_forecast.export import export_detailed, export_nice, export_simulation_output
from otai_forecast.models import Assumptions, MonthlyDecision
from otai_forecast.plots import plot_enhanced_dashboard


def run() -> None:
    import pandas as pd

    a = DEFAULT_ASSUMPTIONS

    # Create simple constant decisions - optimizer will find the optimal values
    base_decisions = [
        MonthlyDecision(
            ads_spend=1000.0,
            seo_spend=1000.0,
            social_spend=100.0,
            dev_spend=10000.0,
            scraping_spend=100.0,
            outreach_intensity=0.3,
        )
        for _ in range(a.months)
    ]
    
    decisions, df = choose_best_decisions_by_market_cap(a, base_decisions)

    export_simulation_output(
        df,
        out_path="OTAI_Simulation_Output.xlsx",
        assumptions=a,
        monthly_decisions=decisions,
    )

    # Show plots
    plot_enhanced_dashboard(df, save_path="OTAI_Simulation_Plots.png")
    plt.close('all')

    export_detailed(
        df,
        out_path="OTAI_Simulation_Detailed.xlsx",
        assumptions=a,
        monthly_decisions=decisions,
    )
    export_nice(
        df,
        out_path="OTAI_Simulation_Nice.xlsx",
        assumptions=a,
        monthly_decisions=decisions,
    )


if __name__ == "__main__":
    run()
