from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

Month = int


class PricingMilestone(BaseModel):
    product_value_min: float = Field(ge=0, description="Minimum product value to reach this milestone.")
    pro_price: float = Field(ge=0, description="Pro license price for this milestone.")
    ent_price: float = Field(ge=0, description="Enterprise license price for this milestone.")

    model_config = {"frozen": True}


class Assumptions(BaseModel):
    """Core assumptions for the financial forecasting simulation.

    All parameters are validated using Pydantic field validators. These parameters control
    how the simulation evolves month by month, including user acquisition,
    conversion rates, pricing, costs, and financial dynamics.
    """

    # Simulation Time
    months: int = Field(gt=0, description="Number of months to simulate. Must be > 0.")

    # Initial Financial State
    starting_cash: float = Field(ge=0, description="Initial cash on hand at month 0. Must be >= 0.")
    base_organic_users_per_month: float = Field(ge=0, description="Baseline organic users acquired per month without any SEO. Must be >= 0.")

    # CPC (Cost Per Click) Model - Dynamic with diminishing returns
    cpc_base: float = Field(ge=0, description="Base CPC at zero ad spend. Must be >= 0.")
    cpc_sensitivity_factor: float = Field(ge=0, description="CPC scaling factor for ad spend. Must be >= 0.")
    cpc_ref_spend: float = Field(gt=0, description="Reference ad spend for CPC calculation. Must be > 0.")

    # SEO Model - Accumulating stock
    seo_users_per_eur: float = Field(ge=0, description="SEO efficiency: users generated per euro spent. Must be >= 0.")

    # Domain Rating - Grows with SEO spend, decays over time
    domain_rating_init: float = Field(ge=0, description="Initial domain rating at month 0. Must be >= 0.")
    domain_rating_max: float = Field(gt=0, description="Maximum possible domain rating. Must be > 0.")
    domain_rating_spend_sensitivity: float = Field(ge=0, description="Domain rating growth coefficient. Must be >= 0.")
    domain_rating_reference_spend_eur: float = Field(gt=0, description="Reference SEO spend for domain rating growth. Must be > 0.")
    domain_rating_decay: float = Field(ge=0, le=1, description="Monthly domain rating decay (0-1). Must be in [0, 1].")

    # Conversion Funnel - Base rates affected by product value
    conv_web_to_lead: float = Field(ge=0, le=1, description="Base conversion rate: website visitors to leads. Must be in [0, 1].")
    conv_website_lead_to_free: float = Field(ge=0, le=1)
    conv_website_lead_to_pro: float = Field(ge=0, le=1)
    conv_website_lead_to_ent: float = Field(ge=0, le=1)
    direct_contacted_demo_conversion: float = Field(ge=0, le=1)
    direct_demo_appointment_conversion_to_free: float = Field(ge=0, le=1)
    direct_demo_appointment_conversion_to_pro: float = Field(ge=0, le=1)
    direct_demo_appointment_conversion_to_ent: float = Field(ge=0, le=1)
    conv_free_to_pro: float = Field(ge=0, le=1, description="Base conversion rate: free to paid pro users. Must be in [0, 1].")
    conv_pro_to_ent: float = Field(ge=0, le=1, description="Base conversion rate: pro to enterprise users. Must be in [0, 1].")

    # Churn Rates - Base rates affected by product value
    churn_free: float = Field(ge=0, le=1, description="Base monthly churn rate for free users (0-1). Must be in [0, 1].")
    churn_pro: float = Field(ge=0, le=1, description="Base monthly churn rate for pro users (0-1). Must be in [0, 1].")
    churn_ent: float = Field(ge=0, le=1, description="Base monthly churn rate for enterprise users (0-1). Must be in [0, 1].")

    # Pricing milestones (step-wise by product value)
    pricing_milestones: tuple[PricingMilestone, ...] = Field(
        min_length=1,
        description="Ordered pricing milestones keyed by product value thresholds.",
    )

    # Financial Parameters
    tax_rate: float = Field(ge=0, le=1, description="Corporate tax rate on profit (0-1). Must be in [0, 1].")
    market_cap_multiple: float = Field(ge=0, description="Valuation multiple applied to TTM revenue. Must be >= 0.")

    # Sales & Support Costs
    sales_cost_per_new_pro: float = Field(ge=0, description="Sales cost for each new pro customer. Must be >= 0.")
    sales_cost_per_new_ent: float = Field(ge=0, description="Sales cost for each new enterprise customer. Must be >= 0.")
    support_cost_per_pro: float = Field(ge=0, description="Monthly support cost per pro user. Must be >= 0.")
    support_cost_per_ent: float = Field(ge=0, description="Monthly support cost per enterprise user. Must be >= 0.")
    support_subscription_fee_pct_pro: float = Field(ge=0, le=1)
    support_subscription_fee_pct_ent: float = Field(ge=0, le=1)
    support_subscription_take_rate_pro: float = Field(ge=0, le=1)
    support_subscription_take_rate_ent: float = Field(ge=0, le=1)

    # Partner Program
    partner_spend_ref: float = Field(gt=0)
    partner_product_value_ref: float = Field(gt=0)
    partner_commission_rate: float = Field(ge=0, le=1)
    partner_churn_per_month: float = Field(ge=0, le=1)
    partner_pro_deals_per_partner_per_month: float = Field(ge=0)
    partner_ent_deals_per_partner_per_month: float = Field(ge=0)

    # Operating Costs
    operating_baseline: float = Field(ge=0, description="Fixed baseline operating costs per month. Must be >= 0.")
    operating_per_user: float = Field(ge=0, description="Variable operating cost per user (all tiers). Must be >= 0.")
    operating_per_dev: float = Field(ge=0, description="Operating cost multiplier per dev spend euro. Must be >= 0.")

    # Scraping & Outreach Model
    qualified_pool_total: float = Field(ge=0, description="Total size of qualified prospects pool. Must be >= 0.")
    scraping_efficiency_k: float = Field(ge=0, description="Scraping efficiency coefficient. Must be >= 0.")
    scraping_ref_spend: float = Field(gt=0, description="Reference scraping spend for efficiency calculation. Must be > 0.")
    cost_per_direct_lead: float = Field(ge=0, description="Cost to contact one direct lead. Must be >= 0.")
    cost_per_direct_demo: float = Field(ge=0, description="Cost to run one direct demo appointment. Must be >= 0.")

    # Debt & Credit Model
    debt_interest_rate_base_annual: float = Field(ge=0, description="Base annual interest rate (used with revenue scaling). Must be >= 0.")
    credit_draw_factor: float = Field(ge=0, description="Multiplier applied to negative cashflow for credit draw.")
    debt_repay_factor: float = Field(ge=0, description="Multiplier applied to positive cashflow for debt repayment.")

    # Product Value Model - Accumulates with dev spend, decays without
    pv_init: float = Field(ge=0, description="Initial product value at month 0. Must be >= 0.")
    pv_min: float = Field(ge=0, description="Minimum product value (decay limit). Must be >= 0.")
    product_value_depreciation_rate: float = Field(
        ge=0,
        le=1,
        description="Monthly depreciation rate for product value (0-1).",
    )
    milestone_achieved_renewal_percentage: float = Field(
        ge=0,
        le=1,
        description="Share of active licenses that renew when a new milestone is achieved (0-1).",
    )
    product_renewal_discount_percentage: float = Field(
        ge=0,
        le=1,
        description="Discount applied to milestone renewal price (0-1).",
    )

    # Cost Category Assumptions
    payment_processing_rate: float = Field(ge=0, le=1, description="Payment processing fee rate as percentage of revenue (0-1).")
    dev_capex_ratio: float = Field(ge=0, le=1, description="Portion of dev spend that is capitalized as CAPEX (0-1).")

    # Add stricter constraints with validators
    @field_validator('domain_rating_init')
    @classmethod
    def domain_rating_init_must_be_le_max(cls, v: float, info: Any) -> float:
        if 'domain_rating_max' in info.data and v > info.data['domain_rating_max']:
            raise ValueError('domain_rating_init must be <= domain_rating_max')
        return v


    @field_validator('pv_min')
    @classmethod
    def pv_min_must_be_le_pv_init(cls, v: float, info: Any) -> float:
        if 'pv_init' in info.data and v > info.data['pv_init']:
            raise ValueError('pv_min must be <= pv_init')
        return v

    @model_validator(mode="after")
    def pricing_milestones_ordered(self) -> "Assumptions":
        milestones = list(self.pricing_milestones)
        if not milestones:
            raise ValueError("pricing_milestones must have at least one entry")
        if milestones[0].product_value_min != 0:
            raise ValueError("pricing_milestones must start at product_value_min = 0")
        for prev, current in zip(milestones, milestones[1:]):
            if current.product_value_min <= prev.product_value_min:
                raise ValueError("pricing_milestones must be strictly increasing")
        for milestone in milestones:
            if milestone.ent_price < milestone.pro_price:
                raise ValueError("enterprise price must be >= pro price in pricing_milestones")
            if milestone.pro_price > 100_000:
                raise ValueError("pro price must be <= €100,000 for realistic business modeling")
            if milestone.ent_price > 500_000:
                raise ValueError("enterprise price must be <= €500,000 for realistic business modeling")
        return self

    # Add reasonable upper bounds for critical business metrics
    @field_validator('conv_web_to_lead', 'conv_website_lead_to_free', 'conv_website_lead_to_pro', 'conv_website_lead_to_ent',
                     'direct_contacted_demo_conversion', 'direct_demo_appointment_conversion_to_free',
                     'direct_demo_appointment_conversion_to_pro', 'direct_demo_appointment_conversion_to_ent',
                     'conv_free_to_pro', 'conv_pro_to_ent')
    @classmethod
    def conversion_rates_reasonable_upper_bound(cls, v: float) -> float:
        if v > 0.5:  # No conversion rate should exceed 50%
            raise ValueError('Conversion rates must be <= 0.5 (50%) for realistic business modeling')
        return v

    @field_validator('churn_free', 'churn_pro', 'churn_ent')
    @classmethod
    def churn_rates_reasonable_upper_bound(cls, v: float) -> float:
        if v > 0.3:  # Churn rates shouldn't exceed 30% per month
            raise ValueError('Churn rates must be <= 0.3 (30%) per month for realistic business modeling')
        return v

    @field_validator('cpc_base')
    @classmethod
    def cpc_reasonable_upper_bound(cls, v: float) -> float:
        if v > 100:  # CPC shouldn't exceed €100
            raise ValueError('CPC must be <= €100 for realistic business modeling')
        return v

    @field_validator('months')
    @classmethod
    def months_reasonable_upper_bound(cls, v: int) -> int:
        if v > 120:  # Max 10 years
            raise ValueError('Simulation duration must be <= 120 months (10 years)')
        return v

    @field_validator('starting_cash')
    @classmethod
    def starting_cash_reasonable_upper_bound(cls, v: float) -> float:
        if v > 100_000_000:  # Max €100M starting cash
            raise ValueError('Starting cash must be <= €100M for realistic business modeling')
        return v

    @field_validator('market_cap_multiple')
    @classmethod
    def market_cap_multiple_reasonable_bound(cls, v: float) -> float:
        if v > 100:  # Max 100x revenue multiple
            raise ValueError('Market cap multiple must be <= 100 for realistic business modeling')
        return v

    model_config = {"frozen": True}


