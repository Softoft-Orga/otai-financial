"""Centralized configuration for default assumptions."""

from __future__ import annotations

from .models import Assumptions

# Default assumptions used across the application
DEFAULT_ASSUMPTIONS = Assumptions(
    months=36,  # 3-year simulation horizon typical for SaaS financial planning
    starting_cash=25000.0,  # Initial seed capital - THIS IS DEFINITIVE
    base_organic_users_per_month=50.0,  # Reduced baseline organic traffic
    cpc_eur=3.0,  # Legacy fallback - not used in current model (kept for compatibility)
    # CPC (Cost Per Click) parameters - realistic range for B2B SaaS is 1.5-7 EUR
    cpc_base=2,  # Base CPC at low spend levels (best case scenario)
    cpc_sensitivity_factor=0.5,  # CPC scaling factor - controls how quickly CPC increases with spend (increased for stronger diminishing returns)
    cpc_ref_spend=1000.0,  # Reference spend level for CPC calculations
    # SEO (Search Engine Optimization) parameters
    # Competitors typically have Ahrefs Domain Rating (DR) of 40-70
    seo_users_per_eur=0.25,  # Users generated per EUR spent on SEO content/links
    seo_decay=0.0,  # Monthly decay of SEO stock (0 = no decay, 0.01 = 1% decay per month)
    domain_rating_init=10.0,  # Starting domain rating (our real DR is ~2, but 10 is more optimistic for simulation)
    domain_rating_max=100.0,  # Maximum achievable domain rating (theoretical ceiling)
    domain_rating_spend_sensitivity=0.07,  # Growth coefficient for DR improvement from SEO spend
    domain_rating_reference_spend_eur=1500.0,  # Reference monthly SEO spend for DR growth calculations
    domain_rating_decay=0.01,  # Natural monthly decay of domain rating without maintenance
    # Conversion funnel rates (typical B2B SaaS benchmarks)
    conv_web_to_lead=0.01,  # 1% of website visitors become leads (more conservative)
    conv_website_lead_to_free=0.08,  # Reduced from 15%
    conv_website_lead_to_pro=0.005,  # Reduced from 1%
    conv_website_lead_to_ent=0.0005,  # Reduced from 0.1%
    conv_outreach_lead_to_free=0.01,  # Reduced from 5%
    conv_outreach_lead_to_pro=0.0015,  # Reduced from 3%
    conv_outreach_lead_to_ent=0.0001,  # Reduced from 0.5%
    conv_free_to_pro=0.01,  # 2% of free users upgrade to paid (reduced from 5%)
    conv_pro_to_ent=0.005,  # 0.5% of pro users upgrade to enterprise (reduced from 1%)
    # Monthly customer churn rates (industry benchmarks)
    churn_free=0.25,  # 25% monthly churn for free users (equivalent to ~94% annual - high but realistic for freemium)
    churn_pro=0.04,  # 4% monthly churn for pro users (equivalent to ~39% annual - typical for SMB SaaS)
    churn_ent=0.015,  # 1.5% monthly churn for enterprise (equivalent to ~17% annual - low due to contracts)
    churn_pro_floor=0.02,  # Minimum churn rate for pro users regardless of product value
    # Pricing (one-time license fees in EUR)
    # Note: In this model prices are dynamic based on product value to simulate dev spend impact
    # In reality, prices would be stable and dev spend would affect conversion rates instead
    pro_price_base=5000.0,  # Base price for pro plan (5K EUR one-time license)
    ent_price_base=20000.0,  # Base price for enterprise plan (20K EUR one-time license)
    pro_price_k=0.001,  # Price scaling factor for pro plan based on product value
    ent_price_k=0.0005,  # Price scaling factor for enterprise plan based on product value
    tax_rate=0.25,  # Corporate tax rate (25% - typical for many European countries)
    market_cap_multiple=8.0,  # Revenue multiple for valuation (8x TTM revenue - realistic for growing SaaS)
    # Sales costs (one-time cost per new customer acquisition)
    sales_cost_per_new_pro=500.0,  # 500 EUR cost to acquire new pro customer (includes sales team, demos, etc.)
    sales_cost_per_new_ent=500.0,  # 500 EUR cost for enterprise (seems low, should be higher - see note)
    # Support costs (monthly cost per active customer)
    support_cost_per_pro=30.0,  # 30 EUR/month per pro customer (360 EUR/year)
    support_cost_per_ent=100.0,
    # Optional support subscription (premium support add-on)
    support_subscription_fee_pct_pro=0.01,  # per MONTH!?
    support_subscription_fee_pct_ent=0.01,  # per MONTH!?
    support_subscription_take_rate_pro=0.70,  # 70% of pro customers purchase support subscription
    support_subscription_take_rate_ent=0.90,  # 90% of enterprise customers purchase support subscription
    # Partner program parameters
    partner_spend_ref=200.0,  # Reference monthly spend to calculate partner acquisition efficiency
    partner_product_value_ref=1000.0,  # Reference product value for partner acquisition formula
    partner_commission_rate=0.20,  # 20% commission on partner-generated deals (industry standard: 15-30%)
    partner_churn_per_month=0.02,  # 2% monthly partner churn (equivalent to ~22% annual)
    partner_pro_deals_per_partner_per_month=0.5,  # Average 0.5 pro deals per partner per month
    partner_ent_deals_per_partner_per_month=0.1,  # Average 0.5 enterprise deals per partner per month
    # Operating costs (monthly EUR)
    operating_baseline=1000.0,  # Fixed baseline costs (tools, software, basic infrastructure)
    operating_per_user=5.0,  # Variable cost per active user (hosting, bandwidth, etc.)
    operating_per_dev=0.2,  # Additional cost per dev spend (dev tools, cloud services for development)
    # Lead generation via scraping/outreach
    qualified_pool_total=20_000.0,  # Total addressable prospects in the market (reduced from 5,000 for more realism)
    scraping_efficiency_k=0.2,  # Efficiency factor for scraping (reduced from 0.8 for stronger diminishing returns)
    scraping_ref_spend=2000.0,  # Reference monthly spend for scraping calculations
    # Debt financing parameters
    credit_cash_threshold=20_000.0,  # Cash level below which credit is automatically drawn
    credit_draw_amount=50_000.0,  # Fixed amount drawn when credit is triggered
    debt_repay_cash_threshold=100_000.0,  # Cash level above which debt is automatically repaid
    debt_repay_amount=50_000.0,  # Fixed amount to repay when triggered
    debt_interest_rate_base_annual=0.12,  # Base annual interest rate (12% - typical for venture debt)
    debt_interest_rate_k=0.04,  # Interest rate scaling factor based on debt level
    debt_interest_rate_ref=100_000.0,  # Reference debt level for interest rate calculations
    # Product value dynamics (affects conversions, pricing, and churn)
    pv_init=100.0,  # Initial product value (normalized to 100)
    pv_min=40.0,  # Minimum product value (40% of initial - product degradation floor)
    pv_ref=1000.0,  # Reference product value for calculations
    product_value_decay_shape=0.06,  # Natural monthly decay without dev spend (6% at pv_ref)
    dev_spend_growth_efficiency=0.02,  # Growth efficiency from dev spend (18% at pv_ref)
    monthly_renewal_fee_product_divisor=10_000.0,
    # Product value impact coefficients (how strongly product value affects various metrics)
    product_value_impact_on_web_conversions=0.10,  # 10% max improvement in web-to-lead conversion from product value (reduced from 30%)
    product_value_impact_on_lead_to_free=0.05,  # 5% max improvement in lead-to-free conversion (reduced from 15%)
    product_value_impact_on_free_to_pro=0.10,  # 10% max improvement in free-to-pro conversion (reduced from 25%)
    product_value_impact_on_pro_to_ent=0.08,  # 8% max improvement in pro-to-enterprise conversion (reduced from 20%)
    product_value_impact_on_pro_churn=0.10,  # 10% max reduction in pro churn from product value (reduced from 20%)
    product_value_impact_on_free_churn=0.05,  # 5% max reduction in free churn (reduced from 10%)
    product_value_impact_on_ent_churn=0.08,  # 8% max reduction in enterprise churn (reduced from 15%)
    # Cost Category Assumptions
    payment_processing_rate=0.02,  # Payment processing fee rate (2% of revenue)
    cost_per_outreach_conversion_free=5.0,  # Cost to convert outreach lead to free user
    cost_per_outreach_conversion_pro=1000.0,  # Cost to convert outreach lead to pro user
    cost_per_outreach_conversion_ent=1000.0,  # Cost to convert outreach lead to enterprise user
    dev_capex_ratio=0.3,  # Portion of dev spend that is capitalized as CAPEX (30%)
)
