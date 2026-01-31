import unittest

from otai_forecast.models import (
    Assumptions,
    Feature,
    Policy,
    PolicyParams,
    Roadmap,
    State,
)
from otai_forecast.simulator import BaseSimulator, DetailedSimulator, Simulator


class TestBaseSimulator(unittest.TestCase):
    def setUp(self):
        self.a = Assumptions(
            months=12,
            dev_day_cost_eur=500.0,
            starting_cash_eur=100000.0,
            fixed_overhead_eur_per_month=10000.0,
            cpc_eur=2.0,
            base_organic_users_per_month=1000.0,
            seo_eff_users_per_eur=1.0,
            seo_growth_per_month=0.05,
            seo_decay_per_month=0.02,
            conv_web_to_lead=0.05,
            conv_lead_to_free=0.25,
            conv_free_to_pro=0.10,
            conv_pro_to_ent=0.02,
            churn_free=0.15,
            churn_pro=0.03,
            churn_ent=0.01,
            hq_share_website_leads=0.5,
            hq_mult_lead_to_free=1.3,
            hq_mult_free_to_pro=1.5,
            hq_mult_pro_to_ent=1.2,
            lq_mult_lead_to_free=0.7,
            lq_mult_free_to_pro=0.6,
            lq_mult_pro_to_ent=0.8,
            referral_leads_per_active_free=0.01,
            partner_commission_rate=0.20,
            pro_deals_per_partner_per_month=0.02,
            ent_deals_per_partner_per_month=0.002,
            new_partners_base_per_month=0.1,
            market_dach_scale=1.0,
            market_global_scale=1.0,
            market_friction_strength=1.0,
        )

        self.policy = Policy(
            p=PolicyParams(
                ads_start=500.0,
                ads_growth=0.0,
                ads_cap=500.0,
                social_baseline=150.0,
                additional_dev_days=5.0,
                pro_price=3500.0,
                ent_price=20000.0,
            ),
        )

        self.roadmap = Roadmap(features=[])

        self.simulator = BaseSimulator(
            a=self.a,
            roadmap=self.roadmap,
            policy=self.policy,
        )

    def test_create_initial_state(self):
        state = self.simulator._create_initial_state()

        self.assertEqual(state.t, 0)
        self.assertEqual(state.cash, 100000.0)
        self.assertEqual(state.free_active, 0.0)
        self.assertEqual(state.pro_active, 0.0)
        self.assertEqual(state.ent_active, 0.0)
        self.assertEqual(state.partners, 0.0)


