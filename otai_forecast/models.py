from __future__ import annotations

import math
from dataclasses import dataclass, field

Month = int


@dataclass(frozen=True)
class Assumptions:
    """Core assumptions for the financial forecasting simulation.

    All parameters are validated in __post_init__. These parameters control
    how the simulation evolves month by month, including user acquisition,
    conversion rates, pricing, costs, and financial dynamics.
    """

    # Simulation Time
    months: int
    """Number of months to simulate. Must be > 0.

    Effect: Linear - determines the length of the simulation timeline.
    """

    # Initial Financial State
    starting_cash: float
    """Initial cash on hand at month 0. Must be >= 0.

    Effect: Linear - directly adds to cash balance at start.
    """

    # Organic User Acquisition
    base_organic_users_per_month: float
    """Baseline organic users acquired per month without any SEO. Must be >= 0.

    Effect: Linear - constant flow of users independent of SEO efforts.
    """

    # CPC (Cost Per Click) Model - Dynamic with diminishing returns
    cpc_eur: float  # fallback; dynamic CPC will be used if cpc_base/cpc_k/cpc_ref_spend are set
    """Fixed fallback CPC in euros. Must be >= 0.

    Effect: Linear - if used, ads_clicks = ads_spend / cpc_eur.
    Only used if dynamic CPC parameters are not set.
    """

    cpc_base: float
    """Base CPC at zero ad spend. Must be >= 0.

    Effect: Logarithmic - minimum CPC even with no spend.
    Formula: effective_cpc = cpc_base + cpc_k * log(1 + ads_spend / cpc_ref_spend)
    """

    cpc_sensitivity_factor: float
    """CPC scaling factor for ad spend. Must be >= 0.

    Effect: Logarithmic - controls how quickly CPC increases with spend.
    Higher values = faster increase (worse efficiency at scale).
    """

    cpc_ref_spend: float
    """Reference ad spend for CPC calculation. Must be > 0.

    Effect: Logarithmic scale parameter for CPC curve.
    """

    # SEO Model - Accumulating stock with decay
    seo_users_per_eur: float
    """SEO efficiency: users generated per euro spent. Must be >= 0.

    Effect: Linear on spend, but subject to decay.
    New SEO users = seo_spend * seo_users_per_eur.
    """

    seo_decay: float
    """Monthly decay rate for SEO stock (0-1). Must be in [0, 1].

    Effect: Exponential decay - fraction of SEO stock lost each month.
    0 = no decay, 0.1 = 10% monthly decay, 1 = complete decay.
    """

    # Domain Rating - Grows with SEO spend, decays over time
    domain_rating_init: float
    """Initial domain rating at month 0. Must be >= 0 and <= domain_rating_max.

    Effect: Linear multiplier - affects organic traffic and SEO effectiveness.
    """

    domain_rating_max: float
    """Maximum possible domain rating. Must be > 0.

    Effect: Asymptotic limit - domain rating approaches but never exceeds this.
    """

    domain_rating_spend_sensitivity: float
    """Domain rating growth coefficient. Must be >= 0.

    Effect: Logarithmic - controls growth rate from SEO spend.
    Higher values = faster growth but with diminishing returns.
    """

    domain_rating_reference_spend_eur: float
    """Reference SEO spend for domain rating growth. Must be > 0.

    Effect: Logarithmic scale parameter for domain rating growth.
    """

    domain_rating_decay: float
    """Monthly domain rating decay (0-1). Must be in [0, 1].

    Effect: Linear decay - points lost each month regardless of SEO.
    """

    # Conversion Funnel - Base rates affected by product value
    conv_web_to_lead: float
    """Base conversion rate: website visitors to leads. Must be in [0, 1].

    Effect: Linear - fraction of website users who become leads.
    Modified by product_value via k_pv_web_to_lead.
    """

    conv_website_lead_to_free: float
    conv_website_lead_to_pro: float
    conv_website_lead_to_ent: float

    conv_outreach_lead_to_free: float
    conv_outreach_lead_to_pro: float
    conv_outreach_lead_to_ent: float

    conv_free_to_pro: float
    """Base conversion rate: free to paid pro users. Must be in [0, 1].

    Effect: Linear - fraction of free users upgrading to pro.
    Modified by product_value via k_pv_free_to_pro.
    """

    conv_pro_to_ent: float
    """Base conversion rate: pro to enterprise users. Must be in [0, 1].

    Effect: Linear - fraction of pro users upgrading to enterprise.
    Modified by product_value via k_pv_pro_to_ent.
    """

    # Churn Rates - Base rates affected by product value
    churn_free: float
    """Base monthly churn rate for free users (0-1). Must be in [0, 1].

    Effect: Linear - fraction of free users lost each month.
    Modified by product_value via k_pv_churn_free.
    """

    churn_pro: float
    """Base monthly churn rate for pro users (0-1). Must be in [0, 1].

    Effect: Linear - fraction of pro users lost each month.
    Modified by product_value via k_pv_churn_pro.
    """

    churn_ent: float
    """Base monthly churn rate for enterprise users (0-1). Must be in [0, 1].

    Effect: Linear - fraction of enterprise users lost each month.
    Modified by product_value via k_pv_churn_ent.
    """

    churn_pro_floor: float
    """Minimum churn rate for pro users (0-1). Must be in [0, 1] and <= churn_pro.

    Effect: Linear lower bound - pro churn cannot go below this even with perfect product.
    """

    # Pricing Model - Base prices with scaling
    pro_price_base: float
    """Base monthly price for pro tier at reference product value. Must be >= 0.

    Effect: Linear - scaled by product_value_ratio ^ pro_price_k.
    """

    ent_price_base: float
    """Base monthly price for enterprise tier at reference product value. Must be >= 0.

    Effect: Linear - scaled by product_value_ratio ^ ent_price_k.
    """

    pro_price_k: float
    """Pro price elasticity to product value. Must be >= 0.

    Effect: Power law - how much pro price scales with product value.
    0 = no scaling, 1 = linear scaling, >1 = superlinear.
    """

    ent_price_k: float
    """Enterprise price elasticity to product value. Must be >= 0.

    Effect: Power law - how much enterprise price scales with product value.
    """

    # Financial Parameters
    tax_rate: float
    """Corporate tax rate on profit (0-1). Must be in [0, 1].

    Effect: Linear - fraction of pre-tax profit paid as tax.
    """

    market_cap_multiple: float
    """Valuation multiple applied to TTM revenue. Must be >= 0.

    Effect: Linear multiplier - final valuation = TTM_revenue * multiple.
    """

    # Sales & Support Costs
    sales_cost_per_new_pro: float
    """Sales cost for each new pro customer. Must be >= 0.

    Effect: Linear - cost incurred for each pro conversion.
    """

    sales_cost_per_new_ent: float
    """Sales cost for each new enterprise customer. Must be >= 0.

    Effect: Linear - cost incurred for each enterprise conversion.
    """

    support_cost_per_pro: float
    """Monthly support cost per pro user. Must be >= 0.

    Effect: Linear - ongoing cost for each active pro user.
    """

    support_cost_per_ent: float
    """Monthly support cost per enterprise user. Must be >= 0.

    Effect: Linear - ongoing cost for each active enterprise user.
    """

    support_subscription_fee_pct_pro: float
    support_subscription_fee_pct_ent: float
    support_subscription_take_rate_pro: float
    support_subscription_take_rate_ent: float

    partner_spend_ref: float
    partner_product_value_ref: float
    partner_commission_rate: float
    partner_churn_per_month: float
    partner_pro_deals_per_partner_per_month: float
    partner_ent_deals_per_partner_per_month: float

    # Operating Costs
    operating_baseline: float
    """Fixed baseline operating costs per month. Must be >= 0.

    Effect: Linear - constant cost regardless of users or dev spend.
    """

    operating_per_user: float
    """Variable operating cost per user (all tiers). Must be >= 0.

    Effect: Linear - cost scales with total active users.
    """

    operating_per_dev: float
    """Operating cost multiplier per dev spend euro. Must be >= 0.

    Effect: Linear - dev_spend * operating_per_dev added to operating costs.
    Models overhead, infrastructure, and scaling costs.
    """

    # Scraping & Outreach Model
    qualified_pool_total: float
    """Total size of qualified prospects pool. Must be >= 0.

    Effect: Linear upper bound - maximum prospects that can be discovered.
    Fixed pool that depletes as scraping finds prospects.
    """

    scraping_efficiency_k: float
    """Scraping efficiency coefficient. Must be >= 0.

    Effect: Logarithmic - controls diminishing returns of scraping.
    Higher values = more efficient prospect discovery.
    """

    scraping_ref_spend: float
    """Reference scraping spend for efficiency calculation. Must be > 0.

    Effect: Logarithmic scale parameter for scraping efficiency.
    """

    # Debt & Credit Model
    credit_cash_threshold: float
    """Cash level that triggers automatic credit draw. Must be >= 0.

    Effect: Threshold - if cash < threshold and credit_draw_amount > 0, credit is drawn.
    """

    credit_draw_amount: float
    """Amount of credit to draw when threshold is breached. Must be >= 0.

    Effect: Linear - fixed amount added to debt and cash when triggered.
    """

    debt_repay_cash_threshold: float
    """Cash level that triggers automatic debt repayment. Must be >= 0.

    Effect: Threshold - if cash > threshold and debt > 0, repayment is made.
    """

    debt_repay_amount: float
    """Amount of debt to repay when threshold is breached. Must be >= 0.

    Effect: Linear - fixed amount subtracted from debt and cash when triggered.
    """

    debt_interest_rate_base_annual: float
    """Base annual interest rate at zero debt. Must be >= 0.

    Effect: Logarithmic - minimum interest rate even with no debt.
    """

    debt_interest_rate_k: float
    """Interest rate scaling factor for debt level. Must be >= 0.

    Effect: Logarithmic - controls how quickly interest rate increases with debt.
    """

    debt_interest_rate_ref: float
    """Reference debt for interest rate calculation. Must be > 0.

    Effect: Logarithmic scale parameter for interest rate curve.
    """

    # Product Value Model - Accumulates with dev spend, decays without
    pv_init: float
    """Initial product value at month 0. Must be > 0.

    Effect: Normalized reference point - affects conversions, pricing, and churn.
    """

    pv_min: float
    """Minimum product value (decay limit). Must be > 0 and <= pv_init.

    Effect: Asymptotic lower bound - product value cannot decay below this.
    """

    pv_ref: float
    """Reference product value for scaling calculations. Must be > 0.

    Effect: Normalization point - used to calculate pv_norm = product_value / pv_ref.
    """

    product_value_decay_shape: float
    """Shape parameter for product value natural decay. Must be >= 0.

    Effect: Controls how quickly product value degrades without maintenance.
    Higher values = faster decay.
    """

    dev_spend_growth_efficiency: float
    """Scale factor for product value growth from dev spend. Must be >= 0.

    Effect: Logarithmic - controls how efficiently dev spend increases product value.
    Higher values = more efficient growth.
    """

    monthly_renewal_fee_product_divisor: float

    # Product Value Effects - How product value influences other metrics
    product_value_impact_on_web_conversions: float
    """Product value impact on web-to-lead conversion. Must be >= 0.

    Effect: Controls how much product value improves web-to-lead conversions.
    Higher values = stronger impact.
    """

    product_value_impact_on_lead_to_free: float
    """Product value impact on lead-to-free conversion. Must be >= 0.

    Effect: Controls how much product value improves lead-to-free conversions.
    Higher values = stronger impact.
    """

    product_value_impact_on_free_to_pro: float
    """Product value impact on free-to-pro conversion. Must be >= 0.

    Effect: Controls how much product value improves free-to-pro conversions.
    Higher values = stronger impact.
    """

    product_value_impact_on_pro_to_ent: float
    """Product value impact on pro-to-enterprise conversion. Must be >= 0.

    Effect: Controls how much product value improves pro-to-enterprise conversions.
    Higher values = stronger impact.
    """

    product_value_impact_on_pro_churn: float
    """Product value impact on pro churn reduction. Must be >= 0.

    Effect: Controls how much product value reduces pro customer churn.
    Higher values = stronger reduction.
    """

    product_value_impact_on_free_churn: float
    """Product value impact on free churn reduction. Must be >= 0.

    Effect: Controls how much product value reduces free customer churn.
    Higher values = stronger reduction.
    """

    product_value_impact_on_ent_churn: float
    """Product value impact on enterprise churn reduction. Must be >= 0.

    Effect: Controls how much product value reduces enterprise customer churn.
    Higher values = stronger reduction.
    """

    # Cost Category Assumptions
    payment_processing_rate: float
    """Payment processing fee rate as percentage of revenue (0-1).

    Effect: Linear - revenue * payment_processing_rate = payment fees.
    Part of COGS (Cost of Goods Sold).
    """

    # Direct conversion costs (COGS)
    cost_per_outreach_conversion_free: float
    """Cost to convert one outreach lead to free user. Must be >= 0.

    Effect: Linear - new_free_from_outreach * cost = COGS.
    Direct cost of conversion effort per successful free signup.
    """

    cost_per_outreach_conversion_pro: float
    """Cost to convert one outreach lead to pro user. Must be >= 0.

    Effect: Linear - new_pro_from_outreach * cost = COGS.
    Direct cost of sales effort per successful pro conversion.
    """

    cost_per_outreach_conversion_ent: float
    """Cost to convert one outreach lead to enterprise user. Must be >= 0.

    Effect: Linear - new_ent_from_outreach * cost = COGS.
    Direct cost of enterprise sales effort per successful enterprise conversion.
    """

    dev_capex_ratio: float
    """Portion of dev spend that is capitalized as CAPEX (0-1).

    Effect: Linear - dev_spend * dev_capex_ratio = CAPEX.
    Remaining dev_spend is treated as R&D operating expense.
    """

    def __post_init__(self):
        if self.months <= 0:
            raise ValueError("months must be > 0")

        if self.cpc_eur < 0:
            raise ValueError("cpc_eur must be >= 0")
        if self.cpc_base < 0:
            raise ValueError("cpc_base must be >= 0")
        if self.cpc_k < 0:
            raise ValueError("cpc_k must be >= 0")
        if self.cpc_ref_spend <= 0:
            raise ValueError("cpc_ref_spend must be > 0")
        if self.seo_eff_users_per_eur < 0:
            raise ValueError("seo_eff_users_per_eur must be >= 0")
        if not (0.0 <= self.seo_decay <= 1.0):
            raise ValueError("seo_decay must be in [0, 1]")

        if self.domain_rating_init < 0:
            raise ValueError("domain_rating_init must be >= 0")
        if self.domain_rating_max <= 0:
            raise ValueError("domain_rating_max must be > 0")
        if self.domain_rating_init > self.domain_rating_max:
            raise ValueError("domain_rating_init must be <= domain_rating_max")
        if self.domain_rating_growth_k < 0:
            raise ValueError("domain_rating_growth_k must be >= 0")
        if self.domain_rating_growth_ref_spend <= 0:
            raise ValueError("domain_rating_growth_ref_spend must be > 0")
        if not (0.0 <= self.domain_rating_decay <= 1.0):
            raise ValueError("domain_rating_decay must be in [0, 1]")

        for name, v in (
            ("conv_web_to_lead", self.conv_web_to_lead),
            ("conv_website_lead_to_free", self.conv_website_lead_to_free),
            ("conv_website_lead_to_pro", self.conv_website_lead_to_pro),
            ("conv_website_lead_to_ent", self.conv_website_lead_to_ent),
            ("conv_outreach_lead_to_free", self.conv_outreach_lead_to_free),
            ("conv_outreach_lead_to_pro", self.conv_outreach_lead_to_pro),
            ("conv_outreach_lead_to_ent", self.conv_outreach_lead_to_ent),
            ("conv_free_to_pro", self.conv_free_to_pro),
            ("conv_pro_to_ent", self.conv_pro_to_ent),
            ("churn_free", self.churn_free),
            ("churn_pro", self.churn_pro),
            ("churn_ent", self.churn_ent),
        ):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"{name} must be in [0, 1]")

        if not (0.0 <= self.tax_rate <= 1.0):
            raise ValueError("tax_rate must be in [0, 1]")

        if self.market_cap_multiple < 0:
            raise ValueError("market_cap_multiple must be >= 0")

        if self.sales_cost_per_new_pro < 0:
            raise ValueError("sales_cost_per_new_pro must be >= 0")
        if self.sales_cost_per_new_ent < 0:
            raise ValueError("sales_cost_per_new_ent must be >= 0")
        if self.support_cost_per_pro < 0:
            raise ValueError("support_cost_per_pro must be >= 0")
        if self.support_cost_per_ent < 0:
            raise ValueError("support_cost_per_ent must be >= 0")

        for name, v in (
            ("support_subscription_fee_pct_pro", self.support_subscription_fee_pct_pro),
            ("support_subscription_fee_pct_ent", self.support_subscription_fee_pct_ent),
            (
                "support_subscription_take_rate_pro",
                self.support_subscription_take_rate_pro,
            ),
            (
                "support_subscription_take_rate_ent",
                self.support_subscription_take_rate_ent,
            ),
        ):
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"{name} must be in [0, 1]")

        if self.partner_spend_ref <= 0:
            raise ValueError("partner_spend_ref must be > 0")
        if self.partner_product_value_ref <= 0:
            raise ValueError("partner_product_value_ref must be > 0")
        if not (0.0 <= self.partner_commission_rate <= 1.0):
            raise ValueError("partner_commission_rate must be in [0, 1]")
        if not (0.0 <= self.partner_churn_per_month <= 1.0):
            raise ValueError("partner_churn_per_month must be in [0, 1]")
        if self.partner_pro_deals_per_partner_per_month < 0:
            raise ValueError("partner_pro_deals_per_partner_per_month must be >= 0")
        if self.partner_ent_deals_per_partner_per_month < 0:
            raise ValueError("partner_ent_deals_per_partner_per_month must be >= 0")

        if self.operating_baseline < 0:
            raise ValueError("operating_baseline must be >= 0")
        if self.operating_per_user < 0:
            raise ValueError("operating_per_user must be >= 0")
        if self.operating_per_dev < 0:
            raise ValueError("operating_per_dev must be >= 0")

        if self.churn_pro_floor < 0 or self.churn_pro_floor > 1:
            raise ValueError("churn_pro_floor must be in [0, 1]")
        if self.churn_pro_floor > self.churn_pro:
            raise ValueError("churn_pro_floor must be <= churn_pro")

        if self.qualified_pool_total < 0:
            raise ValueError("qualified_pool_total must be >= 0")
        if self.scraping_efficiency_k < 0:
            raise ValueError("scraping_efficiency_k must be >= 0")
        if self.scraping_ref_spend <= 0:
            raise ValueError("scraping_ref_spend must be > 0")

        if self.credit_cash_threshold < 0:
            raise ValueError("credit_cash_threshold must be >= 0")
        if self.credit_draw_amount < 0:
            raise ValueError("credit_draw_amount must be >= 0")
        if self.debt_repay_cash_threshold < 0:
            raise ValueError("debt_repay_cash_threshold must be >= 0")
        if self.debt_repay_amount < 0:
            raise ValueError("debt_repay_amount must be >= 0")
        if self.debt_interest_rate_base_annual < 0:
            raise ValueError("debt_interest_rate_base_annual must be >= 0")
        if self.debt_interest_rate_k < 0:
            raise ValueError("debt_interest_rate_k must be >= 0")
        if self.debt_interest_rate_ref <= 0:
            raise ValueError("debt_interest_rate_ref must be > 0")

        if self.pv_init <= 0 or self.pv_ref <= 0:
            raise ValueError("pv_init and pv_ref must be > 0")
        if self.pv_min <= 0:
            raise ValueError("pv_min must be > 0")
        if self.pv_min > self.pv_init:
            raise ValueError("pv_min must be <= pv_init")
        if self.pv_growth_scale < 0:
            raise ValueError("pv_growth_scale must be >= 0")
        if self.pv_decay_shape < 0:
            raise ValueError("pv_decay_shape must be >= 0")

        if self.monthly_renewal_fee_product_divisor <= 0:
            raise ValueError("product_value_divisor must be > 0")


