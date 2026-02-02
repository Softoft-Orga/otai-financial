# AI Agent Guidelines for OTAI Financial Forecasting System

## Project Overview
OTAI Financial Forecasting System is a comprehensive B2B business simulation tool that models user growth, revenue, cash flow, and market dynamics.
The system includes optimization capabilities, visualization tools, and a Streamlit web interface.

## Core Architecture

### Data Models (`otai_forecast/models.py`)
- **Immutable Dataclasses**: Prefer Immutable/Frozen Dataclasses

## Module Structure

### Core Modules
- **`models.py`**: Data models and validation logic
- **`simulator.py`**: Main simulation engine (`Simulator` class)
- **`compute.py`**: Calculation functions for monthly metrics
- **`config.py`**: Default assumptions and configuration

### Optimization Module (`otai_forecast/decision_optimizer.py`)
- **`choose_best_decisions_by_market_cap()`**: Optimizes decisions to maximize final market cap
- Uses random search with configurable evaluation count (default: 25,000 trials)
- Applies time-based scaling to decision variables
- Filters out simulations that run out of cash

### Visualization Module (`otai_forecast/plots.py`)
Comprehensive plotting functions including:
- Basic plots: `plot_results()`, `plot_user_growth()`, `plot_revenue_cashflow()`
- Enhanced plots: `plot_enhanced_dashboard()`, `plot_growth_insights()`
- Specialized analyses: `plot_ltv_cac_analysis()`, `plot_conversion_funnel()`, `plot_financial_health_score()`

### Export Module (`otai_forecast/export.py`)
Three export formats:
- **`export_simulation_output()`**: Basic Excel with simulation, assumptions, and decisions
- **`export_detailed()`**: Detailed monthly breakdown
- **`export_nice()`**: Formatted Excel with KPIs, multiple views, and styling

### Web Interface (`streamlit_app.py`)
- Interactive dashboard for parameter adjustment
- Real-time simulation and optimization
- Downloadable Excel exports
- Comprehensive visualization suite

### Entry Point (`otai_forecast/run.py`)
Script that:
1. Loads default assumptions
2. Creates base decisions
3. Runs optimization
4. Exports results to Excel
5. Generates visualization dashboard

## Simulation Flow

### 1. Initialization
```python
assumptions = Assumptions(...)
decisions = [MonthlyDecision(...) for _ in range(assumptions.months)]
simulator = Simulator(a=assumptions, decisions=decisions)
```

### 2. Monthly Step Execution
For each month `t`:
1. Get the monthly decision: `decisions[t]`
2. Calculate new monthly data: `calculate_new_monthly_data(state, assumptions, decision)`
3. Update state: `calculate_new_state(state, monthly_calculated, assumptions)`
4. Append results to output list

### 3. Market Cap Calculation
After simulation:
```python
df["revenue_ttm"] = df["revenue_total"].rolling(window=12, min_periods=1).sum()
df["market_cap"] = df["revenue_ttm"] * assumptions.market_cap_multiple
```

## Core Calculations

### Revenue
```python
revenue_pro = pro_active * pro_price
revenue_ent = ent_active * ent_price
revenue_total = revenue_pro + revenue_ent
```

### Dynamic CPC (Ads)
- CPC increases with spend via logarithmic scaling (diminishing returns)
- `_effective_cpc(ads_spend, assumptions)` computes CPC for the month
- `ads_clicks = ads_spend / effective_cpc` (if ads_spend > 0)

### SEO & Domain Rating
- `domain_rating` grows with `seo_spend` via logarithmic curve and decays over time
- `seo_stock_users` accumulates and decays; boosted by current `domain_rating`
- `website_users` depends on `domain_rating`, `seo_stock_users`, and `ads_clicks`

### Scraping Funnel (Direct Leads)
1. `scraped_found`: fraction of `qualified_pool_total` found via scraping (logarithmic diminishing returns)
2. `outreach_leads`: contact scraped candidates at `contact_rate_per_month * outreach_intensity`
3. `direct_leads = outreach_leads`

### Debt & Credit
- If cash falls below `credit_cash_threshold` and `credit_draw_amount > 0`, credit is drawn automatically
- Debt accumulates; no automatic repayment
- Interest rate depends on current debt level (logarithmic)
- `interest_payment` is part of monthly costs

### Product Value Effects
- `product_value` evolves based on `dev_spend` vs maintenance needs
- Affects conversion rates and pricing via `pv_norm`
- Higher product value improves conversions and reduces churn

## Optimization System

### Decision Optimization
- **Objective**: Maximize final market cap
- **Method**: Random search with time-based scaling
- **Constraints**: Must maintain positive cash throughout simulation
- **Parameters**: Scaling factors for decision variables

### Time-Based Scaling
Uses exponential interpolation to smoothly scale decisions:
```python
scaled_value = start * ((end / start) ** t)  # where t is normalized time
```

## Important Design Notes

- **Forward Simulation Only**: This is a simulation model, not a prediction system
- **Monthly Decisions**: All decision variables are per-month; you can vary them month by month
- **Diminishing Returns**: CPC, scraping, and domain rating all use logarithmic curves for realism
- **Fixed Pools**: Scraping works from a fixed `qualified_pool_total`; you cannot exceed it
- **Market Cap Multiple**: Final valuation calculated as TTM Revenue × Multiple

## Testing Guidelines

### What NOT to Test
- **Dataclass field access**: Don't test trivial getter/setter behavior
- **Type annotations**: Don't test that fields have the correct type
- **Frozen dataclass immutability**: Don't test that frozen dataclasses are immutable
- **Basic arithmetic**: Don't test simple calculations like `revenue = price * users`

### What TO Test
- **Complex business logic**: Test multi-step calculations with edge cases
- **Validation logic**: Test `__post_init__` validation with invalid inputs
- **Helper functions**: Test `_effective_cpc`, `_update_domain_rating`, etc.
- **Simulation flows**: Test that state changes correctly across simulation steps
- **Edge cases**: Test boundary conditions (zero values, maximum values, negative cash)
- **Optimization**: Test that optimizer improves results and respects constraints

Remember: Tests should provide value by catching actual bugs, not just increasing code coverage.

## Usage Examples

### Optimization
```python
from otai_forecast.decision_optimizer import choose_best_decisions_by_market_cap

# Optimize for maximum market cap
best_decisions, df = choose_best_decisions_by_market_cap(
    assumptions, 
    base_decisions,
    max_evals=5000
)
```

### Web Interface
```bash
streamlit run streamlit_app.py
```

### Running Full Pipeline
```bash
python -m otai_forecast.run
```
