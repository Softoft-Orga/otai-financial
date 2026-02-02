from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision
from otai_forecast.simulator import Simulator


def main():
    """Run a simple scenario comparison example (no optimization)."""
    assumptions = DEFAULT_ASSUMPTIONS

    scenarios = {
        "baseline": MonthlyDecision(
            ads_spend=500.0,
            seo_spend=300.0,
            social_spend=150.0,
            dev_spend=5000.0,
            operating_spend=5000.0,
            scraping_spend=0.0,
            outreach_intensity=0.25,
        ),
        "high_dev": MonthlyDecision(
            ads_spend=500.0,
            seo_spend=300.0,
            social_spend=150.0,
            dev_spend=10000.0,
            operating_spend=5000.0,
            scraping_spend=0.0,
            outreach_intensity=0.25,
        ),
    }

    fig, ax = plt.subplots(figsize=(10, 5))

    for name, decision in scenarios.items():
        sim = Simulator(a=assumptions, decisions=[decision] * assumptions.months)
        df = pd.DataFrame(sim.run_rows())
        ax.plot(df["month"], df["cash"], label=name)

    ax.set_title("Scenario comparison: cash")
    ax.set_xlabel("Month")
    ax.set_ylabel("Cash (€)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