@dataclass(frozen=True)
class MonthlyDecision:
    """Monthly decision variables that control the simulation.

    These are the levers you can pull each month to influence growth,
    costs, and financial outcomes. All spend values are in euros.
    """

    # Marketing & Growth Spend
    ads_budget: float
    """Monthly advertising spend (e.g., Google Ads, Facebook). Must be >= 0.

    Effect: Generates clicks via dynamic CPC model.
    Higher spend increases CPC (diminishing returns).
    """

    seo_budget: float
    """Monthly organic marketing investment (SEO, content, etc.). Must be >= 0.

    Effect: Increases domain_rating and adds to seo_stock_users.
    Has logarithmic diminishing returns on domain rating.
    """

    # Product Development
    dev_budget: float
    """Monthly product development spend. Must be >= 0.

    Effect: Increases product_value if above maintenance threshold.
    Below maintenance, product_value decays.
    Also increases operating costs via operating_per_dev.
    """

    # Sales & Outreach
    outreach_budget: float
    """Monthly spend on prospect scraping tools/services. Must be >= 0.

    Effect: Discovers prospects from qualified_pool_total.
    Has logarithmic diminishing returns.
    """

    partner_budget: float

    def __post_init__(self):
        for name, v in (
            ("ads_budget", self.ads_budget),
            ("seo_budget", self.seo_budget),
            ("dev_budget", self.dev_budget),
            ("outreach_budget", self.outreach_budget),
            ("partner_budget", self.partner_budget),
        ):
            if v < 0:
                raise ValueError(f"{name} must be >= 0")


