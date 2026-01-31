import unittest

from otai_forecast.effects import (
    effect_boost_free_to_pro,
    effect_boost_lead_to_free,
    effect_increase_ads_efficiency,
    effect_increase_partner_deals,
    effect_increase_referral_rate,
    effect_increase_seo_efficiency,
    effect_reduce_churn_free,
    effect_reduce_churn_pro,
    effect_reduce_dev_cost,
    effect_unlock_sales,
)
from otai_forecast.models import (
    Assumptions,
    Context,
    MonthlyInputs,
)


class TestEffects(unittest.TestCase):
    def setUp(self):
        self.a = Assumptions(
            months=12,
            dev_day_cost_eur=500.0,
            starting_cash_eur=100000.0,
            ops_fixed_eur_per_month=10000.0,
            ads_cost_per_lead_base=2.0,
            monthly_ads_expense=500.0,
            brand_popularity=1.0,
            conv_lead_to_free=0.25,
            conv_free_to_pro=0.10,
            conv_pro_to_ent=0.02,
            churn_free=0.15,
            churn_pro=0.03,
            churn_ent=0.01,
            referral_leads_per_active_free=0.01,
            partner_commission_rate=0.20,
            pro_deals_per_partner_per_month=0.02,
            ent_deals_per_partner_per_month=0.002,
            new_partners_base_per_month=0.1,
            valuation_multiple_arr=10.0,
            credit_interest_rate_annual=0.10,
            credit_draw_amount=50000.0,
            credit_cash_threshold=25000.0,
        )

        self.inp = MonthlyInputs(
            ads_spend=1000.0,
            social_spend=200.0,
            additional_dev_days=5.0,
        )

        self.ctx = Context(t=0, a=self.a, inp=self.inp)

    def test_effect_boost_free_to_pro(self):
        effect = effect_boost_free_to_pro(0.5)  # 50% boost
        new_ctx = effect(self.ctx)

        # Original: 0.10, boosted: 0.10 * 1.5 = 0.15
        self.assertAlmostEqual(new_ctx.a.conv_free_to_pro, 0.15)

        # Test that it doesn't exceed 1.0
        effect_large = effect_boost_free_to_pro(10.0)  # 1000% boost
        new_ctx_large = effect_large(self.ctx)
        self.assertEqual(new_ctx_large.a.conv_free_to_pro, 1.0)

    def test_effect_boost_lead_to_free(self):
        effect = effect_boost_lead_to_free(0.2)  # 20% boost
        new_ctx = effect(self.ctx)

        # Original: 0.25, boosted: 0.25 * 1.2 = 0.30
        self.assertAlmostEqual(new_ctx.a.conv_lead_to_free, 0.30)

    def test_effect_reduce_churn_free(self):
        effect = effect_reduce_churn_free(0.05)  # Reduce by 5%
        new_ctx = effect(self.ctx)

        # Original: 0.15, reduced: 0.15 - 0.05 = 0.10
        self.assertAlmostEqual(new_ctx.a.churn_free, 0.10)

        # Test that it doesn't go below 0
        effect_large = effect_reduce_churn_free(0.5)  # Try to reduce by 50%
        new_ctx_large = effect_large(self.ctx)
        self.assertEqual(new_ctx_large.a.churn_free, 0.0)

    def test_effect_reduce_churn_pro(self):
        effect = effect_reduce_churn_pro(0.01)  # Reduce by 1%
        new_ctx = effect(self.ctx)

        # Original: 0.03, reduced: 0.03 - 0.01 = 0.02
        self.assertAlmostEqual(new_ctx.a.churn_pro, 0.02)

    def test_effect_increase_seo_efficiency(self):
        effect = effect_increase_seo_efficiency(0.5)  # 50% boost
        new_ctx = effect(self.ctx)

        # Original: 1.0, boosted: 1.0 * 1.5 = 1.5
        self.assertEqual(new_ctx.a.seo_eff_users_per_eur, 1.5)

    def test_effect_increase_referral_rate(self):
        effect = effect_increase_referral_rate(1.0)  # 100% boost (double)
        new_ctx = effect(self.ctx)

        # Original: 0.01, boosted: 0.01 * 2.0 = 0.02
        self.assertEqual(new_ctx.a.referral_leads_per_active_free, 0.02)

    def test_effect_unlock_sales_default_prices(self):
        # effect_unlock_sales is now a no-op since prices are in PolicyParams
        inp = MonthlyInputs(
            ads_spend=1000.0,
            social_spend=200.0,
            dev_capacity_days=20.0,
            additional_dev_days=5.0,
        )

        ctx = Context(t=0, a=self.a, inp=inp)
        effect = effect_unlock_sales()
        new_ctx = effect(ctx)

        # Should not change anything
        self.assertEqual(new_ctx.inp.ads_spend, 1000.0)
        self.assertEqual(new_ctx.inp.social_spend, 200.0)

    def test_effect_unlock_sales_custom_prices(self):
        # effect_unlock_sales is now a no-op since prices are in PolicyParams
        inp = MonthlyInputs(
            ads_spend=1000.0,
            social_spend=200.0,
            dev_capacity_days=20.0,
            additional_dev_days=5.0,
        )

        ctx = Context(t=0, a=self.a, inp=inp)
        effect = effect_unlock_sales(prices=(5000.0, 25000.0))
        new_ctx = effect(ctx)

        # Should not change anything
        self.assertEqual(new_ctx.inp.ads_spend, 1000.0)
        self.assertEqual(new_ctx.inp.social_spend, 200.0)

    def test_effect_unlock_sales_existing_prices(self):
        # effect_unlock_sales is now a no-op
        effect = effect_unlock_sales()
        new_ctx = effect(self.ctx)

        # Should not change anything
        self.assertEqual(new_ctx.inp.ads_spend, 1000.0)
        self.assertEqual(new_ctx.inp.social_spend, 200.0)

    def test_effect_increase_partner_deals(self):
        effect = effect_increase_partner_deals(pro_mult=0.5, ent_mult=1.0)
        new_ctx = effect(self.ctx)

        # Pro deals: 0.02 * (1 + 0.5) = 0.02 * 1.5 = 0.03
        # Ent deals: 0.002 * (1 + 1.0) = 0.002 * 2.0 = 0.004
        self.assertAlmostEqual(new_ctx.a.pro_deals_per_partner_per_month, 0.03)
        self.assertAlmostEqual(new_ctx.a.ent_deals_per_partner_per_month, 0.004)

    def test_effect_reduce_dev_cost(self):
        effect = effect_reduce_dev_cost(0.2)  # 20% reduction
        new_ctx = effect(self.ctx)

        # Original: 500.0, reduced: 500.0 * 0.8 = 400.0
        self.assertEqual(new_ctx.a.dev_day_cost_eur, 400.0)

        # Test that it doesn't go below 0
        effect_full = effect_reduce_dev_cost(1.5)  # 150% reduction
        new_ctx_full = effect_full(self.ctx)
        self.assertEqual(new_ctx_full.a.dev_day_cost_eur, 0.0)

    def test_effect_increase_ads_efficiency(self):
        effect = effect_increase_ads_efficiency(0.5)  # 50% boost
        new_ctx = effect(self.ctx)

        # Original: 2.0, more efficient: 2.0 / 1.5 = 1.333...
        self.assertAlmostEqual(new_ctx.a.cpc_eur, 2.0 / 1.5, places=3)

        # Test minimum CPC
        effect_large = effect_increase_ads_efficiency(100.0)  # Huge boost
        new_ctx_large = effect_large(self.ctx)
        # Original: 2.0 / 101 = 0.0198 (not hitting minimum yet)
        self.assertAlmostEqual(new_ctx_large.a.cpc_eur, 0.0198, places=4)


if __name__ == "__main__":
    unittest.main()
