"""Example demonstrating the OTAI roadmap with financial projections."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import pandas as pd

from otai_forecast.config import DEFAULT_ASSUMPTIONS, DEFAULT_DEV_PARAMS, DEFAULT_PRICES
from otai_forecast.models import Policy, PolicyParams
from otai_forecast.optimize import PolicyOptimizer
from otai_forecast.roadmap import (
    FEATURE_IMPACTS,
    QUARTERLY_ROADMAP,
    create_otai_roadmap,
)
from otai_forecast.simulator import Simulator


def main():
    print("Open Ticket AI - Product Roadmap Financial Projections")
    print("=" * 60)
    print()

    # Create the roadmap
    roadmap = create_otai_roadmap()

    # Display quarterly overview
    print("QUARTERLY RELEASE SCHEDULE")
    print("-" * 40)
    for quarter, features in QUARTERLY_ROADMAP.items():
        print(f"\n{quarter}:")
        for feature in features:
            print(f"  - {feature}")

    print("\n" + "=" * 60)
    print("\nFEATURE IMPACTS ON METRICS")
    print("-" * 40)

    for category, impacts in FEATURE_IMPACTS.items():
        print(f"\n{category}:")
        for impact in impacts:
            print(f"  - {impact}")

    print("\n" + "=" * 60)
    print("\nFINANCIAL PROJECTIONS")
    print("-" * 40)

    # Create policy with default parameters
    policy = Policy(
        p=PolicyParams(
            ads_start=1000.0,
            ads_growth=0.05,
            ads_cap=5000.0,
            social_baseline=200.0,
            additional_dev_days=DEFAULT_DEV_PARAMS["additional_dev_days"],
            **DEFAULT_PRICES,
        )
    )

    # Run simulation
    simulator = Simulator(a=DEFAULT_ASSUMPTIONS, roadmap=roadmap, policy=policy)
    rows = simulator.run()

    # Convert to DataFrame for analysis
    df = pd.DataFrame([r.__dict__ for r in rows])

    # Key metrics
    final_cash = df["cash"].iloc[-1]
    min_cash = df["cash"].min()
    final_users = (
        df["free_active"].iloc[-1]
        + df["pro_active"].iloc[-1]
        + df["ent_active"].iloc[-1]
    )
    final_arr = (df["revenue_total"].iloc[-1]) * 12

    print(f"Final Cash (Month 24): €{final_cash:,.0f}")
    print(f"Minimum Cash: €{min_cash:,.0f}")
    print(f"Final Active Users: {final_users:,.0f}")
    print(f"Final ARR: €{final_arr:,.0f}")

    # Quarterly breakdown
    print("\nQUARTERLY PERFORMANCE")
    print("-" * 40)

    quarters = [0, 3, 6, 9, 12, 15, 18, 21, 24]
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
    print("\nOPTIMIZATION SCENARIO")
    print("-" * 40)

    # Run optimization
    optimizer = PolicyOptimizer(assumptions=DEFAULT_ASSUMPTIONS, roadmap=roadmap)
    result = optimizer.optimize(n_iterations=100)

    print(f"Optimized Market Cap: €{result.best_score:,.0f}")
    print(f"Improvement: {((result.best_score / final_arr) - 1) * 100:.1f}%")

    print("\nOptimized Parameters:")
    print(f"  Ad Start: €{result.best_params.ads_start:,.0f}")
    print(f"  Ad Growth: {result.best_params.ads_growth * 100:.1f}%")
    print(f"  Ad Cap: €{result.best_params.ads_cap:,.0f}")
    print(f"  Social Baseline: €{result.best_params.social_baseline:,.0f}")
    print(f"  Additional Dev Days: {result.best_params.additional_dev_days:.1f}")

    print("\n" + "=" * 60)
    print("\nROADMAP VALIDATION")
    print("-" * 40)

    # Check development capacity
    total_dev_days = sum(f.dev_days for f in roadmap.features)
    total_maintenance_per_month = sum(
        f.maintenance_days_per_month for f in roadmap.features
    )

    print(f"Total Development Days Required: {total_dev_days:.0f}")
    print(f"Average per Month: {total_dev_days / 24:.1f}")
    print(f"Peak Maintenance (Month 24): {total_maintenance_per_month:.1f} days/month")

    # Validate feasibility
    additional_dev_days = DEFAULT_DEV_PARAMS["additional_dev_days"]
    peak_dev_needed = total_maintenance_per_month + additional_dev_days

    print(f"\nPeak Development Need: {peak_dev_needed:.1f} days/month")
    if peak_dev_needed > 30:
        print("Warning: Development capacity may be exceeded!")
        print("   Consider increasing additional_dev_days or adjusting roadmap")
    else:
        print("Roadmap is feasible with current development capacity")

    print("\n" + "=" * 60)
    print("\nFEATURE TIMELINE WITH DEPENDENCIES")
    print("-" * 40)

    # Show feature completion timeline
    cumulative_days = 0
    for i, feature in enumerate(roadmap.features):
        completion_month = min(23, int((cumulative_days + feature.dev_days) / 30))
        print(f"Month {completion_month:2d}: {feature.name}")
        print(
            f"           Dev: {feature.dev_days:.0f} days, Maint: {feature.maintenance_days_per_month:.1f} days/month"
        )
        cumulative_days += feature.dev_days

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
