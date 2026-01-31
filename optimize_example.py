from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.effects import effect_unlock_sales
from otai_forecast.models import (
    Feature,
    Roadmap,
)
from otai_forecast.optimize import PolicyOptimizer


def create_default_assumptions():
    """Create default assumptions for optimization."""
    return DEFAULT_ASSUMPTIONS


def create_default_roadmap() -> Roadmap:
    """Create default roadmap for optimization."""
    return Roadmap(
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


def main():
    """Run optimization example."""
    print("OTAI Financial Model Optimization")
    print("=" * 50)
    print("Objective: Maximize Final Market Cap (while avoiding negative cash)")
    print("=" * 50)

    # Create fixed assumptions and roadmap
    assumptions = create_default_assumptions()
    roadmap = create_default_roadmap()

    # Create optimizer
    optimizer = PolicyOptimizer(
        assumptions=assumptions,
        roadmap=roadmap,
    )

    # Run optimization
    print("\nRunning Random Search Optimization...")
    result = optimizer.optimize(n_iterations=50, verbose=True)

    print("\nOptimization Complete!")
    print(f"Best Score: €{result.best_score:,.2f}")
    print("\nBest Parameters:")
    print(f"  Ad Start: €{result.best_params.ads_start:,.2f}")
    print(f"  Ad Growth: {result.best_params.ads_growth:.1%}")
    print(f"  Ad Cap: €{result.best_params.ads_cap:,.2f}")
    print(f"  Social Baseline: €{result.best_params.social_baseline:,.2f}")
    print(
        f"  Additional Dev Days: {result.best_params.additional_dev_days:.1f} days/month"
    )
    print(f"  Pro Price: €{result.best_params.pro_price:,.2f} (fixed)")
    print(f"  Ent Price: €{result.best_params.ent_price:,.2f} (fixed)")

    # Create a simple visualization
    results_data = []
    for params, score in result.all_results:
        if score > -999999999:  # Only include valid runs
            results_data.append(
                {
                    "score": score,
                    "ads_start": params.ads_start,
                    "ads_growth": params.ads_growth,
                    "social_baseline": params.social_baseline,
                }
            )

    df_results = pd.DataFrame(results_data)

    if len(df_results) > 0:
        # Create visualizations
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle("Optimization Results", fontsize=16)

        # Score distribution
        axes[0, 0].hist(df_results["score"], bins=20, alpha=0.7, color="blue")
        axes[0, 0].axvline(result.best_score, color="red", linestyle="--", label="Best")
        axes[0, 0].set_xlabel("Final Market Cap (€)")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].set_title("Market Cap Distribution")
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Parameter relationships
        axes[0, 1].scatter(df_results["ads_start"], df_results["score"], alpha=0.6)
        axes[0, 1].set_xlabel("Ad Start (€)")
        axes[0, 1].set_ylabel("Final Market Cap (€)")
        axes[0, 1].set_title("Ad Start vs Market Cap")
        axes[0, 1].grid(True, alpha=0.3)

        axes[1, 0].scatter(
            df_results["ads_growth"], df_results["score"], alpha=0.6, color="purple"
        )
        axes[1, 0].set_xlabel("Ad Growth Rate")
        axes[1, 0].set_ylabel("Final Market Cap (€)")
        axes[1, 0].set_title("Ad Growth vs Market Cap")
        axes[1, 0].grid(True, alpha=0.3)

        axes[1, 1].scatter(
            df_results["social_baseline"], df_results["score"], alpha=0.6, color="green"
        )
        axes[1, 1].set_xlabel("Social Baseline (€)")
        axes[1, 1].set_ylabel("Final Market Cap (€)")
        axes[1, 1].set_title("Social Baseline vs Market Cap")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

        # Show top results
        print("\nTop 5 Results:")
        top_5 = df_results.nlargest(5, "score")[
            ["score", "ads_start", "ads_growth", "social_baseline"]
        ]
        print(top_5.round(2))

    print("\nOptimization complete!")


if __name__ == "__main__":
    main()
