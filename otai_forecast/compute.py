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
    ratio = d.dev_budget / dev_maint

    if ratio < 1.0:
        decline = a.product_value_decay_shape * (1.0 - ratio) ** 2
        pv_next = max(a.pv_min, state.product_value * (1.0 - decline))
    else:
        growth = a.dev_spend_growth_efficiency * math.log1p(ratio - 1.0)
        pv_next = state.product_value * (1.0 + growth)

    product_value_factor = math.log1p(pv_next / a.pv_ref)
    return pv_next, product_value_factor


def _map_value_to_rates_prices(
    product_value_factor: float, a: Assumptions, d: MonthlyDecision
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
        a.conv_web_to_lead
        * (1.0 + a.product_value_impact_on_web_conversions * product_value_factor),
        0.0,
        1.0,
    )

    conv_website_lead_to_free_eff = clamp(
        a.conv_website_lead_to_free
        * (1.0 + a.product_value_impact_on_lead_to_free * product_value_factor),
        0.0,
        1.0,
    )
    conv_website_lead_to_pro_eff = clamp(
        a.conv_website_lead_to_pro
        * (1.0 + a.product_value_impact_on_lead_to_free * product_value_factor),
        0.0,
        1.0,
    )
    conv_website_lead_to_ent_eff = clamp(
        a.conv_website_lead_to_ent
        * (1.0 + a.product_value_impact_on_lead_to_free * product_value_factor),
        0.0,
        1.0,
    )

    conv_outreach_lead_to_free_eff = clamp(
        a.conv_outreach_lead_to_free
        * (1.0 + a.product_value_impact_on_lead_to_free * product_value_factor),
        0.0,
        1.0,
    )
    conv_outreach_lead_to_pro_eff = clamp(
        a.conv_outreach_lead_to_pro
        * (1.0 + a.product_value_impact_on_lead_to_free * product_value_factor),
        0.0,
        1.0,
    )
    conv_outreach_lead_to_ent_eff = clamp(
        a.conv_outreach_lead_to_ent
        * (1.0 + a.product_value_impact_on_lead_to_free * product_value_factor),
        0.0,
        1.0,
    )

    upgrade_free_to_pro_eff = clamp(
        a.conv_free_to_pro
        * (1.0 + a.product_value_impact_on_free_to_pro * product_value_factor),
        0.0,
        1.0,
    )
    upgrade_pro_to_ent_eff = clamp(
        a.conv_pro_to_ent
        * (1.0 + a.product_value_impact_on_pro_to_ent * product_value_factor),
        0.0,
        1.0,
    )

    churn_pro_eff = clamp(
        a.churn_pro
        * (1.0 - a.product_value_impact_on_pro_churn * product_value_factor),
        a.churn_pro_floor,
        1.0,
    )
    churn_free_eff = clamp(
        a.churn_free
        * (1.0 - a.product_value_impact_on_free_churn * product_value_factor),
        0.0,
        1.0,
    )
    churn_ent_eff = clamp(
        a.churn_ent
        * (1.0 - a.product_value_impact_on_ent_churn * product_value_factor),
        0.0,
        1.0,
    )

    pro_price = (
        d.pro_price_override
        if d.pro_price_override is not None
        else a.pro_price_base * (1.0 + a.pro_price_k * product_value_factor)
    )
    ent_price = (
        d.ent_price_override
        if d.ent_price_override is not None
        else a.ent_price_base * (1.0 + a.ent_price_k * product_value_factor)
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
    return a.cpc_base * (1.0 + a.cpc_sensitivity_factor * spend_factor)


def _effective_interest_rate_annual(debt: float, a: Assumptions) -> float:
    if debt <= 0:
        return 0.0
    return a.debt_interest_rate_base_annual + a.debt_interest_rate_k * math.log1p(
        debt / a.debt_interest_rate_ref
    )


def _update_domain_rating(state: State, a: Assumptions, d: MonthlyDecision) -> float:
    spend_factor = math.log1p(d.seo_budget / a.domain_rating_reference_spend_eur)
    growth = (
        (a.domain_rating_max - state.domain_rating)
        * a.domain_rating_spend_sensitivity
        * spend_factor
    )
    domain_rating_next = state.domain_rating * (1.0 - a.domain_rating_decay) + growth
    return clamp(domain_rating_next, 0.0, a.domain_rating_max)


def calculate_new_monthly_data(
    state: State, a: Assumptions, d: MonthlyDecision, spend_last_month: float = 0.0
) -> MonthlyCalculated:
    pv_next, product_value_factor = _update_product_value(state, a, d)

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
    ) = _map_value_to_rates_prices(product_value_factor, a, d)

    domain_rating_next = _update_domain_rating(state, a, d)

    seo_mult = 1.0 + (domain_rating_next / a.domain_rating_max)
    ads_clicks = (
        d.ads_budget / _effective_cpc(d.ads_budget, a) if d.ads_budget > 0 else 0.0
    )
    website_users = (
        a.base_organic_users_per_month * seo_mult
        + d.seo_budget * a.seo_users_per_eur * seo_mult
        + ads_clicks
    )
    website_leads = website_users * conv_web_to_lead_eff

    # Direct candidate outreach: find candidates from qualified pool with diminishing returns.
    # In this simplified model we contact all scraped candidates.
    spend_factor = math.log1p(d.outreach_budget / a.scraping_ref_spend)
    # Calculate how many we can find from the remaining pool
    scraped_found = state.qualified_pool_remaining * (
        1.0 - math.exp(-a.scraping_efficiency_k * spend_factor)
    )
    outreach_leads = scraped_found
    direct_leads = outreach_leads

    leads_total = website_leads + direct_leads

    # Conversions from website leads
    new_free_from_website = website_leads * conv_website_lead_to_free_eff
    new_pro_from_website = website_leads * conv_website_lead_to_pro_eff
    new_ent_from_website = website_leads * conv_website_lead_to_ent_eff

    # Conversions from outreach leads
    new_free_from_outreach = outreach_leads * conv_outreach_lead_to_free_eff
    new_pro_from_outreach = outreach_leads * conv_outreach_lead_to_pro_eff
    new_ent_from_outreach = outreach_leads * conv_outreach_lead_to_ent_eff

    # Direct conversion costs from outreach (part of COGS)
    outreach_conversion_cost = (
        new_free_from_outreach * a.cost_per_outreach_conversion_free
        + new_pro_from_outreach * a.cost_per_outreach_conversion_pro
        + new_ent_from_outreach * a.cost_per_outreach_conversion_ent
    )

    # Total new customers from all sources (direct conversions, not upgrades)
    new_free_from_all_sources = new_free_from_website + new_free_from_outreach
    new_pro_from_all_sources = new_pro_from_website + new_pro_from_outreach
    new_ent_from_all_sources = new_ent_from_website + new_ent_from_outreach

    churned_free = state.free_active * clamp(churn_free_eff, 0.0, 1.0)
    churned_pro = state.pro_active * clamp(churn_pro_eff, 0.0, 1.0)
    churned_ent = state.ent_active * clamp(churn_ent_eff, 0.0, 1.0)

    new_partners = math.log1p(
        math.log1p(d.partner_budget / a.partner_spend_ref)
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

    # Calculate next period users before accounting for upgrades
    free_next_pre_pro = max(0.0, free_after_churn + new_free_from_all_sources)
    pro_next_pre_ent = max(
        0.0,
        pro_after_churn
        + new_pro_from_all_sources
        + partner_pro_deals
        + upgraded_to_pro,
    )

    # Calculate final next period users after accounting for upgrades
    free_next = max(0.0, free_next_pre_pro - upgraded_to_pro)
    pro_next = max(0.0, pro_next_pre_ent - upgraded_to_ent)
    ent_next = max(
        0.0,
        ent_after_churn
        + new_ent_from_all_sources
        + partner_ent_deals
        + upgraded_to_ent,
    )

    product_value_increase = pv_next - state.product_value
    # Logarithmic renewal fee: 1% for moderate increases, diminishing for larger ones
    renewal_fee_percentage = max(
        0.0,
        min(
            0.05,
            0.01
            * math.log1p(
                product_value_increase / a.monthly_renewal_fee_product_divisor
            ),
        ),
    )
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

    new_pro = new_pro_from_all_sources + upgraded_to_pro
    new_ent = new_ent_from_all_sources + upgraded_to_ent
    sales_spend = (
        new_pro * a.sales_cost_per_new_pro + new_ent * a.sales_cost_per_new_ent
    )
    support_spend = (
        pro_support_subscribers * a.support_cost_per_pro
        + ent_support_subscribers * a.support_cost_per_ent
    )

    interest_rate_annual_eff = _effective_interest_rate_annual(state.debt, a)
    interest_payment = state.debt * (interest_rate_annual_eff / 12.0)

    # Revenue calculation for one-time licenses
    # Only new customers generate revenue (one-time purchase)
    revenue_pro_website = new_pro_from_website * pro_price
    revenue_pro_outreach = new_pro_from_outreach * pro_price
    revenue_pro_partner = partner_pro_deals * pro_price
    revenue_pro = revenue_pro_website + revenue_pro_outreach + revenue_pro_partner

    revenue_ent_website = new_ent_from_website * ent_price
    revenue_ent_outreach = new_ent_from_outreach * ent_price
    revenue_ent_partner = partner_ent_deals * ent_price
    revenue_ent = revenue_ent_website + revenue_ent_outreach + revenue_ent_partner

    # Split renewal fee by tier
    renewal_fee_pro = (
        monthly_renewal_fee
        * (pro_next * pro_price)
        / (pro_next * pro_price + ent_next * ent_price)
        if (pro_next * pro_price + ent_next * ent_price) > 0
        else 0
    )
    renewal_fee_ent = monthly_renewal_fee - renewal_fee_pro
    revenue_renewal_pro = renewal_fee_pro
    revenue_renewal_ent = renewal_fee_ent

    revenue_support_pro = support_subscription_revenue_pro
    revenue_support_ent = support_subscription_revenue_ent

    revenue_total = (
        revenue_pro
        + revenue_ent
        + monthly_renewal_fee
        + support_subscription_revenue_total
    )

    # Calculate costs by financial category

    # 1. COGS (Cost of Goods Sold)
    # Direct costs to deliver the product/service
    cost_payment_processing = (
        revenue_total * a.payment_processing_rate
    )  # Payment processing fees
    cost_outreach_conversion = (
        outreach_conversion_cost  # Direct outreach conversion costs
    )
    cogs = cost_payment_processing + cost_outreach_conversion

    # 2. Operating Expenses (OPEX)
    # Sales & Marketing (acquisition costs, not direct conversion costs)
    cost_sales_marketing = (
        d.ads_budget + d.seo_budget + d.partner_budget + d.outreach_budget + sales_spend
    )

    # R&D (Research & Development)
    # Split dev_spend: portion for R&D (expense) vs CAPEX (investment)
    cost_rd_expense = d.dev_budget * (1 - a.dev_capex_ratio)

    # General & Administrative
    cost_ga = a.operating_baseline  # Fixed G&A costs

    # Customer Support
    cost_customer_support = support_spend

    # IT / Internal Tools
    cost_it_tools = (
        a.operating_per_dev * d.dev_budget
    )  # Overhead and tools per dev spend

    operating_expenses = (
        cost_sales_marketing
        + cost_rd_expense
        + cost_ga
        + cost_customer_support
        + cost_it_tools
    )

    # 3. CAPEX (Capital Expenditures)
    # Long-term investments
    capital_expenditure = (
        d.dev_budget * a.dev_capex_ratio
    )  # Portion of dev spend that's capitalized

    # 4. Financial Expenses
    cost_partner_commission = partner_commission_cost
    financial_expenses = interest_payment + cost_partner_commission

    # Total costs (for backward compatibility)
    costs_ex_tax = cogs + operating_expenses + capital_expenditure + financial_expenses

    profit_bt = revenue_total - costs_ex_tax
    tax = max(0.0, profit_bt) * a.tax_rate
    net_cashflow = profit_bt - tax

    # Calculate next period's qualified pool
    qualified_pool_remaining_next = max(
        0.0, state.qualified_pool_remaining - scraped_found
    )

    return MonthlyCalculated(
        month=state.month,
        product_value_next=pv_next,
        pv_norm=product_value_factor,
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
        qualified_pool_remaining_next=qualified_pool_remaining_next,
        website_users=website_users,
        website_leads=website_leads,
        scraped_found=scraped_found,
        outreach_leads=outreach_leads,
        direct_leads=direct_leads,
        leads_total=leads_total,
        new_free=new_free_from_all_sources,
        new_pro=new_pro,
        new_ent=new_ent,
        free_next=free_next,
        pro_next=pro_next,
        ent_next=ent_next,
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
        cost_of_goods_sold=cogs,
        operating_expenses=operating_expenses,
        capital_expenditure=capital_expenditure,
        financial_expenses=financial_expenses,
        profit_bt=profit_bt,
        tax=tax,
        net_cashflow=net_cashflow,
        # New fields for enhanced plotting
        spend_last_month=spend_last_month,
        revenue_pro_website=revenue_pro_website,
        revenue_pro_outreach=revenue_pro_outreach,
        revenue_pro_partner=revenue_pro_partner,
        revenue_ent_website=revenue_ent_website,
        revenue_ent_outreach=revenue_ent_outreach,
        revenue_ent_partner=revenue_ent_partner,
        revenue_renewal_pro=revenue_renewal_pro,
        revenue_renewal_ent=revenue_renewal_ent,
        revenue_support_pro=revenue_support_pro,
        revenue_support_ent=revenue_support_ent,
        cost_sales_marketing=cost_sales_marketing,
        cost_rd_expense=cost_rd_expense,
        cost_ga=cost_ga,
        cost_customer_support=cost_customer_support,
        cost_it_tools=cost_it_tools,
        cost_payment_processing=cost_payment_processing,
        cost_outreach_conversion=cost_outreach_conversion,
        cost_partner_commission=cost_partner_commission,
    )


def calculate_new_state(
    state: State, monthly: MonthlyCalculated, a: Assumptions
) -> State:
    cash_next = state.cash + monthly.net_cashflow
    debt_next = state.debt

    # Automatic credit draw when cash is low
    if cash_next < a.credit_cash_threshold and a.credit_draw_amount > 0:
        cash_next += a.credit_draw_amount
        debt_next += a.credit_draw_amount

    # Automatic debt repayment when cash is high
    elif (
        cash_next > a.debt_repay_cash_threshold
        and debt_next > 0
        and a.debt_repay_amount > 0
    ):
        # Repay the lesser of: configured amount, available cash above threshold, or total debt
        available_cash = cash_next - a.debt_repay_cash_threshold
        repay_amount = min(a.debt_repay_amount, available_cash, debt_next)
        cash_next -= repay_amount
        debt_next -= repay_amount

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
        qualified_pool_remaining=monthly.qualified_pool_remaining_next,
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
        qualified_pool_remaining=a.qualified_pool_total,
    )

    out: list[MonthlyCalculated] = []
    spend_last_month = 0.0
    for t in range(a.months):
        d = decisions[t]
        # Calculate total spend for this month
        total_spend = (
            d.ads_budget
            + d.seo_budget
            + d.dev_budget
            + d.outreach_budget
            + d.partner_budget
        )

        monthly = calculate_new_monthly_data(state, a, d, spend_last_month)
        out.append(monthly)
        state = calculate_new_state(state, monthly, a)

        # Update spend_last_month for next iteration
        spend_last_month = total_spend
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
        qualified_pool_remaining=a.qualified_pool_total,
    )

    rows: list[dict] = []
    spend_last_month = 0.0
    for t in range(a.months):
        d = decisions[t]
        # Calculate total spend for this month
        total_spend = (
            d.ads_budget
            + d.seo_budget
            + d.dev_budget
            + d.outreach_budget
            + d.partner_budget
        )

        monthly = calculate_new_monthly_data(state, a, d, spend_last_month)
        state_next = calculate_new_state(state, monthly, a)

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
            "ads_spend": d.ads_budget,
            "organic_marketing_spend": d.seo_budget,
            "dev_spend": d.dev_budget,
            "partner_spend": d.partner_budget,
            "direct_candidate_outreach_spend": d.outreach_budget,
        }
        rows.append(row)
        state = state_next

        # Update spend_last_month for next iteration
        spend_last_month = total_spend
    return rows
