import unittest
from dataclasses import replace

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision
from otai_forecast.simulator import Simulator


class TestSimulator(unittest.TestCase):
    def setUp(self):
        # Start from defaults and only override test-specific values
        self.a = replace(
            DEFAULT_ASSUMPTIONS,
            months=3,
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

        self.decisions = [
            MonthlyDecision(
                ads_spend=500.0,
                seo_spend=300.0,
                social_spend=150.0,
                dev_spend=5000.0,
                partner_spend=0.0,
                direct_candidate_outreach_spend=0.0,
            )
            for _ in range(self.a.months)
        ]

        self.simulator = Simulator(a=self.a, decisions=self.decisions)

    def test_run(self):
        rows = self.simulator.run()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0].month, 0)
        self.assertEqual(rows[1].month, 1)
        self.assertEqual(rows[2].month, 2)

        rows_dict = self.simulator.run_rows()
        self.assertEqual(len(rows_dict), 3)
        self.assertIn("cash", rows_dict[0])
        self.assertIn("month", rows_dict[0])
        self.assertIn("revenue_total", rows_dict[0])


if __name__ == "__main__":
    unittest.main()
