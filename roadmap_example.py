"""Example demonstrating the OTAI roadmap with financial projections."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import pandas as pd

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision
from otai_forecast.simulator import Simulator


def main():
    print("Open Ticket AI - Product Roadmap Financial Projections")
    print("=" * 60)
    print()

    a = DEFAULT_ASSUMPTIONS
    decisions = [
        MonthlyDecision(
            ads_spend=500.0,
            seo_spend=300.0,
            social_spend=150.0,
            dev_spend=5000.0,
            operating_spend=5000.0,
            scraping_spend=0.0,
            outreach_intensity=0.25,
        )
        for _ in range(a.months)
    ]

    simulator = Simulator(a=a, decisions=decisions)
    df = pd.DataFrame(simulator.run_rows())

    # Key metrics
    final_cash = df["cash"].iloc[-1]
    min_cash = df["cash"].min()
    final_users = (
        df["free_active"].iloc[-1]
        + df["pro_active"].iloc[-1]
        + df["ent_active"].iloc[-1]
    )
    final_arr = (df["revenue_total"].iloc[-1]) * 12

    print(f"Final Cash (Month {a.months}): €{final_cash:,.0f}")
    print(f"Minimum Cash: €{min_cash:,.0f}")
    print(f"Final Active Users: {final_users:,.0f}")
    print(f"Final ARR: €{final_arr:,.0f}")

    # Quarterly breakdown
    print("\nQUARTERLY PERFORMANCE")
    print("-" * 40)

    quarters = list(range(0, a.months + 1, 3))
    for i in range(len(quarters) - 1):
        start = quarters[i]
        end = quarters[i + 1] - 1
        quarter_name = f"Q{(i // 4) + 1} {2026 + (i // 4)}"

        if end < len(df):
            revenue = df["revenue_total"].iloc[end]
            users = (
                df["free_active"].iloc[end]
                + df["pro_active"].iloc[end]
                + df["ent_active"].iloc[end]
            )
            cash = df["cash"].iloc[end]

            print(f"\n{quarter_name}:")
            print(f"  Monthly Revenue: €{revenue:,.0f}")
            print(f"  Active Users: {users:,.0f}")
            print(f"  Cash: €{cash:,.0f}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
