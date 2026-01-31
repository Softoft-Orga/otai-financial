"""Centralized configuration for default assumptions."""

from .models import Assumptions

# Default assumptions used across the application
DEFAULT_ASSUMPTIONS = Assumptions(
    # Time and costs
    months=36,
    dev_day_cost_eur=600.0,
    starting_cash_eur=100_000.0,
    # Fixed costs
    ops_fixed_eur_per_month=5_000.0,
    # Marketing parameters
    ads_cost_per_lead_base=2.0,
    monthly_ads_expense=500.0,
    brand_popularity=1.0,
    # Conversion rates
    conv_lead_to_free=0.25,
    conv_free_to_pro=0.10,
    conv_pro_to_ent=0.02,
    # Churn rates
    churn_free=0.15,
    churn_pro=0.03,
    churn_ent=0.01,
    # Referral and partners
    referral_leads_per_active_free=0.01,
    partner_commission_rate=0.20,
    pro_deals_per_partner_per_month=0.02,
    ent_deals_per_partner_per_month=0.002,
    new_partners_base_per_month=0.1,
    # Financial parameters
    valuation_multiple_arr=10.0,
    # Credit parameters
    credit_interest_rate_annual=0.10,
    credit_draw_amount=100_000.0,
    credit_cash_threshold=50_000.0,
)

# Default policy parameters (fixed, not optimized)
DEFAULT_PRICES = {
    "pro_price": 3500.0,
    "ent_price": 20000.0,
}

# Default development parameters
DEFAULT_DEV_PARAMS = {
    "additional_dev_days": 5.0,  # Additional dev days per month for new features
}

# Default parameter ranges for optimization
# Note: Currently optimized parameters are those in PolicyParams that are not fixed prices
DEFAULT_OPTIMIZATION_RANGES = {
    "ads_start": (100, 2000),
    "ads_growth": (0.0, 0.2),
    "ads_cap": (1000, 10000),
    "social_baseline": (50, 500),
    "additional_dev_days": (0, 15),  # Additional dev days for new features
}