class MonthlyDecision(BaseModel):
    """Monthly decision variables that control the simulation.

    These are the levers you can pull each month to influence growth,
    costs, and financial outcomes. All spend values are in euros.
    """

    # Marketing & Growth Spend
    ads_budget: float = Field(ge=0, description="Monthly advertising spend (e.g., Google Ads, Facebook). Must be >= 0.")
    seo_budget: float = Field(ge=0, description="Monthly organic marketing investment (SEO, content, etc.). Must be >= 0.")
    
    # Product Development
    dev_budget: float = Field(ge=0, description="Monthly product development spend. Must be >= 0.")
    
    # Sales & Outreach
    outreach_budget: float = Field(ge=0, description="Monthly spend on prospect scraping tools/services. Must be >= 0.")
    partner_budget: float = Field(ge=0, description="Monthly spend on partner program management. Must be >= 0.")
    
    # Optional price overrides (for testing or manual control)
    pro_price_override: float | None = Field(default=None, description="Optional override for pro plan price. If None, uses dynamic pricing.")
    ent_price_override: float | None = Field(default=None, description="Optional override for enterprise plan price. If None, uses dynamic pricing.")

    # Add reasonable upper bounds for budgets
    @field_validator('ads_budget', 'seo_budget', 'dev_budget', 'outreach_budget', 'partner_budget')
    @classmethod
    def budget_reasonable_upper_bound(cls, v: float) -> float:
        if v > 10_000_000:  # Max €10M per month for any budget
            raise ValueError('Monthly budgets must be <= €10M for realistic business modeling')
        return v

    @field_validator('pro_price_override', 'ent_price_override')
    @classmethod
    def price_override_reasonable_bound(cls, v: float | None) -> float | None:
        if v is not None and v > 100_000:  # Max €100k for price overrides
            raise ValueError('Price overrides must be <= €100,000 for realistic business modeling')
        return v

    model_config = {"frozen": True}