class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.a = Assumptions(
            months=3,
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

        self.policy = Policy(
            p=PolicyParams(
                ads_start=500.0,
                ads_growth=0.0,
                ads_cap=500.0,
                social_baseline=150.0,
                additional_dev_days=5.0,
                pro_price=3500.0,
                ent_price=20000.0,
            ),
        )

        self.roadmap = Roadmap(features=[])

        self.simulator = Simulator(
            a=self.a,
            roadmap=self.roadmap,
            policy=self.policy,
        )

    def test_step(self):
        state = State(
            t=0,
            cash=100000.0,
            free_active=50.0,
            pro_active=20.0,
            ent_active=5.0,
            partners=10.0,
        )

        dev_progress = [0.0] * len(self.roadmap.features)
        new_state, row, new_dev_progress = self.simulator.step(state, dev_progress)

        # Check that time advanced
        self.assertEqual(new_state.t, 1)
        self.assertEqual(row.t, 0)

        # Check that values are updated
        self.assertGreaterEqual(
            new_state.cash, state.cash
        )  # Should be profitable or break-even

        # Check row structure
        self.assertIsNotNone(row.cash)
        self.assertIsNotNone(row.leads)
        self.assertIsNotNone(row.free_active)
        self.assertIsNotNone(row.pro_active)
        self.assertIsNotNone(row.ent_active)
        self.assertIsNotNone(row.partners)
        self.assertIsNotNone(row.revenue_total)
        self.assertIsNotNone(row.net_cashflow)

    def test_run(self):
        rows = self.simulator.run()

        # Should have 3 rows for 3 months
        self.assertEqual(len(rows), 3)

        # Check first row
        self.assertEqual(rows[0].t, 0)
        self.assertEqual(rows[1].t, 1)
        self.assertEqual(rows[2].t, 2)

        # Check that cash changes over time
        cash_values = [r.cash for r in rows]
        self.assertNotEqual(cash_values[0], cash_values[-1])

    def test_run_with_feature(self):
        # Add a feature that launches at month 1
        from otai_forecast.effects import effect_boost_free_to_pro

        feature = Feature(
            name="test_feature",
            dev_days=10.0,
            maintenance_days_per_month=2.0,
            launch_t=1,
            effect=effect_boost_free_to_pro(0.5),  # Real effect function
        )

        roadmap_with_feature = Roadmap(features=[feature])
        simulator_with_feature = Simulator(
            a=self.a,
            roadmap=roadmap_with_feature,
            policy=self.policy,
        )

        rows = simulator_with_feature.run()

        # Check that we got results
        self.assertEqual(len(rows), 3)
        # Feature should be active from month 1 onwards
        self.assertGreater(rows[1].free_active, rows[0].free_active)


class TestDetailedSimulator(unittest.TestCase):
    def setUp(self):
        self.a = Assumptions(
            months=3,
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

        self.policy = Policy(
            p=PolicyParams(
                ads_start=500.0,
                ads_growth=0.0,
                ads_cap=500.0,
                social_baseline=150.0,
                additional_dev_days=5.0,
                pro_price=3500.0,
                ent_price=20000.0,
            ),
        )

        self.roadmap = Roadmap(features=[])

        self.simulator = DetailedSimulator(
            a=self.a,
            roadmap=self.roadmap,
            policy=self.policy,
        )

    def test_run(self):
        data_log = self.simulator.run()

        # Should have 3 rows for 3 months
        self.assertEqual(len(data_log), 3)

        # Check first row structure
        row = data_log[0]

        # Check that all expected keys are present
        expected_keys = [
            "month",
            "cash",
            "ads_spend",
            "social_spend",
            "leads",
            "free_active",
            "pro_active",
            "ent_active",
            "partners",
            "revenue",
            "cost_ads",
            "cost_social",
            "cost_ops",
            "cost_dev_maint",
            "cost_dev_feat",
            "cost_partners",
            "total_costs",
            "net_cashflow",
        ]

        for key in expected_keys:
            self.assertIn(key, row)

        # Check month values
        self.assertEqual(data_log[0]["month"], 0)
        self.assertEqual(data_log[1]["month"], 1)
        self.assertEqual(data_log[2]["month"], 2)

        # Check that values are reasonable
        self.assertGreater(row["website_users"], 0)
        self.assertGreaterEqual(row["leads_total"], 0)
        self.assertGreaterEqual(row["revenue"], 0)
        self.assertIsInstance(row["net_cashflow"], (int, float))


class TestRowsToDicts(unittest.TestCase):
    def test_rows_to_dicts(self):
        from otai_forecast.models import Row
        from otai_forecast.simulator import rows_to_dicts

        rows = [
            Row(
                t=0,
                cash=100000.0,
                debt=0.0,
                leads=50.0,
                free_active=20.0,
                pro_active=5.0,
                ent_active=1.0,
                partners=2.0,
                revenue_total=50000.0,
                net_cashflow=10000.0,
            ),
            Row(
                t=1,
                cash=110000.0,
                debt=0.0,
                leads=60.0,
                free_active=25.0,
                pro_active=7.0,
                ent_active=2.0,
                partners=2.1,
                revenue_total=60000.0,
                net_cashflow=15000.0,
            ),
        ]

        dicts = rows_to_dicts(rows)

        self.assertEqual(len(dicts), 2)
        self.assertEqual(dicts[0]["t"], 0)
        self.assertEqual(dicts[0]["cash"], 100000.0)
        self.assertEqual(dicts[1]["t"], 1)
        self.assertEqual(dicts[1]["cash"], 110000.0)


if __name__ == "__main__":
    unittest.main()
