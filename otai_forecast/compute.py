from __future__ import annotations

import math

from .models import Context, Finance, Roadmap, State


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp a value between a minimum and maximum."""
    return lo if x < lo else hi if x > hi else x


def apply_effects(ctx: Context, roadmap: Roadmap) -> Context:
    """Apply all active feature effects to the context."""
    for feature in roadmap.active(ctx.t):
        if feature.effect is not None:
            ctx = feature.effect(ctx)
    return ctx


def compute_leads(state: State, ctx: Context) -> float:
    """Compute total leads using exponential formulas."""
    # Ads leads with exponential cost
    ads_leads = 0.0
    if ctx.inp.ads_spend > 0 and ctx.a.ads_cost_per_lead_base > 0:
        ads_leads = (
            math.log(ctx.inp.ads_spend / ctx.a.ads_cost_per_lead_base + 1, 2)
            * ctx.a.ads_cost_per_lead_base
        )

    # Brand/organic leads with exponential popularity
    organic_leads = ctx.a.brand_popularity**1.5 * 10  # Base organic leads

    # Referral leads
    referral_leads = max(0.0, state.free_active * ctx.a.referral_leads_per_active_free)

    return ads_leads + organic_leads + referral_leads


def compute_new_free(ctx: Context, leads: float) -> float:
    """Compute new free signups from leads."""
    return leads * ctx.a.conv_lead_to_free


def compute_new_pro(ctx: Context, new_free: float) -> float:
    """Compute new Pro upgrades from free users."""
    return new_free * ctx.a.conv_free_to_pro


def compute_new_ent(ctx: Context, new_pro: float) -> float:
    """Compute new Enterprise upgrades from Pro users."""
    return new_pro * ctx.a.conv_pro_to_ent


def apply_churn(active: float, churn: float) -> tuple[float, float]:
    """Apply churn to active users. Returns (churned, remaining)."""
    churn_rate = clamp(churn, 0.0, 1.0)
    churned = active * churn_rate
    remaining = max(0.0, active - churned)
    return churned, remaining


def compute_partners(state: State, ctx: Context) -> tuple[float, float, float]:
    """Compute partner metrics. Returns (new_partners, pro_deals, ent_deals)."""
    new_partners = max(0.0, ctx.a.new_partners_base_per_month)
    total_partners = max(0.0, state.partners + new_partners)
    pro_deals = total_partners * ctx.a.pro_deals_per_partner_per_month
    ent_deals = total_partners * ctx.a.ent_deals_per_partner_per_month
    return new_partners, pro_deals, ent_deals


def compute_finance(
    state: State,
    ctx: Context,
    pro_price: float,
    ent_price: float,
    maintenance_days: float,
    feature_dev_days_done: float,
) -> Finance:
    """Compute financial metrics for the month."""
    revenue = state.pro_active * pro_price + state.ent_active * ent_price

    costs = {
        "marketing": ctx.inp.ads_spend + ctx.inp.social_spend,
        "ops": ctx.a.ops_fixed_eur_per_month,
        "dev_maintenance": maintenance_days * ctx.a.dev_day_cost_eur,
        "dev_features": feature_dev_days_done * ctx.a.dev_day_cost_eur,
        "partner_commission": ctx.a.partner_commission_rate * revenue,
    }

    total_costs = sum(costs.values())

    # Calculate interest payment (monthly)
    monthly_interest_rate = ctx.a.credit_interest_rate_annual / 12
    interest_payment = state.debt * monthly_interest_rate

    # Check if we need to draw credit
    credit_draw = 0.0
    if state.cash < ctx.a.credit_cash_threshold:
        credit_draw = ctx.a.credit_draw_amount

    # Net cashflow includes interest payment and credit draw
    net_cashflow = revenue - total_costs - interest_payment + credit_draw

    # Calculate profit (no tax)
    profit_before_tax = revenue - total_costs - interest_payment
    profit_after_tax = profit_before_tax  # No tax

    # Calculate MRR, ARR, and market cap (debt reduces market cap)
    mrr = revenue  # Monthly recurring revenue
    arr = mrr * 12  # Annual recurring revenue
    market_cap = arr * ctx.a.valuation_multiple_arr + state.cash - state.debt

    return Finance(
        revenue_total=revenue,
        net_cashflow=net_cashflow,
        profit_before_tax=profit_before_tax,
        profit_after_tax=profit_after_tax,
        mrr=mrr,
        arr=arr,
        market_cap=market_cap,
        debt=state.debt,
        interest_payment=interest_payment,
    )


def feature_dev_days_done(
    ctx: Context, roadmap: Roadmap, maintenance_days: float
) -> float:
    """Compute how many feature development days can be completed this month."""
    # We only have additional_dev_days for new features
    # Maintenance is handled separately from active features
    return ctx.inp.additional_dev_days
