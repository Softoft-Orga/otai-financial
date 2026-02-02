from __future__ import annotations

import math
from dataclasses import asdict

from .models import (
    Assumptions,
    MonthlyCalculated,
    MonthlyDecision,
    MonthlyDecisions,
    State,
)


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _update_product_value(
    state: State, a: Assumptions, d: MonthlyDecision
) -> tuple[float, float]:
    dev_maint = max(1e-9, state.product_value / 12.0)
    ratio = d.dev_spend / dev_maint

    if ratio < 1.0:
        decline = a.pv_decay_shape * (1.0 - ratio) ** 2
        pv_next = max(a.pv_min, state.product_value * (1.0 - decline))
    else:
        growth = a.pv_growth_scale * math.log1p(ratio - 1.0)
        pv_next = state.product_value * (1.0 + growth)

    pv_norm = math.log1p(pv_next / a.pv_ref)
    return pv_next, pv_norm


def _map_value_to_rates_prices(
    pv_norm: float, a: Assumptions, d: MonthlyDecision
) -> tuple[
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
    float,
]:
    conv_web_to_lead_eff = clamp(
        a.conv_web_to_lead * (1.0 + a.k_pv_web_to_lead * pv_norm), 0.0, 1.0
    )

    conv_website_lead_to_free_eff = clamp(
        a.conv_website_lead_to_free * (1.0 + a.k_pv_lead_to_free * pv_norm), 0.0, 1.0
    )
    conv_website_lead_to_pro_eff = clamp(
        a.conv_website_lead_to_pro * (1.0 + a.k_pv_lead_to_free * pv_norm), 0.0, 1.0
    )
    conv_website_lead_to_ent_eff = clamp(
        a.conv_website_lead_to_ent * (1.0 + a.k_pv_lead_to_free * pv_norm), 0.0, 1.0
    )

    conv_outreach_lead_to_free_eff = clamp(
        a.conv_outreach_lead_to_free * (1.0 + a.k_pv_lead_to_free * pv_norm), 0.0, 1.0
    )
    conv_outreach_lead_to_pro_eff = clamp(
        a.conv_outreach_lead_to_pro * (1.0 + a.k_pv_lead_to_free * pv_norm), 0.0, 1.0
    )
    conv_outreach_lead_to_ent_eff = clamp(
        a.conv_outreach_lead_to_ent * (1.0 + a.k_pv_lead_to_free * pv_norm), 0.0, 1.0
    )

    upgrade_free_to_pro_eff = clamp(
        a.conv_free_to_pro * (1.0 + a.k_pv_free_to_pro * pv_norm), 0.0, 1.0
    )
    upgrade_pro_to_ent_eff = clamp(
        a.conv_pro_to_ent * (1.0 + a.k_pv_pro_to_ent * pv_norm), 0.0, 1.0
    )

    churn_pro_eff = clamp(
        a.churn_pro * (1.0 - a.k_pv_churn_pro * pv_norm), a.churn_pro_floor, 1.0
    )
    churn_free_eff = clamp(a.churn_free * (1.0 - a.k_pv_churn_free * pv_norm), 0.0, 1.0)
    churn_ent_eff = clamp(a.churn_ent * (1.0 - a.k_pv_churn_ent * pv_norm), 0.0, 1.0)

    pro_price = (
        d.pro_price_override
        if d.pro_price_override is not None
        else a.pro_price_base * (1.0 + a.pro_price_k * pv_norm)
    )
    ent_price = (
        d.ent_price_override
        if d.ent_price_override is not None
        else a.ent_price_base * (1.0 + a.ent_price_k * pv_norm)
    )

    return (
        pro_price,
        ent_price,
        conv_web_to_lead_eff,
        conv_website_lead_to_free_eff,
        conv_website_lead_to_pro_eff,
        conv_website_lead_to_ent_eff,
        conv_outreach_lead_to_free_eff,
        conv_outreach_lead_to_pro_eff,
        conv_outreach_lead_to_ent_eff,
        upgrade_free_to_pro_eff,
        upgrade_pro_to_ent_eff,
        churn_free_eff,
        churn_pro_eff,
        churn_ent_eff,
    )


def _effective_cpc(ads_spend: float, a: Assumptions) -> float:
    """Dynamic CPC: lower when less is spent, higher when more is spent (logarithmic)."""
    if ads_spend <= 0:
        return a.cpc_base
    spend_factor = math.log1p(ads_spend / a.cpc_ref_spend)
    return a.cpc_base * (1.0 + a.cpc_k * spend_factor)


