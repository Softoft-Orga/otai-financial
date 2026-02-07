"""Centralized configuration for default assumptions."""

from __future__ import annotations

from .models import Assumptions, MonthlyDecision, PricingMilestone, ScenarioAssumptions

# Default assumptions used across the application
DEFAULT_ASSUMPTIONS = Assumptions(
    months=24,  # 2-year simulation horizon typical for SaaS financial planning
    starting_cash=25000.0,  # Initial seed capital - THIS IS DEFINITIVE
    # CPC (Cost Per Click) parameters - realistic range for B2B SaaS is 1.5-7 EUR
    cpc_base=2,  # Base CPC at low spend levels (best case scenario)
    cpc_sensitivity_factor=0.4,
    # CPC scaling factor - controls how quickly CPC increases with spend (increased for stronger diminishing returns)
    cpc_ref_spend=2000.0,  # Reference spend level for CPC calculations
    # SEO (Search Engine Optimization) parameters
    # Competitors typically have Ahrefs Domain Rating (DR) of 40-70
    seo_users_per_eur=0.5,  # Users generated per EUR spent on SEO content/links

    domain_rating_init=1,
    domain_rating_max=100.0,  # Maximum achievable domain rating (theoretical ceiling)
    domain_rating_spend_sensitivity=0.1,
    # ? How exactly calculated ? Growth coefficient for DR improvement from SEO spend
    domain_rating_reference_spend_eur=100.0,  # Reference monthly SEO spend for DR growth calculations
    domain_rating_decay=0.02,  # Natural monthly decay of domain rating without maintenance
    # Conversion funnel rates (typical B2B SaaS benchmarks)
    conv_web_to_lead=0.05,  # 5% of website visitors become leads (more conservative)
    conv_website_lead_to_free=0.4,
    conv_website_lead_to_pro=0.01,
    conv_website_lead_to_ent=0.005,
    # direct lead -> demo conversion, then demo -> tier conversions
    direct_contacted_demo_conversion=0.01,
    direct_demo_appointment_conversion_to_free=0.1,
    direct_demo_appointment_conversion_to_pro=0.1,
    direct_demo_appointment_conversion_to_ent=0.05,

    conv_free_to_pro=0.01,  # 1% of free users upgrade to paid (reduced from 5%) MONTHLY !
    conv_pro_to_ent=0.005,  # 0.5% of pro users upgrade to enterprise (reduced from 1%)
    # Monthly customer churn rates (industry benchmarks)
    churn_free=0.05,  #
    churn_pro=0.05,  # 4% monthly churn for pro users (equivalent to ~39% annual - typical for SMB SaaS)
    churn_ent=0.05,  # 1.5% monthly churn for enterprise (equivalent to ~17% annual - low due to contracts)
    # UNUSED irrelevant
    # Pricing (one-time license fees in EUR) - milestone based
    pricing_milestones=(
        PricingMilestone(product_value_min=0.0, pro_price=2500.0, ent_price=10000.0),
        PricingMilestone(product_value_min=100_000.0, pro_price=5000.0, ent_price=20000.0),
        PricingMilestone(product_value_min=250_000.0, pro_price=6000.0, ent_price=22500.0),
        PricingMilestone(product_value_min=500_000.0, pro_price=6500.0, ent_price=25000.0),
        PricingMilestone(product_value_min=1_000_000.0, pro_price=8_000.0, ent_price=30_000.0),
        PricingMilestone(product_value_min=2_500_000.0, pro_price=9_000.0, ent_price=35_000.0),
    ),

    tax_rate=0.25,  # Corporate tax rate (25% - typical for many European countries)
    market_cap_multiple=4.0,  # Revenue multiple for valuation (8x TTM revenue - realistic for growing SaaS)
    # Sales costs (one-time cost per new customer acquisition)
    # There must e differentation between the direct and the organic/website
    sales_cost_per_new_pro=200.0,  # There are already direct outreach, payment and other costs!
    sales_cost_per_new_ent=200.0,  # There are already direct outreach, payment and other costs!
    it_infra_cost_per_free_deal=10.0,
    it_infra_cost_per_pro_deal=100.0,
    it_infra_cost_per_ent_deal=500.0,
    # Support costs (monthly cost per active customer)
    support_cost_per_pro=200.0,  # 30 EUR/month per pro customer (360 EUR/year)
    support_cost_per_ent=600.0,
    # Optional support subscription (premium support add-on)
    support_subscription_fee_pct_pro=0.05,  # per MONTH! so 5000 -> 250 * 12 -> ~ 4000
    support_subscription_fee_pct_ent=0.05,  # per MONTH! so 20000 -> 1000 * 12 -> 12000
    support_subscription_take_rate_pro=0.70,  # 70% of pro customers purchase support subscription
    support_subscription_take_rate_ent=0.90,  # 90% of enterprise customers purchase support subscription
    # Partner program parameters
    partner_spend_ref=1000.0,  # Reference monthly spend to calculate partner acquisition efficiency
    partner_product_value_ref=100_000.0,  # Reference product value for partner acquisition formula
    partner_commission_rate=0.25,  # 20% commission on partner-generated deals (industry standard: 15-30%)
    partner_churn_per_month=0.02,  # 2% monthly partner churn (equivalent to ~22% annual)
    partner_pro_deals_per_partner_per_month=0.5,  # Average 0.5 pro deals per partner per month
    partner_ent_deals_per_partner_per_month=0.1,  # Average 0.5 enterprise deals per partner per month
    # Operating costs (monthly EUR)
    operating_baseline=1000.0,  # Fixed baseline costs (tools, software, basic infrastructure)
    operating_per_user=2.0,  # Variable cost per active user (hosting, bandwidth, etc.)
    operating_per_dev=0.1,  # Additional cost per dev spend (dev tools, cloud services for development)
    # Lead generation via scraping/outreach
    qualified_pool_total=20_000.0,  # Total addressable prospects in the market (reduced from 5,000 for more realism)
    scraping_efficiency_k=0.2,  # Efficiency factor for scraping (reduced from 0.8 for stronger diminishing returns)
    scraping_ref_spend=1000.0,  # Reference monthly spend for scraping calculations
    cost_per_direct_lead=10.0,
    cost_per_direct_demo=200.0,
    # Debt financing parameters
    debt_interest_rate_base_annual=0.08,  # Base annual interest rate 8%
    debt_interest_rate_sensitivity_factor=0.5,  # Sensitivity factor for interest rate scaling with revenue
    credit_draw_factor=1.25,
    debt_repay_factor=0.25,
    min_months_cash_reserve=3.0,  # Maintain 3 months of cash reserves
    minimum_cash_balance=5_000.0,  # Minimum cash balance for optimizer constraint
    minimum_liquidity_ratio=0.25,  # Minimum (cash + product_value) / debt
    # Product value dynamics (dev spend accumulation with depreciation)
    pv_init=80_000.0,  # Initial product value (starting milestone)
    pv_min=0.0,  # Minimum product value floor
    product_value_depreciation_rate=0.02,  # 2% monthly depreciation ~ 30% yearly
    milestone_achieved_renewal_percentage=0.5,  # 50% of licenses renew on new milestone
    product_renewal_discount_percentage=0.75,  # 50% discount on renewal price
    # Cost Category Assumptions
    payment_processing_rate=0.02,  # Payment processing fee rate (2% of revenue)
    dev_capex_ratio=0.3,  # Portion of dev spend that is capitalized as CAPEX (30%)
)