type MonthlyDecisions = list["MonthlyDecision"]


class State(BaseModel):
    """Current state of the simulation at a given month.

    This represents the cumulative effects of all previous decisions and
    assumptions. State evolves month by month based on MonthlyCalculated values.
    """

    # Time
    month: Month = Field(ge=0, description="Current month number (0-indexed). Must be >= 0.")

    # Financial Position
    cash: float = Field(description="Current cash on hand. Can be negative if credit is used.")
    debt: float = Field(ge=0, description="Total debt accumulated. Must be >= 0.")

    # Marketing Assets
    domain_rating: float = Field(ge=0, description="Current domain rating (0 to domain_rating_max). Must be >= 0.")
    product_value: float = Field(gt=0, description="Current product value index. Must be > 0.")

    # User Base
    free_active: float = Field(ge=0, description="Current active free tier users. Must be >= 0.")
    pro_active: float = Field(ge=0, description="Current active pro tier users. Must be >= 0.")
    ent_active: float = Field(ge=0, description="Current active enterprise users. Must be >= 0.")
    partners_active: float = Field(ge=0)

    qualified_pool_remaining: float = Field(ge=0, description="Remaining prospects in the market that haven't been scraped yet. Must be >= 0.")
    website_leads: float = Field(ge=0, description="Website leads carried into this month for conversion.")
    direct_demo_appointments: float = Field(ge=0, description="Direct demo appointments available for conversion this month.")
    revenue_history: tuple[float, ...] = Field(
        default_factory=tuple,
        description="Trailing revenue history (up to 12 months).",
    )

    # Add reasonable upper bounds
    @field_validator('cash')
    @classmethod
    def cash_reasonable_bound(cls, v: float) -> float:
        if v > 1_000_000_000:  # Max €1B cash
            raise ValueError('Cash must be <= €1B for realistic business modeling')
        if v < -1_000_000_000:  # Min -€1B cash
            raise ValueError('Cash must be >= -€1B for realistic business modeling')
        return v

    @field_validator('debt')
    @classmethod
    def debt_reasonable_upper_bound(cls, v: float) -> float:
        if v > 1_000_000_000:  # Max €1B debt
            raise ValueError('Debt must be <= €1B for realistic business modeling')
        return v

    @field_validator('domain_rating')
    @classmethod
    def domain_rating_reasonable_upper_bound(cls, v: float) -> float:
        if v > 100:  # Max domain rating of 100
            raise ValueError('Domain rating must be <= 100 for realistic business modeling')
        return v

    @field_validator('product_value')
    @classmethod
    def product_value_reasonable_bound(cls, v: float) -> float:
        if v > 1_000_000_000:  # Max product value of 1B
            raise ValueError('Product value must be <= 1B for realistic business modeling')
        return v

    @field_validator('free_active', 'pro_active', 'ent_active')
    @classmethod
    def active_users_reasonable_upper_bound(cls, v: float) -> float:
        if v > 100_000_000:  # Max 100M users
            raise ValueError('Active user counts must be <= 100M for realistic business modeling')
        return v

    @field_validator('partners_active')
    @classmethod
    def partners_active_reasonable_upper_bound(cls, v: float) -> float:
        if v > 10_000:  # Max 10k partners
            raise ValueError('Active partners must be <= 10,000 for realistic business modeling')
        return v

    @field_validator('qualified_pool_remaining')
    @classmethod
    def qualified_pool_reasonable_upper_bound(cls, v: float) -> float:
        if v > 100_000_000:  # Max 100M prospects
            raise ValueError('Qualified pool must be <= 100M for realistic business modeling')
        return v