def _effective_interest_rate_annual(debt: float, a: Assumptions) -> float:
    if debt <= 0:
        return 0.0
    return a.debt_interest_rate_base_annual + a.debt_interest_rate_k * math.log1p(
        debt / a.debt_interest_rate_ref
    )


def _update_domain_rating(state: State, a: Assumptions, d: MonthlyDecision) -> float:
    spend_factor = math.log1p(d.seo_spend / a.domain_rating_growth_ref_spend)
    growth = (
        (a.domain_rating_max - state.domain_rating)
        * a.domain_rating_growth_k
        * spend_factor
    )
    domain_rating_next = state.domain_rating * (1.0 - a.domain_rating_decay) + growth
    return clamp(domain_rating_next, 0.0, a.domain_rating_max)


def calculate_new_monthly_data(
    state: State, a: Assumptions, d: MonthlyDecision
) -> MonthlyCalculated:
    pv_next, pv_norm = _update_product_value(state, a, d)

    (
        pro_price,
        ent_price,
        conv_web_to_lead_eff,
        conv_website_lead_to_free_eff,
        conv_website_lead_to_pro_eff,
        conv_website_lead_to_ent_eff,
        conv_outreach_lead_to_free_eff,
        conv_outreach_lead_to_pro_eff,
        conv_outreach_lead_to_ent_eff,
        upgrade_free_to_pro_eff,
        upgrade_pro_to_ent_eff,
        churn_free_eff,
        churn_pro_eff,
        churn_ent_eff,
    ) = _map_value_to_rates_prices(pv_norm, a, d)

    domain_rating_next = _update_domain_rating(state, a, d)

    seo_mult = 1.0 + (domain_rating_next / a.domain_rating_max)
    ads_clicks = (
        d.ads_spend / _effective_cpc(d.ads_spend, a) if d.ads_spend > 0 else 0.0
    )
    website_users = (
        a.base_organic_users_per_month * seo_mult
        + d.seo_spend * a.seo_eff_users_per_eur * seo_mult
        + ads_clicks
    )
    website_leads = website_users * conv_web_to_lead_eff

    # Direct candidate outreach: find candidates from qualified pool with diminishing returns.
    # In this simplified model we contact all scraped candidates.
    spend_factor = math.log1p(d.direct_candidate_outreach_spend / a.scraping_ref_spend)
    scraped_found = a.qualified_pool_total * (
        1.0 - math.exp(-a.scraping_efficiency_k * spend_factor)
    )
    outreach_leads = scraped_found
    direct_leads = outreach_leads

    leads_total = website_leads + direct_leads

    new_free_from_website = website_leads * conv_website_lead_to_free_eff
    new_pro_direct_from_website = website_leads * conv_website_lead_to_pro_eff
    new_ent_direct_from_website = website_leads * conv_website_lead_to_ent_eff

    new_free_from_outreach = outreach_leads * conv_outreach_lead_to_free_eff
    new_pro_direct_from_outreach = outreach_leads * conv_outreach_lead_to_pro_eff
    new_ent_direct_from_outreach = outreach_leads * conv_outreach_lead_to_ent_eff

    new_free = new_free_from_website + new_free_from_outreach
    new_pro_direct = new_pro_direct_from_website + new_pro_direct_from_outreach
    new_ent_direct = new_ent_direct_from_website + new_ent_direct_from_outreach

    churned_free = state.free_active * clamp(churn_free_eff, 0.0, 1.0)
    churned_pro = state.pro_active * clamp(churn_pro_eff, 0.0, 1.0)
    churned_ent = state.ent_active * clamp(churn_ent_eff, 0.0, 1.0)

    new_partners = math.log1p(
        math.log1p(d.partner_spend / a.partner_spend_ref)
        * math.log1p(state.product_value / a.partner_product_value_ref)
    )
    churned_partners = state.partners_active * a.partner_churn_per_month
    partners_next = max(0.0, state.partners_active - churned_partners + new_partners)

    partner_pro_deals = partners_next * a.partner_pro_deals_per_partner_per_month
    partner_ent_deals = partners_next * a.partner_ent_deals_per_partner_per_month

    free_after_churn = max(0.0, state.free_active - churned_free)
    pro_after_churn = max(0.0, state.pro_active - churned_pro)
    ent_after_churn = max(0.0, state.ent_active - churned_ent)

    upgraded_to_pro = free_after_churn * upgrade_free_to_pro_eff
    upgraded_to_ent = pro_after_churn * upgrade_pro_to_ent_eff

    max(0.0, free_after_churn + new_free - upgraded_to_pro)
    pro_next_pre_ent = max(
        0.0,
        pro_after_churn + new_pro_direct + partner_pro_deals + upgraded_to_pro,
    )
    pro_next = max(0.0, pro_next_pre_ent - upgraded_to_ent)
    ent_next = max(
        0.0, ent_after_churn + new_ent_direct + partner_ent_deals + upgraded_to_ent
    )

    product_value_increase = pv_next - state.product_value
    renewal_fee_percentage = max(0.0, product_value_increase / a.product_value_divisor)
    monthly_renewal_fee = renewal_fee_percentage * (
        pro_next * pro_price + ent_next * ent_price
    )

    pro_support_subscribers = pro_next * a.support_subscription_take_rate_pro
    ent_support_subscribers = ent_next * a.support_subscription_take_rate_ent

    support_subscription_revenue_pro = (
        pro_support_subscribers * pro_price * a.support_subscription_fee_pct_pro
    )
    support_subscription_revenue_ent = (
        ent_support_subscribers * ent_price * a.support_subscription_fee_pct_ent
    )
    support_subscription_revenue_total = (
        support_subscription_revenue_pro + support_subscription_revenue_ent
    )

    partner_commission_cost = a.partner_commission_rate * (
        partner_pro_deals * pro_price + partner_ent_deals * ent_price
    )

    new_pro = new_pro_direct + upgraded_to_pro
    new_ent = new_ent_direct + upgraded_to_ent
    sales_spend = (
        new_pro * a.sales_cost_per_new_pro + new_ent * a.sales_cost_per_new_ent
    )
    support_spend = (
        pro_support_subscribers * a.support_cost_per_pro
        + ent_support_subscribers * a.support_cost_per_ent
    )

    operating_spend = (
        a.operating_baseline
        + a.operating_per_user * (pro_next + ent_next)
        + a.operating_per_dev * d.dev_spend
    )

    interest_rate_annual_eff = _effective_interest_rate_annual(state.debt, a)
    interest_payment = state.debt * (interest_rate_annual_eff / 12.0)

    revenue_pro = pro_next * pro_price
    revenue_ent = ent_next * ent_price
    revenue_total = (
        revenue_pro
        + revenue_ent
        + monthly_renewal_fee
        + support_subscription_revenue_total
    )

    costs_ex_tax = (
        d.ads_spend
        + d.seo_spend
        + d.social_spend
        + d.dev_spend
        + d.partner_spend
        + operating_spend
        + d.direct_candidate_outreach_spend
        + sales_spend
        + support_spend
        + partner_commission_cost
        + interest_payment
    )

    profit_bt = revenue_total - costs_ex_tax
    tax = max(0.0, profit_bt) * a.tax_rate
    net_cashflow = profit_bt - tax

    return MonthlyCalculated(
        month=state.month,
        product_value_next=pv_next,
        pv_norm=pv_norm,
        pro_price=pro_price,
        ent_price=ent_price,
        renewal_fee_percentage=renewal_fee_percentage,
        monthly_renewal_fee=monthly_renewal_fee,
        pro_support_subscribers=pro_support_subscribers,
        ent_support_subscribers=ent_support_subscribers,
        support_subscription_revenue_pro=support_subscription_revenue_pro,
        support_subscription_revenue_ent=support_subscription_revenue_ent,
        support_subscription_revenue_total=support_subscription_revenue_total,
        new_partners=new_partners,
        churned_partners=churned_partners,
        partner_pro_deals=partner_pro_deals,
        partner_ent_deals=partner_ent_deals,
        partner_commission_cost=partner_commission_cost,
        conv_web_to_lead_eff=conv_web_to_lead_eff,
        conv_website_lead_to_free_eff=conv_website_lead_to_free_eff,
        conv_website_lead_to_pro_eff=conv_website_lead_to_pro_eff,
        conv_website_lead_to_ent_eff=conv_website_lead_to_ent_eff,
        conv_outreach_lead_to_free_eff=conv_outreach_lead_to_free_eff,
        conv_outreach_lead_to_pro_eff=conv_outreach_lead_to_pro_eff,
        conv_outreach_lead_to_ent_eff=conv_outreach_lead_to_ent_eff,
        upgrade_free_to_pro_eff=upgrade_free_to_pro_eff,
        upgrade_pro_to_ent_eff=upgrade_pro_to_ent_eff,
        churn_free_eff=churn_free_eff,
        churn_pro_eff=churn_pro_eff,
        churn_ent_eff=churn_ent_eff,
        ads_clicks=ads_clicks,
        domain_rating_next=domain_rating_next,
        website_users=website_users,
        website_leads=website_leads,
        scraped_found=scraped_found,
        outreach_leads=outreach_leads,
        direct_leads=direct_leads,
        leads_total=leads_total,
        new_free=new_free,
        new_pro=new_pro,
        new_ent=new_ent,
        upgraded_to_pro=upgraded_to_pro,
        upgraded_to_ent=upgraded_to_ent,
        churned_free=churned_free,
        churned_pro=churned_pro,
        churned_ent=churned_ent,
        sales_spend=sales_spend,
        support_spend=support_spend,
        interest_rate_annual_eff=interest_rate_annual_eff,
        interest_payment=interest_payment,
        revenue_pro=revenue_pro,
        revenue_ent=revenue_ent,
        revenue_total=revenue_total,
        costs_ex_tax=costs_ex_tax,
        profit_bt=profit_bt,
        tax=tax,
        net_cashflow=net_cashflow,
    )