DEFAULT_DECISION = MonthlyDecision(
    ads_budget=1000.0,
    seo_budget=1000.0,
    dev_budget=1000.0,
    partner_budget=1000.0,
    outreach_budget=1000.0,
)

RUN_BASE_DECISION = DEFAULT_DECISION

OPTIMIZER_NUM_KNOTS = 9
OPTIMIZER_KNOT_LOWS = [0.1 + 0.2 * (i + 1) for i in range(OPTIMIZER_NUM_KNOTS)]
OPTIMIZER_KNOT_HIGHS = [8 * 2 ** (i + 2) for i in range(OPTIMIZER_NUM_KNOTS)]


def build_base_decisions(months: int, base_decision: MonthlyDecision) -> list[MonthlyDecision]:
    return [base_decision.model_copy() for _ in range(months)]


def _scale_assumptions(
    base: Assumptions,
    multipliers: dict[str, float],
) -> Assumptions:
    return base.model_copy(
        update={
            field: getattr(base, field) * multiplier
            for field, multiplier in multipliers.items()
        }
    )

CONSERVATIVE_MULTIPLIERS: dict[str, float] = {
    "seo_users_per_eur": 0.8,
    "conv_web_to_lead": 0.7,
    "conv_website_lead_to_free": 0.875,
    "conv_website_lead_to_pro": 0.75,
    "conv_website_lead_to_ent": 0.6,
    "direct_contacted_demo_conversion": 0.8,
    "direct_demo_appointment_conversion_to_pro": 0.8,
    "direct_demo_appointment_conversion_to_ent": 0.8,
    "conv_free_to_pro": 0.8,
    "conv_pro_to_ent": 0.8,
    "churn_free": 1.4,
    "churn_pro": 1.2,
    "churn_ent": 1.0,
}

