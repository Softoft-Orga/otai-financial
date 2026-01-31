from __future__ import annotations

from dataclasses import asdict

import matplotlib.pyplot as plt
import pandas as pd

from otai_forecast.config import DEFAULT_ASSUMPTIONS, DEFAULT_DEV_PARAMS, DEFAULT_PRICES
from otai_forecast.effects import effect_unlock_sales
from otai_forecast.export import export_detailed, export_nice, export_simulation_output
from otai_forecast.models import (
    Feature,
    Policy,
    PolicyParams,
    Roadmap,
)
from otai_forecast.simulator import DetailedSimulator, Simulator


def plot_results(df: pd.DataFrame) -> None:
    """Create plots for the simulation results."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("OTAI Financial Simulation Results", fontsize=16)

    # Plot 1: User Growth
    axes[0, 0].plot(df["t"], df["free_active"], label="Free Users", marker="o")
    axes[0, 0].plot(df["t"], df["pro_active"], label="Pro Users", marker="o")
    axes[0, 0].plot(df["t"], df["ent_active"], label="Enterprise Users", marker="o")
    axes[0, 0].set_title("User Growth Over Time")
    axes[0, 0].set_xlabel("Month")
    axes[0, 0].set_ylabel("Number of Users")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Plot 2: Revenue and Cashflow
    ax2_twin = axes[0, 1].twinx()
    axes[0, 1].plot(
        df["t"], df["revenue_total"], color="green", label="Revenue", marker="o"
    )
    ax2_twin.plot(
        df["t"], df["net_cashflow"], color="blue", label="Net Cashflow", marker="s"
    )
    axes[0, 1].set_title("Revenue and Net Cashflow")
    axes[0, 1].set_xlabel("Month")
    axes[0, 1].set_ylabel("Revenue (€)", color="green")
    ax2_twin.set_ylabel("Net Cashflow (€)", color="blue")
    axes[0, 1].grid(True, alpha=0.3)

    # Combine legends
    lines1, labels1 = axes[0, 1].get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    axes[0, 1].legend(lines1 + lines2, labels1 + labels2)

    # Plot 3: Cash Position
    axes[1, 0].plot(df["t"], df["cash"], marker="o", color="purple")
    axes[1, 0].set_title("Cash Position")
    axes[1, 0].set_xlabel("Month")
    axes[1, 0].set_ylabel("Cash (€)")
    axes[1, 0].grid(True, alpha=0.3)

    # Plot 4: Leads and Conversion
    axes[1, 1].plot(df["t"], df["leads"], label="Total Leads", marker="o")
    axes[1, 1].set_title("Leads Generation")
    axes[1, 1].set_xlabel("Month")
    axes[1, 1].set_ylabel("Count")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def run() -> None:
    import pandas as pd

    a = DEFAULT_ASSUMPTIONS

    policy = Policy(
        p=PolicyParams(
            ads_start=500.0,
            ads_growth=0.0,
            ads_cap=500.0,
            social_baseline=150.0,
            dev_capacity_days=30.0,
            **DEFAULT_PRICES,
            **DEFAULT_DEV_PARAMS,
        ),
    )

    roadmap = Roadmap(
        features=[
            Feature(
                name="v1",
                dev_days=30 * 4,
                maintenance_days_per_month=10.0,
                effect=effect_unlock_sales(),
            ),
            Feature(
                name="v2",
                dev_days=30 * 4,
                maintenance_days_per_month=5.0,
                effect=None,
            ),
        ]
    )

    sim = Simulator(
        a=a,
        roadmap=roadmap,
        policy=policy,
    )

    rows = sim.run()
    df = pd.DataFrame([asdict(r) for r in rows])
    export_simulation_output(df, out_path="OTAI_Simulation_Output.xlsx")

    # Show plots
    plot_results(df)

    sim_detailed = DetailedSimulator(
        a=a,
        roadmap=roadmap,
        policy=policy,
    )
    detailed_log = sim_detailed.run()
    df_detailed = pd.DataFrame(detailed_log)

    export_detailed(df_detailed, out_path="OTAI_Simulation_Detailed.xlsx")
    export_nice(df_detailed, out_path="OTAI_Simulation_Nice.xlsx")


if __name__ == "__main__":
    run()
