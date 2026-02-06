from __future__ import annotations

import math

from .models import (
    Assumptions,
    MonthlyCalculated,
    MonthlyDecision,
    MonthlyDecisions,
    State,
)


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def _update_product_value(state: State, a: Assumptions, d: MonthlyDecision) -> float:
    pv_next = state.product_value * (1.0 - a.product_value_depreciation_rate) + d.dev_budget
    return max(a.pv_min, pv_next)


def _milestone_for_value(product_value: float, a: Assumptions) -> int:
    milestone_index = 0
    for idx, milestone in enumerate(a.pricing_milestones):
        if product_value >= milestone.product_value_min:
            milestone_index = idx
        else:
            break
    return milestone_index


def _prices_for_value(product_value: float, a: Assumptions) -> tuple[float, float]:
    milestone = a.pricing_milestones[_milestone_for_value(product_value, a)]
    return milestone.pro_price, milestone.ent_price


def _effective_cpc(ads_spend: float, a: Assumptions) -> float:
    """Dynamic CPC: lower when less is spent, higher when more is spent (logarithmic)."""
    if ads_spend <= 0:
        return a.cpc_base
    spend_factor = math.log1p(ads_spend / a.cpc_ref_spend)
    return a.cpc_base * (1.0 + a.cpc_sensitivity_factor * spend_factor)


def _effective_interest_rate_annual(
        debt: float, annual_revenue_ttm: float, new_credit_draw: float, a: Assumptions
) -> float:
    if debt <= 0 and new_credit_draw <= 0:
        return 0.0
    if annual_revenue_ttm <= 0:
        return a.debt_interest_rate_base_annual

    debt_base = debt + new_credit_draw

    # Use logarithmic scaling to prevent interest rate from going extremely low
    # The debt_to_revenue_ratio is the primary driver, but we use log1p to create diminishing returns
    debt_to_revenue_ratio = debt_base / annual_revenue_ttm

    # Apply logarithmic scaling with sensitivity factor
    # Higher sensitivity_factor makes the rate decrease slower with revenue
    log_factor = math.log1p(debt_to_revenue_ratio) / math.log1p(1.0)

    # Calculate effective rate with minimum floor to prevent extremely low rates
    effective_rate = a.debt_interest_rate_base_annual * (1.0 + a.debt_interest_rate_sensitivity_factor * log_factor)

    # Ensure minimum rate of 1% (0.01) to prevent unrealistically low interest rates
    return max(effective_rate, 0.01)


def _update_domain_rating(state: State, a: Assumptions, d: MonthlyDecision) -> float:
    spend_factor = math.log1p(d.seo_budget / a.domain_rating_reference_spend_eur)
    growth_potential = a.domain_rating_max - state.domain_rating
    growth_rate = 1.0 - math.exp(-a.domain_rating_spend_sensitivity * spend_factor)
    decay_amount = state.domain_rating * a.domain_rating_decay
    growth = growth_potential * growth_rate
    domain_rating_next = state.domain_rating - decay_amount + growth
    return clamp(domain_rating_next, 0.0, a.domain_rating_max)


