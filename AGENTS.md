# AI Agent Guidelines for OTAI Financial Forecasting System

## Core Architecture

### Data Models (`otai_forecast/models.py`)
- **Immutable Dataclasses**: All dataclasses are frozen (`@dataclass(frozen=True)`) except `State`, `Policy`, and `Roadmap`
- **Validation**: All validation logic is in `__post_init__` methods
- **No Field Constraints**: Never use `field(gt=0)`, `field(ge=0)`, etc. Use validation in `__post_init__` instead
- **Required Fields**: All fields in `Assumptions` and `PolicyParams` are required

### Key Data Structures

```python
# Core assumptions - all financial and operational parameters
Assumptions(months, dev_day_cost_eur, starting_cash_eur, tax_rate, valuation_multiple_arr, 
            credit_interest_rate_annual, credit_draw_amount, credit_cash_threshold, ...)

# Policy parameters - controllable variables for simulation
PolicyParams(ads_start, ads_growth, ads_cap, social_baseline, 
            additional_dev_days, pro_price, ent_price)

# Monthly inputs - derived from policy parameters
MonthlyInputs(ads_spend, social_spend, additional_dev_days)

# Simulation state - changes each month
State(t, cash, debt, free_active, pro_active, ent_active, partners, ...)

# Financial results - calculated each month
Finance(revenue_total, net_cashflow, profit_before_tax, tax, profit_after_tax, mrr, arr, market_cap, debt, interest_payment)
```

## Simulation Flow

### 1. Initialization
```python
assumptions = Assumptions(...)
policy = Policy(p=PolicyParams(...))
roadmap = Roadmap(features=[Feature(...)])
simulator = Simulator(a=assumptions, roadmap=roadmap, policy=policy)
```

### 2. Monthly Step Execution
For each month `t`:
1. Get monthly inputs from policy: `policy.inputs(t)`
2. Create context: `Context(t=t, a=assumptions, inp=inputs)`
3. Apply feature effects: `apply_effects(context, roadmap)`
4. Compute metrics (traffic, leads, customers, finance)
5. Update state and create Row

## Financial Calculations

### Revenue
```python
revenue = pro_active * pro_price + ent_active * ent_price
```

### Debt/Credit Financing
- `credit_interest_rate_annual`: Annual interest rate
- `credit_draw_amount`: Amount to draw when cash is low
- `credit_cash_threshold`: Cash level that triggers credit draw
- Debt accumulates - no automatic repayment
- Debt reduces company valuation in market cap calculation

## Optimization System

### Objective Function
Maximize **final market cap** while ensuring cash never goes negative:
```python
if min_cash < 0:
    return -999999999  # Invalid solution
return final_market_cap
```

### Parameter Ranges
Default ranges (in `config.py`):
- ads_start: (100, 2000)
- ads_growth: (0.0, 0.2)
- ads_cap: (1000, 10000)
- social_baseline: (50, 500)
- additional_dev_days: (0, 15)

**Note**: pro_price and ent_price are fixed (€3,500 and €20,000) and not optimized.

## Feature Development System

### Sequential Development
- Features are developed one after another, not based on launch dates
- Each feature has a required `dev_days` to complete
- Features become active immediately when development completes
- Development progress is tracked per feature

### Important Notes
- Features without effects (`effect=None`) still incur maintenance costs
- Development is sequential - only one feature is worked on at a time
- `maintenance_days` is calculated from active features, not set as a parameter

## Testing Guidelines

### What NOT to Test
- **Dataclass field access**: Don't test trivial getter/setter behavior
- **Type annotations**: Don't test that fields have the correct type
- **Frozen dataclass immutability**: Don't test that frozen dataclasses are immutable
- **Basic arithmetic**: Don't test simple calculations like `revenue = price * users`

### What TO Test
- **Complex business logic**: Test multi-step calculations with edge cases
- **Validation logic**: Test `__post_init__` validation with invalid inputs
- **Feature effects**: Test that effect functions modify the correct context values
- **Simulation flows**: Test that state changes correctly across simulation steps
- **Edge cases**: Test boundary conditions (zero values, maximum values, negative cash)

Remember: Tests should provide value by catching actual bugs, not just increasing code coverage.