type MonthlyDecisions = list["MonthlyDecision"]


@dataclass
class State:
    """Current state of the simulation at a given month.

    This represents the cumulative effects of all previous decisions and
    assumptions. State evolves month by month based on MonthlyCalculated values.
    """

    # Time
    month: Month = field()
    """Current month number (0-indexed). Must be >= 0.

    Effect: Tracks simulation progress.
    """

    # Financial Position
    cash: float = field()
    """Current cash on hand. Can be negative if credit is used.

    Effect: Determines if credit is drawn (if < credit_cash_threshold).
    Updated each month by net_cashflow.
    """

    debt: float = field()
    """Total debt accumulated. Must be >= 0.

    Effect: Increases interest payments via debt_interest_rate model.
    Grows when credit is drawn.
    """

    # Marketing Assets
    domain_rating: float = field()
    """Current domain rating (0 to domain_rating_max). Must be >= 0.

    Effect: Multiplies organic traffic and SEO effectiveness.
    Grows with seo_spend, decays each month.
    """

    product_value: float = field()
    """Current product value index. Must be > 0.

    Effect: Improves conversion rates and pricing, reduces churn.
    Grows with dev_spend, decays without maintenance.
    """

    # User Base
    free_active: float = field()
    """Current active free tier users. Must be >= 0.

    Effect: Contributes to operating costs and can upgrade to paid tiers.
    Updated: new_free - churned_free.
    """

    pro_active: float = field()
    """Current active pro tier users. Must be >= 0.

    Effect: Generates revenue, incurs support and sales costs.
    Updated: new_pro - churned_pro.
    """

    ent_active: float = field()
    """Current active enterprise users. Must be >= 0.

    Effect: Generates high-value revenue, incurs support and sales costs.
    Updated: new_ent - churned_ent.
    """

    partners_active: float = field()

    qualified_pool_remaining: float = field()
    """Remaining prospects in the market that haven't been scraped yet. Must be >= 0.

    Effect: Limits the total leads that can be generated via scraping/outreach.
    Decreases as prospects are found and contacted.
    """

    def __post_init__(self):
        if self.month < 0:
            raise ValueError("month must be >= 0")
        if self.debt < 0:
            raise ValueError("debt must be >= 0")
        if self.domain_rating < 0:
            raise ValueError("domain_rating must be >= 0")
        if self.product_value <= 0:
            raise ValueError("product_value must be > 0")
        if self.free_active < 0 or self.pro_active < 0 or self.ent_active < 0:
            raise ValueError("active user counts must be >= 0")
        if self.partners_active < 0:
            raise ValueError("partners_active must be >= 0")
        if self.qualified_pool_remaining < 0:
            raise ValueError("qualified_pool_remaining must be >= 0")


