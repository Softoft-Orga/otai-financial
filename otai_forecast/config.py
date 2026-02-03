"""Centralized configuration for default assumptions."""

from __future__ import annotations

from .models import Assumptions, PricingMilestone

# Default assumptions used across the application
DEFAULT_ASSUMPTIONS = Assumptions(
    months=36,  # 3-year simulation horizon typical for SaaS financial planning
    starting_cash=25000.0,  # Initial seed capital - THIS IS DEFINITIVE
    base_organic_users_per_month=25.0,  # Reduced baseline organic traffic
    # CPC (Cost Per Click) parameters - realistic range for B2B SaaS is 1.5-7 EUR
    cpc_base=2,  # Base CPC at low spend levels (best case scenario)
    cpc_sensitivity_factor=0.5,  # CPC scaling factor - controls how quickly CPC increases with spend (increased for stronger diminishing returns)
    cpc_ref_spend=1000.0,  # Reference spend level for CPC calculations
    # SEO (Search Engine Optimization) parameters
    # Competitors typically have Ahrefs Domain Rating (DR) of 40-70
    seo_users_per_eur=0.25,  # Users generated per EUR spent on SEO content/links

    domain_rating_init=1,
    domain_rating_max=100.0,  # Maximum achievable domain rating (theoretical ceiling)
    domain_rating_spend_sensitivity=0.07,  # ? How exactly calculated ? Growth coefficient for DR improvement from SEO spend
    domain_rating_reference_spend_eur=1500.0,  # Reference monthly SEO spend for DR growth calculations
    domain_rating_decay=0.01,  # Natural monthly decay of domain rating without maintenance
    # Conversion funnel rates (typical B2B SaaS benchmarks)
    conv_web_to_lead=0.01,  # 1% of website visitors become leads (more conservative)
    conv_website_lead_to_free=0.4,
    conv_website_lead_to_pro=0.15,
    conv_website_lead_to_ent=0.05,
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
    ),
    tax_rate=0.25,  # Corporate tax rate (25% - typical for many European countries)
    market_cap_multiple=8.0,  # Revenue multiple for valuation (8x TTM revenue - realistic for growing SaaS)
    # Sales costs (one-time cost per new customer acquisition)
    # There must e differentation between the direct and the organic/website
    sales_cost_per_new_pro=500.0,  # 500 EUR cost to acquire new pro customer (includes sales team, demos, etc.)
    sales_cost_per_new_ent=500.0,  # 500 EUR cost for enterprise (seems low, should be higher - see note)
    # Support costs (monthly cost per active customer)
    support_cost_per_pro=30.0,  # 30 EUR/month per pro customer (360 EUR/year)
    support_cost_per_ent=100.0,
    # Optional support subscription (premium support add-on)
    support_subscription_fee_pct_pro=0.01,  # per MONTH! so 5000 -> 50 * 12 -> 600
    support_subscription_fee_pct_ent=0.01,  # per MONTH! so 20000 -> 200 * 12 -> 2400
    support_subscription_take_rate_pro=0.70,  # 70% of pro customers purchase support subscription
    support_subscription_take_rate_ent=0.90,  # 90% of enterprise customers purchase support subscription
    # Partner program parameters
    partner_spend_ref=200.0,  # Reference monthly spend to calculate partner acquisition efficiency
    partner_product_value_ref=1000.0,  # Reference product value for partner acquisition formula
    partner_commission_rate=0.20,  # 20% commission on partner-generated deals (industry standard: 15-30%)
    partner_churn_per_month=0.02,  # 2% monthly partner churn (equivalent to ~22% annual)
    partner_pro_deals_per_partner_per_month=1,  # Average 0.5 pro deals per partner per month
    partner_ent_deals_per_partner_per_month=0.5,  # Average 0.5 enterprise deals per partner per month
    # Operating costs (monthly EUR)
    operating_baseline=1000.0,  # Fixed baseline costs (tools, software, basic infrastructure)
    operating_per_user=5.0,  # Variable cost per active user (hosting, bandwidth, etc.)
    operating_per_dev=0.2,  # Additional cost per dev spend (dev tools, cloud services for development)
    # Lead generation via scraping/outreach
    qualified_pool_total=20_000.0,  # Total addressable prospects in the market (reduced from 5,000 for more realism)
    scraping_efficiency_k=0.2,  # Efficiency factor for scraping (reduced from 0.8 for stronger diminishing returns)
    scraping_ref_spend=2000.0,  # Reference monthly spend for scraping calculations
    cost_per_direct_lead=5.0,
    cost_per_direct_demo=200.0,
    # Debt financing parameters
    debt_interest_rate_base_annual=0.08,  # Base annual interest rate 8%
    credit_draw_factor=1.0,
    debt_repay_factor=0.5,
    # Product value dynamics (dev spend accumulation with depreciation)
    pv_init=100_000.0,  # Initial product value (starting milestone)
    pv_min=0.0,  # Minimum product value floor
    product_value_depreciation_rate=0.02,  # 2% monthly depreciation
    milestone_achieved_renewal_percentage=0.50,  # 50% of licenses renew on new milestone
    product_renewal_discount_percentage=0.50,  # 50% discount on renewal price
    # Cost Category Assumptions
    payment_processing_rate=0.02,  # Payment processing fee rate (2% of revenue)
    dev_capex_ratio=0.3,  # Portion of dev spend that is capitalized as CAPEX (30%)
)
