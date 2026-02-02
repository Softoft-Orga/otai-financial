# AI Agent Guidelines for OTAI Financial Forecasting System

## Core Architecture

### Data Models (`otai_forecast/models.py`)
- **Immutable Dataclasses**: All dataclasses are frozen (`@dataclass(frozen=True)`) except `State`
- **Validation**: All validation logic is in `__post_init__` methods
- **No Field Constraints**: Never use `field(gt=0)`, `field(ge=0)`, etc. Use validation in `__post_init__` instead
- **Required Fields**: All fields in `Assumptions` and `MonthlyDecision` are required

### Key Data Structures

```python
# Core assumptions - all financial and operational parameters
Assumptions(months, starting_cash, base_organic_users_per_month, cpc_base, cpc_k, cpc_ref_spend,
            seo_eff_users_per_eur, seo_decay,
            domain_rating_init, domain_rating_max, domain_rating_growth_k, domain_rating_growth_ref_spend, domain_rating_decay,
            conv_web_to_lead, conv_lead_to_free, conv_free_to_pro, conv_pro_to_ent,
            churn_free, churn_pro, churn_ent, churn_pro_floor,
            pro_price_base, ent_price_base, pro_price_k, ent_price_k,
            tax_rate, sales_cost_per_new_pro, sales_cost_per_new_ent, support_cost_per_pro, support_cost_per_ent,
            qualified_pool_total, contact_rate_per_month, scraping_efficiency_k, scraping_ref_spend,
            credit_cash_threshold, credit_draw_amount, debt_interest_rate_base_annual, debt_interest_rate_k, debt_interest_rate_ref,
            pv_init, pv_min, pv_ref, pv_decay_shape, pv_growth_scale,
            k_pv_web_to_lead, k_pv_lead_to_free, k_pv_free_to_pro, k_pv_pro_to_ent, k_pv_churn_pro)

# Single-month decision - what you can control each month
MonthlyDecision(ads_spend, seo_spend, social_spend, dev_spend, operating_spend, scraping_spend, outreach_intensity,
                pro_price_override=None, ent_price_override=None)

# Type alias: list of monthly decisions
MonthlyDecisions = list[MonthlyDecision]

# Simulation state - changes each month
State(month, cash, debt, seo_stock_users, domain_rating, product_value,
      free_active, pro_active, ent_active)

# Monthly calculated outputs - computed each month
MonthlyCalculated(month, product_value_next, pv_norm, pro_price, ent_price,
                  conv_web_to_lead_eff, conv_lead_to_free_eff, conv_free_to_pro_eff, conv_pro_to_ent_eff, churn_pro_eff,
                  ads_clicks, domain_rating_next, seo_stock_next, website_users, website_leads,
                  scraped_found, outreach_leads, direct_leads, leads_total,
                  new_free, new_pro, new_ent, churned_free, churned_pro, churned_ent,
                  sales_spend, support_spend, interest_rate_annual_eff, interest_payment,
                  revenue_pro, revenue_ent, revenue_total, costs_ex_tax, profit_bt, tax, net_cashflow)
```

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

## Important Design Notes

- **No Optimization**: This is a forward-simulation model only. No optimization, roadmap, or policy system.
- **Monthly Decisions**: All decision variables are per-month; you can vary them month by month.
- **Diminishing Returns**: CPC, scraping, and domain rating all use logarithmic curves for realism.
- **Fixed Pools**: Scraping works from a fixed `qualified_pool_total`; you cannot exceed it.

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

Remember: Tests should provide value by catching actual bugs, not just increasing code coverage.
