"""Centralized configuration for default assumptions."""

from __future__ import annotations

from .models import Assumptions, MonthlyDecision, PricingMilestone, ScenarioAssumptions

# Default assumptions used across the application
DEFAULT_ASSUMPTIONS = Assumptions(
    months=24,  # 2-year simulation horizon typical for SaaS financial planning
    starting_cash=35000.0,  # Initial seed capital - THIS IS DEFINITIVE
    # CPC (Cost Per Click) parameters - realistic range for B2B SaaS is 1.5-7 EUR
    cpc_base=2,  # Base CPC at low spend levels (best case scenario)
    cpc_sensitivity_factor=1,
    # CPC scaling factor - controls how quickly CPC increases with spend (increased for stronger diminishing returns)
    cpc_ref_spend=2000.0,  # Reference spend level for CPC calculations
    # SEO (Search Engine Optimization) parameters
    # Competitors typically have Ahrefs Domain Rating (DR) of 40-70
    seo_users_per_eur=1,  # Users generated per EUR spent on SEO content/links

    domain_rating_init=4,
    domain_rating_max=100.0,  # Maximum achievable domain rating (theoretical ceiling)
    domain_rating_spend_sensitivity=0.05,
    # Growth coefficient for DR improvement from SEO spend (lower = harder to grow)
    domain_rating_reference_spend_eur=2000.0,  # Reference monthly SEO spend for DR growth calculations
    domain_rating_decay=0.01,  # Natural monthly decay of domain rating without maintenance
    # Conversion funnel rates (typical B2B SaaS benchmarks)
    conv_web_to_lead=0.05,  # 5% of website visitors become leads (more conservative)
    conv_website_lead_to_free=0.4,
    conv_website_lead_to_pro=0.01,
    conv_website_lead_to_ent=0.005,
    # direct lead -> demo conversion, then demo -> tier conversions
    direct_contacted_demo_conversion=0.01,
    direct_demo_appointment_conversion_to_free=0.05,
    direct_demo_appointment_conversion_to_pro=0.15,
    direct_demo_appointment_conversion_to_ent=0.05,

    conv_free_to_pro=0.01,  # 1% of free users upgrade to paid (reduced from 5%) MONTHLY !
    conv_pro_to_ent=0.005,  # 0.5% of pro users upgrade to enterprise (reduced from 1%)
    # Monthly customer churn rates (industry benchmarks)
    churn_free=0.05,
    churn_pro=0.05,
    churn_ent=0.05,
    # UNUSED irrelevant
    # Pricing (one-time license fees in EUR) - milestone based
    pricing_milestones=(
        PricingMilestone(product_value_min=0.0, pro_price=2500.0, ent_price=10000.0),
        PricingMilestone(product_value_min=100_000.0, pro_price=5000.0, ent_price=20000.0),
        PricingMilestone(product_value_min=200_000.0, pro_price=5500.0, ent_price=22000.0),
        PricingMilestone(product_value_min=400_000.0, pro_price=6000.0, ent_price=24000.0),
        PricingMilestone(product_value_min=800_000.0, pro_price=6_500.0, ent_price=26_000.0),
        PricingMilestone(product_value_min=1_600_000.0, pro_price=7_000.0, ent_price=28_000.0),
        PricingMilestone(product_value_min=3_200_000.0, pro_price=7_500.0, ent_price=30_000.0),
        PricingMilestone(product_value_min=6_400_000.0, pro_price=8_000.0, ent_price=32_000.0),
        PricingMilestone(product_value_min=12_800_000.0, pro_price=8_500.0, ent_price=34_000.0),
    ),

    tax_rate=0.25,  # Corporate tax rate (25% - typical for many European countries)
    market_cap_multiple=3.0,  # Base multiplier
    # Sales costs (one-time cost per new customer acquisition)
    # There must e differentation between the direct and the organic/website
    sales_cost_per_new_pro=200.0,  # There are already direct outreach, payment and other costs!
    sales_cost_per_new_ent=400.0,  # There are already direct outreach, payment and other costs!
    it_infra_cost_per_free_deal=25,
    it_infra_cost_per_pro_deal=150.0,
    it_infra_cost_per_ent_deal=500.0,
    # Support costs (monthly cost per active customer)
    support_cost_per_pro=200.0,  # 30 EUR/month per pro customer (360 EUR/year)
    support_cost_per_ent=400.0,
    # Optional support subscription (premium support add-on)
    support_subscription_fee_pct_pro=0.1,  # per MONTH! so 5000 -> 250 * 12 -> ~ 4000
    support_subscription_fee_pct_ent=0.1,  # per MONTH! so 20000 -> 1000 * 12 -> 12000
    support_subscription_take_rate_pro=0.35,  # 70% of pro customers purchase support subscription
    support_subscription_take_rate_ent=0.70,  # 90% of enterprise customers purchase support subscription
    # Partner program parameters
    partner_spend_ref=2500.0,  # Reference monthly spend to calculate partner acquisition efficiency
    partner_product_value_ref=250_000.0,  # Reference product value for partner acquisition formula
    partner_commission_rate=0.25,  # 25% commission on partner-generated deals (industry standard: 15-30%)
    partner_churn_per_month=0.02,  # 2% monthly partner churn (equivalent to ~22% annual)
    partner_saturation_scale=5.0,  # At 10 active partners, acquisition rate halves; at 20, it's 1/3, etc.
    partner_pro_deals_per_partner_per_month=0.5,  # Average 0.5 pro deals per partner per month
    partner_ent_deals_per_partner_per_month=0.1,  # Average 0.5 enterprise deals per partner per month
    # Operating costs (monthly EUR)
    operating_baseline=500.0,  # Fixed baseline costs (tools, software, basic infrastructure)
    operating_per_user=1,  # Variable cost per active user (hosting, bandwidth, etc.)
    operating_per_dev=0.25,  # Additional cost per dev spend (dev tools, cloud services for development)
    # Lead generation via outreach
    qualified_pool_total=20_000.0,  # Total addressable prospects in the market
    outreach_leads_per_1000_eur=200.0,
    # €1,000 finds ~2,000 leads at low volumes (diminishing returns kick in as pool depletes)
    cost_per_direct_lead=10.0,  # Additional cost per lead to actually contact them
    cost_per_direct_demo=200.0,
    # Debt financing parameters
    debt_interest_rate_annual=0.07,  # Base annual interest rate 7% (when debt is low vs revenue)
    debt_interest_rate_max_annual=0.30,  # Maximum annual interest rate 80% (when debt >> revenue)
    credit_draw_factor=1.25,
    debt_repay_factor=0.25,
    min_months_cash_reserve=3.0,  # Maintain 3 months of cash reserves
    minimum_cash_balance=1_000.0,  # Minimum cash balance for optimizer constraint
    minimum_liquidity_ratio=0.25,  # Minimum (cash + product_value) / debt
    # Product value dynamics (dev spend accumulation with depreciation)
    pv_init=105_000.0,  # Initial product value (starting milestone)
    pv_min=0.0,  # Minimum product value floor
    product_value_depreciation_rate=0.01,  # 1% monthly depreciation
    milestone_achieved_renewal_percentage=0.5,  # 50% of licenses renew on new milestone
    product_renewal_discount_percentage=0.75,
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
_DEFAULT_KNOT_LOWS = [0.01 for _ in range(OPTIMIZER_NUM_KNOTS)]
_DEFAULT_KNOT_HIGHS = [1.5 ** (i + 2) for i in range(OPTIMIZER_NUM_KNOTS)]

OPTIMIZER_KNOT_CONFIG: dict[str, dict[str, list[float]]] = {
    "ads": {"lows": _DEFAULT_KNOT_LOWS, "highs": _DEFAULT_KNOT_HIGHS},
    "seo": {"lows": _DEFAULT_KNOT_LOWS, "highs": _DEFAULT_KNOT_HIGHS},
    "dev": {"lows": _DEFAULT_KNOT_LOWS, "highs": _DEFAULT_KNOT_HIGHS},
    "partner": {"lows": _DEFAULT_KNOT_LOWS, "highs": _DEFAULT_KNOT_HIGHS},
    "outreach": {"lows": _DEFAULT_KNOT_LOWS,
                 "highs": [40 * (i+1) / OPTIMIZER_NUM_KNOTS for i in range(OPTIMIZER_NUM_KNOTS)]},
}

# Warm-start knots: set to a known-good solution to give TPE a strong baseline.
# Each list has OPTIMIZER_NUM_KNOTS values (multipliers on the base decision).
# Set to None to disable warm-starting.
WARM_START_KNOTS: dict[str, list[float]] = {
    "ads": [0.1, 0.5, 0.5, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
    "seo": [0.1, 0.5, 1.0, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
    "dev": [0.5, 1.5, 2.0, 3.0, 4.0, 5.0, 8.0, 9.0, 10.0],
    "partner": [0.1, 0.4, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5],
    "outreach": [2.0, 5.0, 3.0, 2.0, 1.5, 1.0, 0.8, 0.5, 0.1],
}


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
    "debt_interest_rate_annual": 2,
    "debt_interest_rate_max_annual": 3,
    "min_months_cash_reserve": 2,
    "minimum_liquidity_ratio": 2,
    "seo_users_per_eur": 1,
    "domain_rating_spend_sensitivity": 0.25,
    "conv_web_to_lead": 0.7,
    "conv_website_lead_to_free": 0.875,
    "conv_website_lead_to_pro": 0.75,
    "conv_website_lead_to_ent": 0.6,
    "qualified_pool_total": 0.5,
    "direct_contacted_demo_conversion": 1,
    "direct_demo_appointment_conversion_to_pro": 1,
    "direct_demo_appointment_conversion_to_ent": 1,
    "conv_free_to_pro": 0.5,
    "conv_pro_to_ent": 0.5,
    "churn_free": 1.5,
    "churn_pro": 1.5,
    "churn_ent": 1.5,
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

SCENARIO_ASSUMPTIONS: dict[str, ScenarioAssumptions] = {
    "conservative_no_inv": ScenarioAssumptions(
        name="Conservative (Without Investment)",
        assumptions=CONSERVATIVE_WITHOUT_INVESTMENT,
    ),
    "conservative_inv": ScenarioAssumptions(
        name="Conservative (With Investment)",
        assumptions=CONSERVATIVE_WITH_INVESTMENT,
    ),
    "realistic_no_inv": ScenarioAssumptions(
        name="Realistic (Without Investment)",
        assumptions=REALISTIC_WITHOUT_INVESTMENT,
    ),
    "realistic_inv": ScenarioAssumptions(
        name="Realistic (With Investment)",
        assumptions=REALISTIC_WITH_INVESTMENT,
    ),
    "optimistic_no_inv": ScenarioAssumptions(
        name="Optimistic (Without Investment)",
        assumptions=OPTIMISTIC_WITHOUT_INVESTMENT,
    ),
    "optimistic_inv": ScenarioAssumptions(
        name="Optimistic (With Investment)",
        assumptions=OPTIMISTIC_WITH_INVESTMENT,
    ),
}
ALL_SCENARIOS = list(SCENARIO_ASSUMPTIONS.values())
