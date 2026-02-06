"""Test that the liquidity constraint is working in the decision optimizer."""

import sys
sys.path.insert(0, '.')

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.decision_optimizer import choose_best_decisions_by_market_cap
from otai_forecast.models import MonthlyDecision

# Create base decisions (minimal spending)
base_decisions = [
    MonthlyDecision(
        ads_budget=100.0,
        seo_budget=100.0,
        dev_budget=100.0,
        outreach_budget=100.0,
        partner_budget=50.0,
    )
    for _ in range(12)  # 12 months
]

# Test with a strict liquidity ratio
assumptions = DEFAULT_ASSUMPTIONS.model_copy(update={
    "months": 12,
    "minimum_liquidity_ratio": 0.1,  # Only allow 10% debt-to-revenue ratio
    "starting_cash": 50000.0,
})

print("Running optimization with liquidity constraint...")
best_decisions, best_df = choose_best_decisions_by_market_cap(
    a=assumptions,
    base=base_decisions,
    max_evals=50,
    seed=42,
    num_knots=3,
)

# Check final liquidity ratio
final_debt = best_df["debt"].iloc[-1]
final_cash = best_df["cash"].iloc[-1]
annual_revenue = best_df["revenue_ttm"].iloc[-1]

if annual_revenue > 0:
    liquidity_ratio = max(0.0, final_debt - final_cash) / annual_revenue
    print(f"\nFinal liquidity ratio: {liquidity_ratio:.3f}")
    print(f"Constraint threshold: {assumptions.minimum_liquidity_ratio:.3f}")
    print(f"Final market cap: {best_df['market_cap'].iloc[-1]:,.0f}")
    print(f"Final debt: {final_debt:,.0f}")
    print(f"Final cash: {final_cash:,.0f}")
    print(f"Annual revenue (TTM): {annual_revenue:,.0f}")
    
    if liquidity_ratio <= assumptions.minimum_liquidity_ratio:
        print("SUCCESS: Liquidity constraint satisfied!")
    else:
        print("ERROR: Liquidity constraint violated!")
else:
    print("No revenue generated")
