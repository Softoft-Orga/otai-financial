from __future__ import annotations

from .models import (
    Context,
    EffectFn,
)


def effect_boost_free_to_pro(mult: float) -> EffectFn:
    """Boost free to pro conversion rate by a multiplier."""

    def apply(ctx: Context) -> Context:
        new_conv = ctx.a.conv_free_to_pro * (1 + mult)
        new_a = ctx.a.__replace__(conv_free_to_pro=new_conv)
        return ctx.__replace__(a=new_a)

    return apply


def effect_boost_lead_to_free(mult: float) -> EffectFn:
    """Boost lead to free conversion rate by a multiplier."""

    def apply(ctx: Context) -> Context:
        new_conv = ctx.a.conv_lead_to_free * (1 + mult)
        new_a = ctx.a.__replace__(conv_lead_to_free=new_conv)
        return ctx.__replace__(a=new_a)

    return apply


def effect_reduce_churn_free(reduction: float) -> EffectFn:
    """Reduce free tier churn rate."""

    def apply(ctx: Context) -> Context:
        new_churn = max(0.0, ctx.a.churn_free * (1 - reduction))
        new_a = ctx.a.__replace__(churn_free=new_churn)
        return ctx.__replace__(a=new_a)

    return apply


def effect_reduce_churn_pro(reduction: float) -> EffectFn:
    """Reduce pro tier churn rate."""

    def apply(ctx: Context) -> Context:
        new_churn = max(0.0, ctx.a.churn_pro * (1 - reduction))
        new_a = ctx.a.__replace__(churn_pro=new_churn)
        return ctx.__replace__(a=new_a)

    return apply


def effect_increase_seo_efficiency(mult: float) -> EffectFn:
    """Increase SEO efficiency by a multiplier."""

    def apply(ctx: Context) -> Context:
        # SEO efficiency is no longer a parameter
        # This effect now increases brand popularity instead
        new_eff = ctx.a.brand_popularity * (1 + mult)
        new_a = ctx.a.__replace__(brand_popularity=new_eff)
        return ctx.__replace__(a=new_a)

    return apply


def effect_increase_referral_rate(mult: float) -> EffectFn:
    """Increase referral rate by a multiplier."""

    def apply(ctx: Context) -> Context:
        new_rate = ctx.a.referral_leads_per_active_free * (1 + mult)
        new_a = ctx.a.__replace__(referral_leads_per_active_free=new_rate)
        return ctx.__replace__(a=new_a)

    return apply


def effect_unlock_sales(prices: tuple[float, float] | None = None) -> EffectFn:
    """Unlock sales by setting default prices."""

    def apply(ctx: Context) -> Context:
        # Prices are now in PolicyParams, not MonthlyInputs
        # This effect no longer needs to do anything
        return ctx

    return apply


def effect_increase_partner_deals(
    pro_mult: float = 1.0, ent_mult: float = 1.0
) -> EffectFn:
    """Increase partner deal rates by multipliers."""

    def apply(ctx: Context) -> Context:
        new_a = ctx.a.__replace__(
            pro_deals_per_partner_per_month=ctx.a.pro_deals_per_partner_per_month
            * (1 + pro_mult),
            ent_deals_per_partner_per_month=ctx.a.ent_deals_per_partner_per_month
            * (1 + ent_mult),
        )
        return ctx.__replace__(a=new_a)

    return apply


def effect_reduce_dev_cost(reduction: float) -> EffectFn:
    """Reduce development cost per day."""

    def apply(ctx: Context) -> Context:
        new_cost = max(0.0, ctx.a.dev_day_cost_eur * (1 - reduction))
        new_a = ctx.a.__replace__(dev_day_cost_eur=new_cost)
        return ctx.__replace__(a=new_a)

    return apply


def effect_increase_ads_efficiency(mult: float) -> EffectFn:
    """Increase ads efficiency by reducing cost per lead."""

    def apply(ctx: Context) -> Context:
        new_cpc = max(0.01, ctx.a.ads_cost_per_lead_base / (1 + mult))
        new_a = ctx.a.__replace__(ads_cost_per_lead_base=new_cpc)
        return ctx.__replace__(a=new_a)

    return apply


def effect_boost_conversion(mult: float) -> EffectFn:
    """Boost lead to free conversion rate."""

    def apply(ctx: Context) -> Context:
        new_a = ctx.a.__replace__(
            conv_lead_to_free=ctx.a.conv_lead_to_free * (1 + mult)
        )
        return ctx.__replace__(a=new_a)

    return apply


def effect_increase_price(mult: float) -> EffectFn:
    """Increase all prices by a multiplier."""

    def apply(ctx: Context) -> Context:
        # This effect doesn't directly modify prices since they're in PolicyParams
        # In a real implementation, this would trigger a price change event
        # For now, we'll simulate by increasing conversion rates (perceived value)
        new_a = ctx.a.__replace__(
            conv_free_to_pro=ctx.a.conv_free_to_pro * (1 + mult * 0.5),
            conv_pro_to_ent=ctx.a.conv_pro_to_ent * (1 + mult * 0.3),
        )
        return ctx.__replace__(a=new_a)

    return apply


def effect_reduce_churn(tier: str, reduction: float) -> EffectFn:
    """Reduce churn rate for a specific tier."""

    def apply(ctx: Context) -> Context:
        if tier == "free":
            new_a = ctx.a.__replace__(churn_free=ctx.a.churn_free * (1 - reduction))
        elif tier == "pro":
            new_a = ctx.a.__replace__(churn_pro=ctx.a.churn_pro * (1 - reduction))
        elif tier == "ent":
            new_a = ctx.a.__replace__(churn_ent=ctx.a.churn_ent * (1 - reduction))
        else:
            return ctx
        return ctx.__replace__(a=new_a)

    return apply


def effect_boost_pro_to_ent(mult: float) -> EffectFn:
    """Boost pro to enterprise conversion rate."""

    def apply(ctx: Context) -> Context:
        new_a = ctx.a.__replace__(conv_pro_to_ent=ctx.a.conv_pro_to_ent * (1 + mult))
        return ctx.__replace__(a=new_a)

    return apply