@dataclass(frozen=True)
class MonthlyCalculated:
    """All calculated values for a single month.

    These are the outputs of the simulation for each month, calculated
    from the current State, Assumptions, and MonthlyDecision.
    """

    month: Month
    """Month number for these calculations (0-indexed)."""

    # Product Value & Pricing
    product_value_next: float
    """Product value for next month. Must be > 0.

    Effect: Becomes the new product_value in next State.
    Calculated based on dev_spend vs maintenance needs.
    """

    pv_norm: float
    """Normalized product value (product_value / pv_ref).

    Effect: Used to scale conversion rates, pricing, and churn.
    """

    pro_price: float
    """Effective pro tier price for this month.

    Effect: Determines revenue_per_pro_user.
    Calculated from base_price * (pv_norm ^ pro_price_k) or override.
    """

    ent_price: float
    """Effective enterprise tier price for this month.

    Effect: Determines revenue_per_ent_user.
    """

    renewal_fee_percentage: float
    monthly_renewal_fee: float

    pro_support_subscribers: float
    ent_support_subscribers: float

    support_subscription_revenue_pro: float
    support_subscription_revenue_ent: float
    support_subscription_revenue_total: float

    new_partners: float
    churned_partners: float
    partner_pro_deals: float
    partner_ent_deals: float
    partner_commission_cost: float

    # Effective Conversion Rates (after product value effects)
    conv_web_to_lead_eff: float
    """Effective web-to-lead conversion rate.

    Effect: website_leads = website_users * conv_eff.
    Modified by product_value: conv_base * (pv_norm ^ k_pv).
    """

    conv_website_lead_to_free_eff: float
    """Effective website lead-to-free conversion rate.

    Effect: new_free = leads_total * conv_eff.
    """

    conv_website_lead_to_pro_eff: float
    """Effective website lead-to-pro conversion rate.

    Effect: new_pro = free_active * conv_eff.
    """

    conv_website_lead_to_ent_eff: float
    """Effective website lead-to-enterprise conversion rate.

    Effect: new_ent = pro_active * conv_eff.
    """

    conv_outreach_lead_to_free_eff: float
    """Effective outreach lead-to-free conversion rate.

    Effect: new_free = leads_total * conv_eff.
    """

    conv_outreach_lead_to_pro_eff: float
    """Effective outreach lead-to-pro conversion rate.

    Effect: new_pro = free_active * conv_eff.
    """

    conv_outreach_lead_to_ent_eff: float
    """Effective outreach lead-to-enterprise conversion rate.

    Effect: new_ent = pro_active * conv_eff.
    """

    upgrade_free_to_pro_eff: float
    """Effective free-to-pro conversion rate.

    Effect: new_pro = free_active * conv_eff.
    """

    upgrade_pro_to_ent_eff: float
    """Effective pro-to-enterprise conversion rate.

    Effect: new_ent = pro_active * conv_eff.
    """

    # Effective Churn Rates (after product value effects)
    churn_free_eff: float
    """Effective free user churn rate.

    Effect: churned_free = free_active * churn_eff.
    Modified by product_value: churn_base / (pv_norm ^ k_pv).
    """

    churn_pro_eff: float
    """Effective pro user churn rate.

    Effect: churned_pro = pro_active * churn_eff.
    Bounded below by churn_pro_floor.
    """

    churn_ent_eff: float
    """Effective enterprise churn rate.

    Effect: churned_ent = ent_active * churn_eff.
    """

    # Traffic & Acquisition Metrics
    ads_clicks: float
    """Number of clicks from ad spend.

    Effect: Adds to website_users.
    Calculated: ads_spend / effective_cpc.
    """

    domain_rating_next: float
    """Domain rating for next month.

    Effect: Becomes the new domain_rating in next State.
    Grows with seo_spend, decays by domain_rating_decay.
    """

    qualified_pool_remaining_next: float
    """Remaining prospects in the market for next month.

    Effect: Becomes the new qualified_pool_remaining in next State.
    Decreases as prospects are scraped and contacted.
    """

    website_users: float
    """Total website visitors this month.

    Effect: Source of leads via conv_web_to_lead_eff.
    Sum of organic, SEO, and ad-driven traffic.
    """

    website_leads: float
    """Leads generated from website traffic.

    Effect: Part of leads_total for conversion to free users.
    """

    # Scraping & Outreach Funnel
    scraped_found: float
    """New prospects discovered via scraping.

    Effect: Pool for outreach_leads.
    Has logarithmic diminishing returns with direct_candidate_outreach_spend.
    """

    outreach_leads: float
    """Leads generated from outreach to scraped prospects.

    Effect: Part of leads_total.
    Calculated: scraped_found.
    """

    direct_leads: float
    """Direct outreach leads (same as outreach_leads).

    Effect: Alternative name for outreach_leads.
    """

    leads_total: float
    """Total leads from all sources.

    Effect: Source of lead-to-user conversions.
    Sum of website_leads and outreach_leads.
    """

    # User Acquisition & Churn
    new_free: float
    """New free users acquired this month.

    Effect: Adds to free_active in next State.
    """

    new_pro: float
    """New pro users acquired this month.

    Effect: Adds to pro_active in next State.
    """

    new_ent: float
    """New enterprise users acquired this month.

    Effect: Adds to ent_active in next State.
    """

    # Next period user counts (after all calculations)
    free_next: float
    """Free users count for next period (after churn and upgrades).

    Effect: For analysis and consistency.
    """
    pro_next: float
    """Pro users count for next period (after churn and upgrades).

    Effect: Used for revenue calculations.
    """
    ent_next: float
    """Enterprise users count for next period (after churn and upgrades).

    Effect: Used for revenue calculations.
    """

    upgraded_to_pro: float
    upgraded_to_ent: float

    churned_free: float
    """Free users lost this month.

    Effect: Subtracts from free_active in next State.
    """

    churned_pro: float
    """Pro users lost this month.

    Effect: Subtracts from pro_active in next State.
    """

    churned_ent: float
    """Enterprise users lost this month.

    Effect: Subtracts from ent_active in next State.
    """

    # Costs
    sales_spend: float
    """Total sales costs this month.

    Effect: Part of costs_ex_tax.
    Calculated: new_pro * sales_cost_per_new_pro + new_ent * sales_cost_per_new_ent.
    """

    support_spend: float
    """Total support costs this month.

    Effect: Part of costs_ex_tax.
    Calculated: pro_active * support_cost_per_pro + ent_active * support_cost_per_ent.
    """

    # Debt & Interest
    interest_rate_annual_eff: float
    """Effective annual interest rate based on current debt.

    Effect: Determines interest_payment.
    Increases with debt level via logarithmic curve.
    """

    interest_payment: float
    """Monthly interest payment on debt.

    Effect: Part of costs_ex_tax.
    Calculated: debt * interest_rate_annual_eff / 12.
    """

    # Financial Results
    revenue_pro: float
    """Revenue from new pro tier customers (one-time licenses).

    Effect: Part of revenue_total.
    Calculated: new_pro * pro_price.
    """

    revenue_ent: float
    """Revenue from new enterprise customers (one-time licenses).

    Effect: Part of revenue_total.
    Calculated: new_ent * ent_price.
    """

    revenue_total: float
    """Total monthly revenue.

    Effect: Used for profit and cash flow calculations.
    Sum of revenue_pro and revenue_ent.
    """

    costs_ex_tax: float
    """Total costs before tax.

    Effect: Subtracted from revenue to calculate profit.
    Includes all operating, sales, support, and interest costs.
    """

    # Cost Categories (Financial Standards)
    cost_of_goods_sold: float
    """Cost of Goods Sold (COGS) - Direct costs to produce/deliver the product.

    Includes hosting/cloud compute, licenses tied to usage, payment processing fees,
    direct subcontractors, and hardware (if sold with product).
    """

    operating_expenses: float
    """Operating Expenses (OPEX) - Costs to run the company.

    Includes R&D (engineering salaries, contractors, tooling),
    Sales & Marketing (ads, events, content, sales tools),
    General & Administrative (accounting, legal, insurance, rent),
    Customer Support (support staff, support tools),
    IT / Internal Tools (SaaS, internal infra).
    """

    capital_expenditure: float
    """Capital Expenditures (CAPEX) - Long-term investments.

    Includes servers, GPUs, office equipment, capitalized software development.
    Currently modeled as part of dev_spend that creates long-term value.
    """

    financial_expenses: float
    """Financial / Non-operating costs.

    Includes interest expenses, FX losses, one-off legal settlements.
    Currently includes interest payments on debt.
    """

    profit_bt: float
    """Profit before tax.

    Effect: Used to calculate tax and net profit.
    Calculated: revenue_total - costs_ex_tax.
    """

    tax: float
    """Tax payment for the month.

    Effect: Part of net_cashflow.
    Calculated: profit_bt * tax_rate (if profit_bt > 0).
    """

    net_cashflow: float
    """Net cash flow for the month (must be finite).

    Effect: Updates cash in next State.
    Calculated: profit_bt - tax - total_spend.
    """

    # Additional fields for enhanced plotting
    spend_last_month: float
    """Total spend in the previous month.

    Effect: Used for cash flow analysis.
    Calculated: Sum of all decision spends from previous month.
    """

    # Detailed revenue breakdowns for plotting
    revenue_pro_website: float
    """Revenue from pro customers acquired via website."""

    revenue_pro_outreach: float
    """Revenue from pro customers acquired via outreach."""

    revenue_pro_partner: float
    """Revenue from pro customers acquired via partners."""

    revenue_ent_website: float
    """Revenue from enterprise customers acquired via website."""

    revenue_ent_outreach: float
    """Revenue from enterprise customers acquired via outreach."""

    revenue_ent_partner: float
    """Revenue from enterprise customers acquired via partners."""

    revenue_renewal_pro: float
    """Revenue from pro customer renewals."""

    revenue_renewal_ent: float
    """Revenue from enterprise customer renewals."""

    revenue_support_pro: float
    """Revenue from pro support subscriptions."""

    revenue_support_ent: float
    """Revenue from enterprise support subscriptions."""

    # Detailed cost breakdowns for plotting
    cost_sales_marketing: float
    """Sales & marketing costs."""

    cost_rd_expense: float
    """R&D expenses."""

    cost_ga: float
    """General & administrative costs."""

    cost_customer_support: float
    """Customer support costs."""

    cost_it_tools: float
    """IT and internal tools costs."""

    cost_payment_processing: float
    """Payment processing fees."""

    cost_outreach_conversion: float
    """Direct outreach conversion costs."""

    cost_partner_commission: float
    """Partner commission costs."""

    def __post_init__(self):
        if self.product_value_next <= 0:
            raise ValueError("product_value_next must be > 0")
        if math.isnan(self.net_cashflow) or math.isinf(self.net_cashflow):
            raise ValueError("net_cashflow must be finite")
