from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, TypeAlias

Month = int


@dataclass(frozen=True)
class Assumptions:
    months: int

    starting_cash: float
    base_organic_users_per_month: float
    cpc_eur: float  # fallback; dynamic CPC will be used if cpc_base/cpc_k/cpc_ref_spend are set
    cpc_base: float
    cpc_k: float
    cpc_ref_spend: float

    seo_eff_users_per_eur: float
    seo_decay: float

    domain_rating_init: float
    domain_rating_max: float
    domain_rating_growth_k: float
    domain_rating_growth_ref_spend: float
    domain_rating_decay: float

    conv_web_to_lead: float
    conv_lead_to_free: float
    conv_free_to_pro: float
    conv_pro_to_ent: float

    churn_free: float
    churn_pro: float
    churn_ent: float
    churn_pro_floor: float

    pro_price_base: float
    ent_price_base: float
    pro_price_k: float
    ent_price_k: float

    tax_rate: float
    market_cap_multiple: float

    sales_cost_per_new_pro: float
    sales_cost_per_new_ent: float
    support_cost_per_pro: float
    support_cost_per_ent: float

    operating_baseline: float
    operating_per_user: float
    operating_per_dev: float

    qualified_pool_total: float
    contact_rate_per_month: float
    scraping_efficiency_k: float
    scraping_ref_spend: float

    credit_cash_threshold: float
    credit_draw_amount: float
    debt_interest_rate_base_annual: float
    debt_interest_rate_k: float
    debt_interest_rate_ref: float

    pv_init: float
    pv_min: float
    pv_ref: float
    pv_decay_shape: float
    pv_growth_scale: float
    k_pv_web_to_lead: float
    k_pv_lead_to_free: float
    k_pv_free_to_pro: float
    k_pv_pro_to_ent: float
    k_pv_churn_pro: float
    k_pv_churn_free: float
    k_pv_churn_ent: float

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
            ("conv_lead_to_free", self.conv_lead_to_free),
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
        if self.contact_rate_per_month < 0:
            raise ValueError("contact_rate_per_month must be >= 0")
        if self.scraping_efficiency_k < 0:
            raise ValueError("scraping_efficiency_k must be >= 0")
        if self.scraping_ref_spend <= 0:
            raise ValueError("scraping_ref_spend must be > 0")

        if self.credit_cash_threshold < 0:
            raise ValueError("credit_cash_threshold must be >= 0")
        if self.credit_draw_amount < 0:
            raise ValueError("credit_draw_amount must be >= 0")
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


@dataclass(frozen=True)
class MonthlyDecision:
    ads_spend: float
    seo_spend: float
    social_spend: float
    dev_spend: float
    scraping_spend: float
    outreach_intensity: float

    pro_price_override: Optional[float] = None
    ent_price_override: Optional[float] = None

    def __post_init__(self):
        for name, v in (
            ("ads_spend", self.ads_spend),
            ("seo_spend", self.seo_spend),
            ("social_spend", self.social_spend),
            ("dev_spend", self.dev_spend),
            ("scraping_spend", self.scraping_spend),
        ):
            if v < 0:
                raise ValueError(f"{name} must be >= 0")

        if self.pro_price_override is not None and self.pro_price_override < 0:
            raise ValueError("pro_price_override must be >= 0")
        if self.ent_price_override is not None and self.ent_price_override < 0:
            raise ValueError("ent_price_override must be >= 0")


MonthlyDecisions: TypeAlias = list["MonthlyDecision"]


@dataclass
class State:
    month: Month = field()
    cash: float = field()
    debt: float = field()
    domain_rating: float = field()
    product_value: float = field()

    free_active: float = field()
    pro_active: float = field()
    ent_active: float = field()

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


@dataclass(frozen=True)
class MonthlyCalculated:
    month: Month

    product_value_next: float
    pv_norm: float
    pro_price: float
    ent_price: float
    conv_web_to_lead_eff: float
    conv_lead_to_free_eff: float
    conv_free_to_pro_eff: float
    conv_pro_to_ent_eff: float
    churn_free_eff: float
    churn_pro_eff: float
    churn_ent_eff: float

    ads_clicks: float
    domain_rating_next: float
    website_users: float
    website_leads: float
    scraped_found: float
    outreach_leads: float
    direct_leads: float
    leads_total: float

    new_free: float
    new_pro: float
    new_ent: float
    churned_free: float
    churned_pro: float
    churned_ent: float

    sales_spend: float
    support_spend: float

    interest_rate_annual_eff: float
    interest_payment: float

    revenue_pro: float
    revenue_ent: float
    revenue_total: float
    costs_ex_tax: float
    profit_bt: float
    tax: float
    net_cashflow: float

    def __post_init__(self):
        if self.product_value_next <= 0:
            raise ValueError("product_value_next must be > 0")
        if math.isnan(self.net_cashflow) or math.isinf(self.net_cashflow):
            raise ValueError("net_cashflow must be finite")
