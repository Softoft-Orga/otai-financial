from __future__ import annotations

import unittest

from otai_forecast.compute import calculate_new_monthly_data
from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision, State


class TestProductValueBehavior(unittest.TestCase):
    def setUp(self):
        # Start from defaults and only override test-specific values
        self.a = DEFAULT_ASSUMPTIONS.model_copy(update={
            "months": 1,
            "starting_cash": 100_000.0,
            "base_organic_users_per_month": 2_000.0,
            "conv_web_to_lead": 0.03,
            "conv_website_lead_to_free": 0.20,
            "conv_website_lead_to_pro": 0.03,
            "conv_website_lead_to_ent": 0.002,
            "direct_contacted_demo_conversion": 0.08,
            "direct_demo_appointment_conversion_to_free": 0.20,
            "direct_demo_appointment_conversion_to_pro": 0.10,
            "direct_demo_appointment_conversion_to_ent": 0.01,
            "conv_free_to_pro": 0.08,
            "conv_pro_to_ent": 0.02,
            "churn_free": 0.15,
            "churn_pro": 0.03,
            "churn_ent": 0.01,
            "qualified_pool_total": 20_000.0,
            "credit_draw_factor": 0.0,
            "debt_repay_factor": 0.0,
        })
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
            qualified_pool_remaining=self.a.qualified_pool_total,
            website_leads=0.0,
            direct_demo_appointments=0.0,
            revenue_history=(),
        )

    def test_higher_dev_spend_improves_product_value(self):
        low = MonthlyDecision(
            ads_budget=0.0,
            seo_budget=0.0,
            dev_budget=0.0,
            partner_budget=0.0,
            outreach_budget=0.0,
        )
        high = MonthlyDecision(
            ads_budget=0.0,
            seo_budget=0.0,
            dev_budget=10000.0,
            partner_budget=0.0,
            outreach_budget=0.0,
        )

        m_low = calculate_new_monthly_data(self.state, self.a, low)
        m_high = calculate_new_monthly_data(self.state, self.a, high)

        self.assertGreaterEqual(m_high.product_value_next, m_low.product_value_next)

    def test_effective_rates_are_bounded(self):
        d = MonthlyDecision(
            ads_budget=1000.0,
            seo_budget=1000.0,
            dev_budget=0.0,
            partner_budget=0.0,
            outreach_budget=0.0,
        )
        m = calculate_new_monthly_data(self.state, self.a, d)
        self.assertGreaterEqual(m.conv_web_to_lead_eff, 0.0)
        self.assertLessEqual(m.conv_web_to_lead_eff, 1.0)
        self.assertLessEqual(m.churn_pro_eff, 1.0)


if __name__ == "__main__":
    unittest.main()