def calculate_new_state(
    state: State, monthly: MonthlyCalculated, a: Assumptions
) -> State:
    cash_next = state.cash + monthly.net_cashflow
    debt_next = state.debt
    if cash_next < a.credit_cash_threshold and a.credit_draw_amount > 0:
        cash_next += a.credit_draw_amount
        debt_next += a.credit_draw_amount

    return State(
        month=state.month + 1,
        cash=cash_next,
        debt=debt_next,
        domain_rating=monthly.domain_rating_next,
        product_value=monthly.product_value_next,
        free_active=max(
            0.0,
            (state.free_active - monthly.churned_free)
            + monthly.new_free
            - monthly.upgraded_to_pro,
        ),
        pro_active=max(
            0.0,
            (state.pro_active - monthly.churned_pro)
            + monthly.new_pro
            + monthly.partner_pro_deals
            - monthly.upgraded_to_ent,
        ),
        ent_active=max(
            0.0,
            (state.ent_active - monthly.churned_ent)
            + monthly.new_ent
            + monthly.partner_ent_deals,
        ),
        partners_active=max(
            0.0, state.partners_active - monthly.churned_partners + monthly.new_partners
        ),
    )


def run_simulation(
    a: Assumptions, decisions: MonthlyDecisions
) -> list[MonthlyCalculated]:
    state = State(
        month=0,
        cash=a.starting_cash,
        debt=0.0,
        domain_rating=a.domain_rating_init,
        product_value=a.pv_init,
        free_active=0.0,
        pro_active=0.0,
        ent_active=0.0,
        partners_active=0.0,
    )

    out: list[MonthlyCalculated] = []
    for t in range(a.months):
        d = decisions[t]
        monthly = calculate_new_monthly_data(state, a, d)
        out.append(monthly)
        state = calculate_new_state(state, monthly, a)
    return out