CONSERVATIVE_ASSUMPTIONS = _scale_assumptions(
    DEFAULT_ASSUMPTIONS,
    CONSERVATIVE_MULTIPLIERS,
)

OPTIMISTIC_MULTIPLIERS: dict[str, float] = {
    "seo_users_per_eur": 1.4,
    "conv_web_to_lead": 1.4,
    "conv_website_lead_to_free": 1.125,
    "conv_website_lead_to_pro": 2.0,
    "conv_website_lead_to_ent": 2.0,
    "direct_contacted_demo_conversion": 1.5,
    "direct_demo_appointment_conversion_to_pro": 1.5,
    "direct_demo_appointment_conversion_to_ent": 1.6,
    "conv_free_to_pro": 2.0,
    "conv_pro_to_ent": 2.0,
    "churn_free": 0.8,
    "churn_pro": 0.6,
    "churn_ent": 0.4,
}

OPTIMISTIC_ASSUMPTIONS = _scale_assumptions(
    DEFAULT_ASSUMPTIONS,
    OPTIMISTIC_MULTIPLIERS,
)

INVESTMENT_STARTING_CASH = 250_000.0


def _with_investment(base: Assumptions) -> Assumptions:
    return base.model_copy(update={"starting_cash": INVESTMENT_STARTING_CASH})


def _without_investment(base: Assumptions) -> Assumptions:
    return base.model_copy(update={"starting_cash": DEFAULT_ASSUMPTIONS.starting_cash})


CONSERVATIVE_WITH_INVESTMENT = _with_investment(CONSERVATIVE_ASSUMPTIONS)
CONSERVATIVE_WITHOUT_INVESTMENT = _without_investment(CONSERVATIVE_ASSUMPTIONS)
REALISTIC_WITH_INVESTMENT = _with_investment(DEFAULT_ASSUMPTIONS)
REALISTIC_WITHOUT_INVESTMENT = _without_investment(DEFAULT_ASSUMPTIONS)
OPTIMISTIC_WITH_INVESTMENT = _with_investment(OPTIMISTIC_ASSUMPTIONS)
OPTIMISTIC_WITHOUT_INVESTMENT = _without_investment(OPTIMISTIC_ASSUMPTIONS)

SCENARIO_ASSUMPTIONS: tuple[ScenarioAssumptions, ...] = (
    ScenarioAssumptions(
        name="Conservative (Without Investment)",
        assumptions=CONSERVATIVE_WITHOUT_INVESTMENT,
    ),
    ScenarioAssumptions(
        name="Conservative (With Investment)",
        assumptions=CONSERVATIVE_WITH_INVESTMENT,
    ),
    ScenarioAssumptions(
        name="Realistic (Without Investment)",
        assumptions=REALISTIC_WITHOUT_INVESTMENT,
    ),
    ScenarioAssumptions(
        name="Realistic (With Investment)",
        assumptions=REALISTIC_WITH_INVESTMENT,
    ),
    ScenarioAssumptions(
        name="Optimistic (Without Investment)",
        assumptions=OPTIMISTIC_WITHOUT_INVESTMENT,
    ),
    ScenarioAssumptions(
        name="Optimistic (With Investment)",
        assumptions=OPTIMISTIC_WITH_INVESTMENT,
    ),
)
