from __future__ import annotations

import unittest

from otai_forecast.compute import (
    calculate_new_monthly_data,
    calculate_new_state,
    clamp,
    run_simulation_rows,
)
from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision, State


class TestCompute(unittest.TestCase):
    def setUp(self):
        # Start from defaults and only override test-specific values
        self.a = DEFAULT_ASSUMPTIONS.model_copy(update={
            "months": 3,
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
            "churn_pro_floor": 0.01,
            "qualified_pool_total": 20_000.0,
            "credit_draw_factor": 0.0,
            "debt_repay_factor": 0.0,
        })

        self.decision = MonthlyDecision(
            ads_budget=500.0,
            seo_budget=300.0,
            dev_budget=5000.0,
            partner_budget=0.0,
            outreach_budget=0.0,
        )
        self.d = self.decision  # Add alias for compatibility

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

    def test_clamp(self):
        self.assertEqual(clamp(-1.0, 0.0, 1.0), 0.0)
        self.assertEqual(clamp(2.0, 0.0, 1.0), 1.0)
        self.assertEqual(clamp(0.5, 0.0, 1.0), 0.5)
        self.assertEqual(clamp(10.0, 5.0, 15.0), 10.0)

    def test_calculate_new_monthly_data_smoke(self):
        monthly = calculate_new_monthly_data(self.state, self.a, self.d)
        self.assertEqual(monthly.month, 0)
        self.assertGreaterEqual(monthly.website_users, 0.0)
        self.assertGreaterEqual(monthly.leads_total, 0.0)
        self.assertGreaterEqual(monthly.costs_ex_tax, 0.0)

    def test_state_progression_matches_rows(self):
        rows = run_simulation_rows(self.a, [self.d] * self.a.months)
        self.assertEqual(len(rows), self.a.months)

        # Cash in row i is end-of-month cash after applying that month's cashflow
        cash = self.a.starting_cash
        for r in rows:
            cash += r["net_cashflow"] + r["new_credit_draw"] - r["debt_repayment"]
            self.assertAlmostEqual(r["cash"], cash, places=6)

    def test_calculate_new_state_advances_month(self):
        monthly = calculate_new_monthly_data(self.state, self.a, self.d)
        next_state = calculate_new_state(self.state, monthly, self.a)
        self.assertEqual(next_state.month, 1)


if __name__ == "__main__":
    unittest.main()