def run_simulation_rows(a: Assumptions, decisions: MonthlyDecisions) -> list[dict]:
    state = State(
        month=0,
        cash=a.starting_cash,
        debt=0.0,
        domain_rating=a.domain_rating_init,
        product_value=a.pv_init,
        free_active=0.0,
        pro_active=0.0,
        ent_active=0.0,
        partners_active=0.0,
    )

    rows: list[dict] = []
    for t in range(a.months):
        d = decisions[t]
        monthly = calculate_new_monthly_data(state, a, d)
        state_next = calculate_new_state(state, monthly, a)

        # Calculate operating_spend using the hybrid formula
        operating_spend = (
            a.operating_baseline
            + a.operating_per_user * (state_next.pro_active + state_next.ent_active)
            + a.operating_per_dev * d.dev_spend
        )

        row = {
            **asdict(monthly),
            "cash": state_next.cash,
            "debt": state_next.debt,
            "domain_rating": state_next.domain_rating,
            "product_value": state_next.product_value,
            "free_active": state_next.free_active,
            "pro_active": state_next.pro_active,
            "ent_active": state_next.ent_active,
            "partners_active": state_next.partners_active,
            "ads_spend": d.ads_spend,
            "seo_spend": d.seo_spend,
            "social_spend": d.social_spend,
            "dev_spend": d.dev_spend,
            "partner_spend": d.partner_spend,
            "operating_spend": operating_spend,
            "direct_candidate_outreach_spend": d.direct_candidate_outreach_spend,
        }
        rows.append(row)
        state = state_next
    return rows
