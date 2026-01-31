import unittest
from unittest.mock import Mock

from otai_forecast.compute import (
    apply_churn,
    apply_effects,
    clamp,
    compute_finance,
    compute_leads,
    compute_new_ent,
    compute_new_free,
    compute_new_pro,
    compute_partners,
    feature_dev_days_done,
)
from otai_forecast.models import (
    Assumptions,
    Context,
    MonthlyInputs,
    Roadmap,
    State,
)


class TestCompute(unittest.TestCase):
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

        self.state = State(
            t=0,
            cash=100000.0,
            free_active=50.0,
            pro_active=20.0,
            ent_active=5.0,
            partners=10.0,
        )

        self.ctx = Context(t=0, a=self.a, inp=self.inp)

    def test_clamp(self):
        self.assertEqual(clamp(-1.0, 0.0, 1.0), 0.0)
        self.assertEqual(clamp(2.0, 0.0, 1.0), 1.0)
        self.assertEqual(clamp(0.5, 0.0, 1.0), 0.5)
        self.assertEqual(clamp(10.0, 5.0, 15.0), 10.0)

    def test_apply_effects(self):
        # Mock feature and effect
        mock_effect = Mock(return_value=self.ctx)
        mock_feature = Mock()
        mock_feature.effect = mock_effect

        roadmap = Roadmap(features=[mock_feature])
        roadmap.active = Mock(return_value=[mock_feature])

        result = apply_effects(self.ctx, roadmap)

        mock_effect.assert_called_once_with(self.ctx)
        self.assertEqual(result, self.ctx)

    def test_compute_leads(self):
        leads_total = compute_leads(self.state, self.ctx)

        # Ads leads: log2(1000/2 + 1) * 2 = log2(501) * 2 ≈ 8.97 * 2 = 17.94
        # Organic leads: 1.0^1.5 * 10 = 10
        # Referral leads: 50 * 0.01 = 0.5
        # Total: 17.94 + 10 + 0.5 = 28.44
        self.assertAlmostEqual(leads_total, 28.44, places=1)

    def test_compute_new_free(self):
        leads = 28.44

        result = compute_new_free(self.ctx, leads)

        # Conversion: 28.44 * 0.25 = 7.11
        self.assertAlmostEqual(result, 7.11, places=1)

    def test_compute_new_pro(self):
        new_free = 7.11

        result = compute_new_pro(self.ctx, new_free)

        # Conversion: 7.11 * 0.10 = 0.711
        self.assertAlmostEqual(result, 0.711, places=2)

    def test_compute_new_ent(self):
        new_pro = 0.711

        result = compute_new_ent(self.ctx, new_pro)

        # Conversion: 0.711 * 0.02 = 0.01422
        self.assertAlmostEqual(result, 0.01422, places=4)

    def test_apply_churn(self):
        churned, remaining = apply_churn(100.0, 0.15)
        self.assertAlmostEqual(churned, 15.0)
        self.assertAlmostEqual(remaining, 85.0)

        # Test edge cases
        churned, remaining = apply_churn(100.0, 0.0)
        self.assertAlmostEqual(churned, 0.0)
        self.assertAlmostEqual(remaining, 100.0)

        churned, remaining = apply_churn(100.0, 1.0)
        self.assertAlmostEqual(churned, 100.0)
        self.assertAlmostEqual(remaining, 0.0)

    def test_compute_partners(self):
        new_partners, pro_deals, ent_deals = compute_partners(self.state, self.ctx)

        # Expected: new_partners = 0.1, total_partners = 10.1
        # pro_deals = 10.1 * 0.02 = 0.202
        # ent_deals = 10.1 * 0.002 = 0.0202
        self.assertAlmostEqual(new_partners, 0.1)
        self.assertAlmostEqual(pro_deals, 0.202, places=3)
        self.assertAlmostEqual(ent_deals, 0.0202, places=4)

    def test_compute_finance(self):
        maintenance_days = 5.0
        feature_dev_days_done = 10.0
        pro_price = 3500.0
        ent_price = 20000.0

        result = compute_finance(
            self.state,
            self.ctx,
            pro_price,
            ent_price,
            maintenance_days,
            feature_dev_days_done,
        )

        # Revenue: 20 * 3500 + 5 * 20000 = 70000 + 100000 = 170000
        # Costs: 1000 + 200 + 10000 + 5*500 + 10*500 + 0.2*170000 = 1200 + 10000 + 2500 + 5000 + 34000 = 52700
        # Net: 170000 - 52700 = 117300
        self.assertAlmostEqual(result.revenue_total, 170000.0)
        self.assertAlmostEqual(result.net_cashflow, 117300.0)

    def test_feature_dev_days_done(self):
        # Mock roadmap with features launching at t=0
        mock_feature1 = Mock()
        mock_feature1.dev_days = 20.0
        mock_feature2 = Mock()
        mock_feature2.dev_days = 15.0

        roadmap = Roadmap(features=[])
        roadmap.launches_at = Mock(return_value=[mock_feature1, mock_feature2])

        maintenance_days = 5.0
        result = feature_dev_days_done(self.ctx, roadmap, maintenance_days)

        # Required: 20 + 15 = 35
        # Available: 20 - 5 = 15
        # Result: min(35, 15) = 15
        self.assertEqual(result, 15.0)


if __name__ == "__main__":
    unittest.main()