def calculate_new_monthly_data(
        state: State, a: Assumptions, d: MonthlyDecision, spend_last_month: float = 0.0
) -> MonthlyCalculated:
    pv_next = _update_product_value(state, a, d)
    pro_price, ent_price = _prices_for_value(pv_next, a)


    domain_rating_next = _update_domain_rating(state, a, d)

    seo_authority = clamp(domain_rating_next / a.domain_rating_max, 0.0, 1.0)
    ads_clicks = (
        d.ads_budget / _effective_cpc(d.ads_budget, a) if d.ads_budget > 0 else 0.0
    )
    seo_users = (
        a.domain_rating_reference_spend_eur * math.log1p(
            d.seo_budget / a.domain_rating_reference_spend_eur
        )
        * a.seo_users_per_eur
        * (0.4 + 1.2 * (seo_authority ** 1.2))
    )
    website_users = seo_users + ads_clicks
    website_leads = website_users * a.conv_web_to_lead
    website_leads_available = state.website_leads

    # Direct candidate outreach: find candidates from qualified pool with diminishing returns.
    # In this simplified model we contact all scraped candidates.
    direct_contacted_leads = state.qualified_pool_remaining * (
            1.0 - math.exp(-a.scraping_efficiency_k * math.log1p(d.outreach_budget / a.scraping_ref_spend))
    )
    direct_contacted_cost = direct_contacted_leads * a.cost_per_direct_lead
    new_direct_demo_appointments = (
            direct_contacted_leads * a.direct_contacted_demo_conversion
    )
    direct_demo_appointments_available = state.direct_demo_appointments
    direct_demo_appointment_cost = (
            direct_demo_appointments_available * a.cost_per_direct_demo
    )

    leads_total = website_leads + direct_contacted_leads

    # Conversions from website leads
    new_free_from_website = website_leads_available * a.conv_website_lead_to_free
    new_pro_from_website = website_leads_available * a.conv_website_lead_to_pro
    new_ent_from_website = website_leads_available * a.conv_website_lead_to_ent

    # Conversions from direct demo appointments (delayed from prior month)
    new_free_from_outreach = (
            direct_demo_appointments_available
            * a.direct_demo_appointment_conversion_to_free
    )
    new_pro_from_outreach = (
            direct_demo_appointments_available
            * a.direct_demo_appointment_conversion_to_pro
    )
    new_ent_from_outreach = (
            direct_demo_appointments_available
            * a.direct_demo_appointment_conversion_to_ent
    )

    # Total new customers from all sources (direct conversions, not upgrades)
    new_free_from_all_sources = new_free_from_website + new_free_from_outreach
    new_pro_from_all_sources = new_pro_from_website + new_pro_from_outreach
    new_ent_from_all_sources = new_ent_from_website + new_ent_from_outreach

    churned_free = state.free_active * clamp(a.churn_free, 0.0, 1.0)
    churned_pro = state.pro_active * clamp(a.churn_pro, 0.0, 1.0)
    churned_ent = state.ent_active * clamp(a.churn_ent, 0.0, 1.0)

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

    upgraded_to_pro = free_after_churn * a.conv_free_to_pro
    upgraded_to_ent = pro_after_churn * a.conv_pro_to_ent

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

    milestone_current = _milestone_for_value(state.product_value, a)
    milestone_next = _milestone_for_value(pv_next, a)
    milestone_advanced = milestone_next > milestone_current
    # Only calculate renewal fees if milestone advanced and hasn't been renewed before
    milestone_already_renewed = milestone_next in state.renewed_milestones
    renewal_upgrade_rate = a.milestone_achieved_renewal_percentage if milestone_advanced and not milestone_already_renewed else 0.0
    renewal_discount_rate = a.product_renewal_discount_percentage if milestone_advanced and not milestone_already_renewed else 0.0
    renewal_multiplier = renewal_upgrade_rate * (1.0 - renewal_discount_rate)
    renewal_fee_pro = pro_next * pro_price * renewal_multiplier
    renewal_fee_ent = ent_next * ent_price * renewal_multiplier
    monthly_renewal_fee = renewal_fee_pro + renewal_fee_ent

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

    annual_revenue_ttm = sum(state.revenue_history)

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
    cost_outreach_conversion = direct_contacted_cost + direct_demo_appointment_cost
    cogs = cost_payment_processing

    # 2. Operating Expenses (OPEX)
    # Sales & Marketing (acquisition costs, not direct conversion costs)
    cost_sales_marketing = (
            d.ads_budget
            + d.seo_budget
            + d.partner_budget
            + d.outreach_budget
            + sales_spend
            + cost_outreach_conversion
    )

    # R&D (Research & Development)
    # Split dev_spend: portion for R&D (expense) vs CAPEX (investment)
    cost_rd_expense = d.dev_budget * (1 - a.dev_capex_ratio)

    # General & Administrative
    cost_ga = a.operating_baseline + a.operating_per_user * (
            state.free_active + state.pro_active + state.ent_active
    )

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

    cost_partner_commission = partner_commission_cost
    costs_ex_tax_pre_interest = (
            cogs + operating_expenses + capital_expenditure + cost_partner_commission
    )
    profit_bt_pre_interest = revenue_total - costs_ex_tax_pre_interest
    tax_pre_interest = max(0.0, profit_bt_pre_interest) * a.tax_rate
    net_cashflow_pre_financing = profit_bt_pre_interest - tax_pre_interest

    new_credit_draw = max(0.0, -net_cashflow_pre_financing * a.credit_draw_factor)

    interest_rate_annual_eff = _effective_interest_rate_annual(
        state.debt, annual_revenue_ttm, new_credit_draw, a
    )
    interest_payment = (state.debt + new_credit_draw) * (
            interest_rate_annual_eff / 12.0
    )
    financial_expenses = interest_payment + cost_partner_commission

    costs_ex_tax = cogs + operating_expenses + capital_expenditure + financial_expenses
    profit_bt = revenue_total - costs_ex_tax
    tax = max(0.0, profit_bt) * a.tax_rate
    net_cashflow = profit_bt - tax

    required_credit_draw = max(0.0, -(state.cash + net_cashflow))
    if required_credit_draw > new_credit_draw:
        new_credit_draw = required_credit_draw
        interest_rate_annual_eff = _effective_interest_rate_annual(
            state.debt, annual_revenue_ttm, new_credit_draw, a
        )
        interest_payment = (state.debt + new_credit_draw) * (
                interest_rate_annual_eff / 12.0
        )
        financial_expenses = interest_payment + cost_partner_commission
        costs_ex_tax = (
                cogs + operating_expenses + capital_expenditure + financial_expenses
        )
        profit_bt = revenue_total - costs_ex_tax
        tax = max(0.0, profit_bt) * a.tax_rate
        net_cashflow = profit_bt - tax

    min_cash_required = max(0.0, -net_cashflow_pre_financing) * a.min_months_cash_reserve
    projected_cash_after_financing = state.cash + net_cashflow + new_credit_draw
    max_payable_debt_repayment = max(0.0, projected_cash_after_financing - min_cash_required)
    debt_repayment = min(state.debt * a.debt_repay_factor, max_payable_debt_repayment)

    # Calculate next period's qualified pool
    qualified_pool_remaining_next = max(
        0.0, state.qualified_pool_remaining - direct_contacted_leads
    )

    return MonthlyCalculated(
        month=state.month,
        product_value_next=pv_next,
        pro_price=pro_price,
        ent_price=ent_price,
        renewal_upgrade_rate=renewal_upgrade_rate,
        renewal_discount_rate=renewal_discount_rate,
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
        conv_web_to_lead_eff=a.conv_web_to_lead,
        conv_website_lead_to_free_eff=a.conv_website_lead_to_free,
        conv_website_lead_to_pro_eff=a.conv_website_lead_to_pro,
        conv_website_lead_to_ent_eff=a.conv_website_lead_to_ent,
        direct_contacted_demo_conversion_eff=a.direct_contacted_demo_conversion,
        direct_demo_appointment_conversion_to_free_eff=a.direct_demo_appointment_conversion_to_free,
        direct_demo_appointment_conversion_to_pro_eff=a.direct_demo_appointment_conversion_to_pro,
        direct_demo_appointment_conversion_to_ent_eff=a.direct_demo_appointment_conversion_to_ent,
        upgrade_free_to_pro_eff=a.conv_free_to_pro,
        upgrade_pro_to_ent_eff=a.conv_pro_to_ent,
        churn_free_eff=a.churn_free,
        churn_pro_eff=a.churn_pro,
        churn_ent_eff=a.churn_ent,
        ads_clicks=ads_clicks,
        domain_rating_next=domain_rating_next,
        qualified_pool_remaining_next=qualified_pool_remaining_next,
        website_users=website_users,
        website_leads=website_leads,
        website_leads_available=website_leads_available,
        annual_revenue_ttm=annual_revenue_ttm,
        new_direct_leads=direct_contacted_leads,
        direct_contacted_leads=direct_contacted_leads,
        direct_contacted_cost=direct_contacted_cost,
        new_direct_demo_appointments=new_direct_demo_appointments,
        direct_demo_appointments_available=direct_demo_appointments_available,
        direct_demo_appointment_cost=direct_demo_appointment_cost,
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
        new_credit_draw=new_credit_draw,
        debt_repayment=debt_repayment,
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
    cash_next = (
            state.cash + monthly.net_cashflow + monthly.new_credit_draw - monthly.debt_repayment
    )
    debt_next = max(0.0, state.debt + monthly.new_credit_draw - monthly.debt_repayment)
    revenue_history = (*state.revenue_history, monthly.revenue_total)
    if len(revenue_history) > 12:
        revenue_history = revenue_history[-12:]

    # Track renewed milestones
    renewed_milestones = set(state.renewed_milestones)
    if monthly.monthly_renewal_fee > 0:
        # Find which milestone we just advanced to
        milestone_next = _milestone_for_value(monthly.product_value_next, a)
        renewed_milestones.add(milestone_next)

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
        website_leads=monthly.website_leads,
        direct_demo_appointments=monthly.new_direct_demo_appointments,
        revenue_history=revenue_history,
        renewed_milestones=renewed_milestones,
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
        website_leads=0.0,
        direct_demo_appointments=0.0,
        revenue_history=(),
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
        website_leads=0.0,
        direct_demo_appointments=0.0,
        revenue_history=(),
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
            **monthly.model_dump(),
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
            # Add decision attributes for plotting
            "ads_budget": d.ads_budget,
            "seo_budget": d.seo_budget,
            "dev_budget": d.dev_budget,
            "outreach_budget": d.outreach_budget,
            "partner_budget": d.partner_budget,
        }
        rows.append(row)
        state = state_next

        # Update spend_last_month for next iteration
        spend_last_month = total_spend
    return rows
