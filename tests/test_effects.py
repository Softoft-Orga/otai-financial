from __future__ import annotations

import unittest
from dataclasses import replace

from otai_forecast.compute import calculate_new_monthly_data
from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision, State


class TestProductValueBehavior(unittest.TestCase):
    def setUp(self):
        # Start from defaults and only override test-specific values
        self.a = replace(
            DEFAULT_ASSUMPTIONS,
            months=1,
            starting_cash=100_000.0,
            base_organic_users_per_month=2_000.0,
            conv_web_to_lead=0.03,
            conv_website_lead_to_free=0.20,
            conv_website_lead_to_pro=0.03,
            conv_website_lead_to_ent=0.002,
            conv_outreach_lead_to_free=0.08,
            conv_outreach_lead_to_pro=0.10,
            conv_outreach_lead_to_ent=0.01,
            conv_free_to_pro=0.08,
            conv_pro_to_ent=0.02,
            churn_free=0.15,
            churn_pro=0.03,
            churn_ent=0.01,
            churn_pro_floor=0.01,
            qualified_pool_total=20_000.0,
            credit_cash_threshold=0.0,
            credit_draw_amount=0.0,
        )
        self.state = State(
            month=0,
            cash=self.a.starting_cash,
            debt=0.0,
            domain_rating=self.a.domain_rating_init,
            product_value=self.a.pv_init,
            free_active=0.0,
            pro_active=0.0,
            ent_active=0.0,
            partners_active=0.0,
        )

    def test_higher_dev_spend_improves_product_value(self):
        low = MonthlyDecision(
            ads_spend=0.0,
            organic_marketing_spend=0.0,
            dev_spend=0.0,
            partner_spend=0.0,
            direct_candidate_outreach_spend=0.0,
        )
        high = MonthlyDecision(
            ads_spend=0.0,
            organic_marketing_spend=0.0,
            dev_spend=10000.0,
            partner_spend=0.0,
            direct_candidate_outreach_spend=0.0,
        )

        m_low = calculate_new_monthly_data(self.state, self.a, low)
        m_high = calculate_new_monthly_data(self.state, self.a, high)

        self.assertGreaterEqual(m_high.product_value_next, m_low.product_value_next)

    def test_effective_rates_are_bounded(self):
        d = MonthlyDecision(
            ads_spend=1000.0,
            organic_marketing_spend=1000.0,
            dev_spend=0.0,
            partner_spend=0.0,
            direct_candidate_outreach_spend=0.0,
        )
        m = calculate_new_monthly_data(self.state, self.a, d)
        self.assertGreaterEqual(m.conv_web_to_lead_eff, 0.0)
        self.assertLessEqual(m.conv_web_to_lead_eff, 1.0)
        self.assertGreaterEqual(m.churn_pro_eff, self.a.churn_pro_floor)
        self.assertLessEqual(m.churn_pro_eff, 1.0)


if __name__ == "__main__":
    unittest.main()
