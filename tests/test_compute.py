import unittest

from otai_forecast.compute import (
    calculate_new_monthly_data,
    calculate_new_state,
    clamp,
    run_simulation_rows,
)
from otai_forecast.models import Assumptions, MonthlyDecision, State


class TestCompute(unittest.TestCase):
    def setUp(self):
        self.a = Assumptions(
            months=3,
            starting_cash=100_000.0,
            base_organic_users_per_month=2_000.0,
            cpc_eur=2.5,
            cpc_base=2.5,
            cpc_k=0.15,
            cpc_ref_spend=1000.0,
            seo_eff_users_per_eur=0.8,
            seo_decay=0.08,
            domain_rating_init=10.0,
            domain_rating_max=100.0,
            domain_rating_growth_k=0.06,
            domain_rating_growth_ref_spend=1000.0,
            domain_rating_decay=0.02,
            conv_web_to_lead=0.03,
            conv_lead_to_free=0.25,
            conv_free_to_pro=0.08,
            conv_pro_to_ent=0.02,
            churn_free=0.15,
            churn_pro=0.03,
            churn_ent=0.01,
            churn_pro_floor=0.01,
            pro_price_base=3500.0,
            ent_price_base=20000.0,
            pro_price_k=0.05,
            ent_price_k=0.03,
            tax_rate=0.25,
            market_cap_multiple=6.0,
            sales_cost_per_new_pro=300.0,
            sales_cost_per_new_ent=1500.0,
            support_cost_per_pro=50.0,
            support_cost_per_ent=400.0,
            operating_baseline=2000.0,
            operating_per_user=3.0,
            operating_per_dev=0.15,
            qualified_pool_total=20_000.0,
            contact_rate_per_month=0.01,
            scraping_efficiency_k=0.5,
            scraping_ref_spend=500.0,
            credit_cash_threshold=0.0,
            credit_draw_amount=0.0,
            debt_interest_rate_base_annual=0.10,
            debt_interest_rate_k=0.05,
            debt_interest_rate_ref=100_000.0,
            pv_init=100.0,
            pv_min=30.0,
            pv_ref=100.0,
            pv_decay_shape=0.08,
            pv_growth_scale=0.15,
            k_pv_web_to_lead=0.30,
            k_pv_lead_to_free=0.15,
            k_pv_free_to_pro=0.25,
            k_pv_pro_to_ent=0.20,
            k_pv_churn_pro=0.20,
            k_pv_churn_free=0.10,
            k_pv_churn_ent=0.15,
        )

        self.d = MonthlyDecision(
            ads_spend=500.0,
            seo_spend=300.0,
            social_spend=150.0,
            dev_spend=5000.0,
            scraping_spend=0.0,
            outreach_intensity=0.25,
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
            cash += r["net_cashflow"]
            self.assertAlmostEqual(r["cash"], cash, places=6)

    def test_calculate_new_state_advances_month(self):
        monthly = calculate_new_monthly_data(self.state, self.a, self.d)
        next_state = calculate_new_state(self.state, monthly, self.a)
        self.assertEqual(next_state.month, 1)


if __name__ == "__main__":
    unittest.main()