class MonthlyCalculated(BaseModel):
    """All calculated values for a single month.

    These are the outputs of the simulation for each month, calculated
    from the current State, Assumptions, and MonthlyDecision.
    """

    month: Month = Field(ge=0, description="Month number for these calculations (0-indexed).")

    # Product Value & Pricing
    product_value_next: float = Field(ge=0, description="Product value for next month. Must be >= 0.")
    pro_price: float = Field(ge=0, description="Effective pro tier price for this month.")
    ent_price: float = Field(ge=0, description="Effective enterprise tier price for this month.")
    renewal_upgrade_rate: float = Field(ge=0, le=1)
    renewal_discount_rate: float = Field(ge=0, le=1)
    monthly_renewal_fee: float = Field(ge=0)

    pro_support_subscribers: float = Field(ge=0)
    ent_support_subscribers: float = Field(ge=0)
    support_subscription_revenue_pro: float = Field(ge=0)
    support_subscription_revenue_ent: float = Field(ge=0)
    support_subscription_revenue_total: float = Field(ge=0)

    new_partners: float = Field(ge=0)
    churned_partners: float = Field(ge=0)
    partner_pro_deals: float = Field(ge=0)
    partner_ent_deals: float = Field(ge=0)
    partner_commission_cost: float = Field(ge=0)

    # Effective Conversion Rates (after product value effects)
    conv_web_to_lead_eff: float = Field(ge=0, le=1, description="Effective web-to-lead conversion rate.")
    conv_website_lead_to_free_eff: float = Field(ge=0, le=1, description="Effective website lead-to-free conversion rate.")
    conv_website_lead_to_pro_eff: float = Field(ge=0, le=1, description="Effective website lead-to-pro conversion rate.")
    conv_website_lead_to_ent_eff: float = Field(ge=0, le=1, description="Effective website lead-to-enterprise conversion rate.")
    direct_contacted_demo_conversion_eff: float = Field(ge=0, le=1, description="Effective direct lead-to-demo conversion rate.")
    direct_demo_appointment_conversion_to_free_eff: float = Field(ge=0, le=1, description="Effective demo-to-free conversion rate.")
    direct_demo_appointment_conversion_to_pro_eff: float = Field(ge=0, le=1, description="Effective demo-to-pro conversion rate.")
    direct_demo_appointment_conversion_to_ent_eff: float = Field(ge=0, le=1, description="Effective demo-to-enterprise conversion rate.")
    upgrade_free_to_pro_eff: float = Field(ge=0, le=1, description="Effective free-to-pro conversion rate.")
    upgrade_pro_to_ent_eff: float = Field(ge=0, le=1, description="Effective pro-to-enterprise conversion rate.")

    # Effective Churn Rates (after product value effects)
    churn_free_eff: float = Field(ge=0, le=1, description="Effective free user churn rate.")
    churn_pro_eff: float = Field(ge=0, le=1, description="Effective pro user churn rate.")
    churn_ent_eff: float = Field(ge=0, le=1, description="Effective enterprise churn rate.")

    # Traffic & Acquisition Metrics
    ads_clicks: float = Field(ge=0, description="Number of clicks from ad spend.")
    domain_rating_next: float = Field(ge=0, description="Domain rating for next month.")
    qualified_pool_remaining_next: float = Field(ge=0, description="Remaining prospects in the market for next month.")
    website_users: float = Field(ge=0, description="Total website visitors this month.")
    website_leads: float = Field(ge=0, description="New website leads generated this month.")
    website_leads_available: float = Field(ge=0, description="Website leads available for conversion this month.")
    annual_revenue_ttm: float = Field(ge=0, description="Trailing 12-month revenue used for debt pricing.")

    # Scraping & Outreach Funnel
    new_direct_leads: float = Field(ge=0, description="New direct leads discovered via scraping.")
    direct_contacted_leads: float = Field(ge=0, description="Direct leads contacted this month.")
    direct_contacted_cost: float = Field(ge=0, description="Cost to contact direct leads this month.")
    new_direct_demo_appointments: float = Field(ge=0, description="New demo appointments scheduled from outreach.")
    direct_demo_appointments_available: float = Field(ge=0, description="Demo appointments available for conversion this month.")
    direct_demo_appointment_cost: float = Field(ge=0, description="Cost to run demo appointments this month.")
    leads_total: float = Field(ge=0, description="Total leads from all sources.")

    # User Acquisition & Churn
    new_free: float = Field(ge=0, description="New free users acquired this month.")
    new_pro: float = Field(ge=0, description="New pro users acquired this month.")
    new_ent: float = Field(ge=0, description="New enterprise users acquired this month.")
    free_next: float = Field(ge=0, description="Free users count for next period (after churn and upgrades).")
    pro_next: float = Field(ge=0, description="Pro users count for next period (after churn and upgrades).")
    ent_next: float = Field(ge=0, description="Enterprise users count for next period (after churn and upgrades).")
    upgraded_to_pro: float = Field(ge=0)
    upgraded_to_ent: float = Field(ge=0)
    churned_free: float = Field(ge=0, description="Free users lost this month.")
    churned_pro: float = Field(ge=0, description="Pro users lost this month.")
    churned_ent: float = Field(ge=0, description="Enterprise users lost this month.")

    # Costs
    sales_spend: float = Field(ge=0, description="Total sales costs this month.")
    support_spend: float = Field(ge=0, description="Total support costs this month.")

    # Debt & Interest
    interest_rate_annual_eff: float = Field(ge=0, description="Effective annual interest rate based on current debt.")
    interest_payment: float = Field(ge=0, description="Monthly interest payment on debt.")
    new_credit_draw: float = Field(ge=0, description="Credit drawn this month based on cashflow.")
    debt_repayment: float = Field(ge=0, description="Debt repayment amount applied this month.")

    # Financial Results
    revenue_pro: float = Field(ge=0, description="Revenue from new pro tier customers (one-time licenses).")
    revenue_ent: float = Field(ge=0, description="Revenue from new enterprise customers (one-time licenses).")
    revenue_total: float = Field(ge=0, description="Total monthly revenue.")
    costs_ex_tax: float = Field(description="Total costs before tax.")
    cost_of_goods_sold: float = Field(ge=0, description="Cost of Goods Sold (COGS) - Direct costs to produce/deliver the product.")
    operating_expenses: float = Field(ge=0, description="Operating Expenses (OPEX) - Costs to run the company.")
    capital_expenditure: float = Field(ge=0, description="Capital Expenditures (CAPEX) - Long-term investments.")
    financial_expenses: float = Field(ge=0, description="Financial / Non-operating costs.")
    profit_bt: float = Field(description="Profit before tax.")
    tax: float = Field(ge=0, description="Tax payment for the month.")
    net_cashflow: float = Field(description="Net cash flow for the month (must be finite).")

    # Additional fields for enhanced plotting
    spend_last_month: float = Field(ge=0, description="Total spend in the previous month.")

    # Detailed revenue breakdowns for plotting
    revenue_pro_website: float = Field(ge=0)
    revenue_pro_outreach: float = Field(ge=0)
    revenue_pro_partner: float = Field(ge=0)
    revenue_ent_website: float = Field(ge=0)
    revenue_ent_outreach: float = Field(ge=0)
    revenue_ent_partner: float = Field(ge=0)
    revenue_renewal_pro: float = Field(ge=0)
    revenue_renewal_ent: float = Field(ge=0)
    revenue_support_pro: float = Field(ge=0)
    revenue_support_ent: float = Field(ge=0)

    # Detailed cost breakdowns for plotting
    cost_sales_marketing: float = Field(ge=0)
    cost_rd_expense: float = Field(ge=0)
    cost_ga: float = Field(ge=0)
    cost_customer_support: float = Field(ge=0)
    cost_it_tools: float = Field(ge=0)
    cost_payment_processing: float = Field(ge=0)
    cost_outreach_conversion: float = Field(ge=0)
    cost_partner_commission: float = Field(ge=0)

    @field_validator('net_cashflow')
    @classmethod
    def net_cashflow_must_be_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError('net_cashflow must be finite')
        return v

    # Add reasonable bounds for financial metrics
    @field_validator('revenue_total', 'costs_ex_tax', 'profit_bt')
    @classmethod
    def financial_metrics_reasonable_bound(cls, v: float) -> float:
        if abs(v) > 1_000_000_000:  # Max €1B absolute value
            raise ValueError('Financial metrics must be <= €1B in absolute value for realistic business modeling')
        return v

    @field_validator('pro_price', 'ent_price')
    @classmethod
    def effective_price_reasonable_bound(cls, v: float) -> float:
        if v > 1_000_000:  # Max €1M for effective prices
            raise ValueError('Effective prices must be <= €1M for realistic business modeling')
        return v

    model_config = {"frozen": True}
