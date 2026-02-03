from __future__ import annotations

import unittest
from otai_forecast.compute import (
    calculate_new_monthly_data,
    _effective_cpc,
    _update_domain_rating,
)
from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import MonthlyDecision, State


class TestAssumptionsValidation(unittest.TestCase):
    """Test that assumptions produce sensible values in calculations."""

    def setUp(self):
        self.a = DEFAULT_ASSUMPTIONS.model_copy(
            update={"credit_draw_factor": 0.0, "debt_repay_factor": 0.0}
        )
        self.state = State(
            month=0,
            cash=self.a.starting_cash,
            debt=0.0,
            domain_rating=self.a.domain_rating_init,
            product_value=self.a.pv_init,
            free_active=100.0,
            pro_active=50.0,
            ent_active=10.0,
            partners_active=5.0,
            qualified_pool_remaining=self.a.qualified_pool_total,
            website_leads=120.0,
            direct_demo_appointments=30.0,
            revenue_history=(10_000.0,) * 12,
        )
        self.decision = MonthlyDecision(
            ads_budget=1000.0,
            seo_budget=1500.0,
            dev_budget=5000.0,
            partner_budget=200.0,
            outreach_budget=2000.0,
        )

    def test_cpc_calculation_sensible_ranges(self):
        """Test that CPC calculations produce sensible values."""
        # Test zero spend
        cpc_zero = _effective_cpc(0.0, self.a)
        self.assertEqual(cpc_zero, self.a.cpc_base)
        self.assertGreaterEqual(cpc_zero, 0.5)  # Should be at least 0.5 EUR
        self.assertLessEqual(cpc_zero, 10.0)   # Should not exceed 10 EUR

        # Test low spend
        cpc_low = _effective_cpc(100.0, self.a)
        self.assertGreater(cpc_low, self.a.cpc_base)
        self.assertLess(cpc_low, self.a.cpc_base * 2.0)

        # Test high spend
        cpc_high = _effective_cpc(10000.0, self.a)
        self.assertGreater(cpc_high, self.a.cpc_base)
        self.assertLess(cpc_high, 20.0)  # Should not exceed 20 EUR even at high spend

        # Test CPC increases with spend (diminishing returns)
        cpc_1000 = _effective_cpc(1000.0, self.a)
        cpc_2000 = _effective_cpc(2000.0, self.a)
        cpc_4000 = _effective_cpc(4000.0, self.a)
        
        self.assertLess(cpc_2000 - cpc_1000, cpc_4000 - cpc_2000)  # Diminishing returns

    def test_seo_lead_calculation_sensible(self):
        """Test that SEO spend produces sensible lead numbers."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # SEO users should be proportional to spend
        seo_users_expected = self.decision.seo_budget * self.a.seo_users_per_eur
        seo_users_actual = monthly.website_users - (
            self.a.base_organic_users_per_month * (1.0 + self.state.domain_rating / self.a.domain_rating_max) +
            (self.decision.ads_budget / _effective_cpc(self.decision.ads_budget, self.a) if self.decision.ads_budget > 0 else 0.0)
        )
        
        # Account for domain rating multiplier
        seo_mult = 1.0 + (self.state.domain_rating / self.a.domain_rating_max)
        
        self.assertGreater(seo_users_actual, 0)
        self.assertLess(abs(seo_users_actual - seo_users_expected * seo_mult) / seo_users_expected, 0.1)  # Within 10%

    def test_domain_rating_growth_sensible(self):
        """Test that domain rating growth follows sensible patterns."""
        # Test with no SEO spend
        decision_no_spend = self.decision.model_copy(update={"seo_budget": 0.0})
        dr_next = _update_domain_rating(self.state, self.a, decision_no_spend)
        
        # Should decay due to natural decay
        expected_dr = self.state.domain_rating * (1.0 - self.a.domain_rating_decay)
        self.assertAlmostEqual(dr_next, expected_dr, places=6)
        
        # Test with moderate SEO spend
        dr_next_spend = _update_domain_rating(self.state, self.a, self.decision)
        self.assertGreater(dr_next_spend, dr_next)  # Should grow with spend
        self.assertLessEqual(dr_next_spend, self.a.domain_rating_max)  # Should not exceed max
        
        # Test with very high SEO spend
        decision_high_spend = self.decision.model_copy(update={"seo_budget": 10000.0})
        dr_next_high = _update_domain_rating(self.state, self.a, decision_high_spend)
        self.assertGreater(dr_next_high, dr_next_spend)  # Should grow more
        self.assertLessEqual(dr_next_high, self.a.domain_rating_max)  # Still capped at max

    def test_conversion_rates_sensible(self):
        """Test that conversion rates are within sensible bounds."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Website users to leads
        self.assertGreaterEqual(monthly.website_leads, 0)
        self.assertLessEqual(monthly.website_leads, monthly.website_users)
        
        # Check that conversion rates are reasonable
        if monthly.website_users > 0:
            web_to_lead_rate = monthly.website_leads / monthly.website_users
            self.assertLessEqual(web_to_lead_rate, 0.1)  # Should not exceed 10%
            
        # Check funnel progression (available leads -> free/pro/ent)
        available_leads = (
            monthly.website_leads_available + monthly.direct_demo_appointments_available
        )
        self.assertLessEqual(monthly.new_free, available_leads)
        self.assertLessEqual(monthly.new_pro, available_leads)
        self.assertLessEqual(monthly.new_ent, available_leads)
        
        # Pro conversions should be less than free conversions
        self.assertLessEqual(monthly.new_pro, monthly.new_free)
        # Ent conversions should be less than pro conversions
        self.assertLessEqual(monthly.new_ent, monthly.new_pro)

    def test_revenue_calculations_sensible(self):
        """Test that revenue calculations are sensible."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Revenue should be positive
        self.assertGreaterEqual(monthly.revenue_total, 0)
        
        # Revenue should match sum of components
        revenue_sum = (
            monthly.revenue_pro + 
            monthly.revenue_ent + 
            monthly.monthly_renewal_fee + 
            monthly.support_subscription_revenue_total
        )
        self.assertAlmostEqual(monthly.revenue_total, revenue_sum, places=6)
        
        # Enterprise revenue per customer should be higher than pro
        if monthly.new_ent > 0 and monthly.new_pro > 0:
            ent_revenue_per_customer = monthly.revenue_ent / monthly.new_ent
            pro_revenue_per_customer = monthly.revenue_pro / monthly.new_pro
            self.assertGreater(ent_revenue_per_customer, pro_revenue_per_customer)

    def test_churn_rates_sensible(self):
        """Test that churn rates are within sensible bounds."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Churn should not exceed active users
        self.assertLessEqual(monthly.churned_free, self.state.free_active)
        self.assertLessEqual(monthly.churned_pro, self.state.pro_active)
        self.assertLessEqual(monthly.churned_ent, self.state.ent_active)
        
        # Enterprise churn should be lowest
        if self.state.pro_active > 0 and self.state.ent_active > 0:
            churn_pro_rate = monthly.churned_pro / self.state.pro_active
            churn_ent_rate = monthly.churned_ent / self.state.ent_active
            self.assertLess(churn_ent_rate, churn_pro_rate)
        
        # Free churn should be highest
        if self.state.free_active > 0 and self.state.pro_active > 0:
            churn_free_rate = monthly.churned_free / self.state.free_active
            churn_pro_rate = monthly.churned_pro / self.state.pro_active
            self.assertGreater(churn_free_rate, churn_pro_rate)

    def test_product_value_pricing_sensible(self):
        """Test that pricing respects product value milestones."""
        state_low_pv = self.state.model_copy(update={"product_value": self.a.pv_min})
        monthly_low = calculate_new_monthly_data(state_low_pv, self.a, self.decision)

        state_high_pv = self.state.model_copy(update={"product_value": self.a.pv_init})
        monthly_high = calculate_new_monthly_data(state_high_pv, self.a, self.decision)

        self.assertGreaterEqual(monthly_high.pro_price, monthly_low.pro_price)
        self.assertGreaterEqual(monthly_high.ent_price, monthly_low.ent_price)

    def test_costs_sensible(self):
        """Test that costs are sensible relative to revenue and operations."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Total costs should be positive
        self.assertGreater(monthly.costs_ex_tax, 0)
        
        # Payment processing should be proportional to revenue
        expected_payment_processing = monthly.revenue_total * self.a.payment_processing_rate
        self.assertAlmostEqual(monthly.cost_payment_processing, expected_payment_processing, places=6)
        
        # Sales & marketing costs should include budget allocations
        expected_sales_marketing = (
            self.decision.ads_budget + 
            self.decision.seo_budget + 
            self.decision.partner_budget + 
            self.decision.outreach_budget + 
            monthly.sales_spend +
            monthly.cost_outreach_conversion
        )
        self.assertAlmostEqual(monthly.cost_sales_marketing, expected_sales_marketing, places=6)
        
        # Dev expense should be portion of dev budget
        expected_dev_expense = self.decision.dev_budget * (1 - self.a.dev_capex_ratio)
        self.assertAlmostEqual(monthly.cost_rd_expense, expected_dev_expense, places=6)

    def test_scraping_funnel_sensible(self):
        """Test that scraping/outreach funnel behaves sensibly."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Direct leads should not exceed what's possible from remaining pool
        self.assertLessEqual(monthly.new_direct_leads, self.state.qualified_pool_remaining)
        
        # Higher spend should find more leads (diminishing returns)
        decision_low_spend = self.decision.model_copy(update={"outreach_budget": 500.0})
        monthly_low = calculate_new_monthly_data(self.state, self.a, decision_low_spend)
        
        decision_high_spend = self.decision.model_copy(update={"outreach_budget": 5000.0})
        monthly_high = calculate_new_monthly_data(self.state, self.a, decision_high_spend)
        
        self.assertGreater(monthly_high.new_direct_leads, monthly_low.new_direct_leads)
        
        # But not linearly (diminishing returns)
        spend_ratio = 5000.0 / 500.0  # 10x spend
        leads_ratio = (
            monthly_high.new_direct_leads / monthly_low.new_direct_leads
            if monthly_low.new_direct_leads > 0
            else 1
        )
        self.assertLess(leads_ratio, spend_ratio)  # Should be less than linear

    def test_partner_program_sensible(self):
        """Test that partner program calculations are sensible."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Partner acquisition should be positive with spend
        if self.decision.partner_budget > 0:
            self.assertGreater(monthly.new_partners, 0)
        
        # Partner deals should be proportional to active partners
        # Note: Due to product value impact, actual deals may vary slightly
        expected_pro_deals = self.state.partners_active * self.a.partner_pro_deals_per_partner_per_month
        expected_ent_deals = self.state.partners_active * self.a.partner_ent_deals_per_partner_per_month
        
        # Allow for small variation due to product value effects
        self.assertAlmostEqual(monthly.partner_pro_deals, expected_pro_deals, delta=0.1)
        self.assertAlmostEqual(monthly.partner_ent_deals, expected_ent_deals, delta=0.05)
        
        # Commission cost should be proportional to deals
        expected_commission = self.a.partner_commission_rate * (
            monthly.partner_pro_deals * monthly.pro_price + 
            monthly.partner_ent_deals * monthly.ent_price
        )
        self.assertAlmostEqual(monthly.partner_commission_cost, expected_commission, places=6)

    def test_debt_interest_sensible(self):
        """Test that debt interest calculations are sensible."""
        # Test with no debt
        state_no_debt = self.state.model_copy(update={"debt": 0.0})
        monthly_no_debt = calculate_new_monthly_data(state_no_debt, self.a, self.decision)
        self.assertEqual(monthly_no_debt.interest_payment, 0.0)
        
        # Test with debt
        state_with_debt = self.state.model_copy(
            update={"debt": 50000.0, "revenue_history": ()}
        )
        monthly_with_debt = calculate_new_monthly_data(state_with_debt, self.a, self.decision)
        
        # Interest should be positive
        self.assertGreater(monthly_with_debt.interest_payment, 0.0)
        
        # Interest rate should match base when no revenue history is available
        annual_rate = monthly_with_debt.interest_rate_annual_eff
        self.assertAlmostEqual(
            annual_rate, self.a.debt_interest_rate_base_annual, places=6
        )

    def test_cash_flow_sensible(self):
        """Test that cash flow calculations are sensible."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Net cash flow = profit before tax - tax
        expected_net_cashflow = monthly.profit_bt - monthly.tax
        self.assertAlmostEqual(monthly.net_cashflow, expected_net_cashflow, places=6)
        
        # With typical assumptions, might be negative initially (growth stage)
        # But should not be extremely negative relative to spend
        total_spend = (
            self.decision.ads_budget + 
            self.decision.seo_budget + 
            self.decision.dev_budget + 
            self.decision.partner_budget + 
            self.decision.outreach_budget
        )
        self.assertGreater(monthly.net_cashflow, -total_spend * 2.0)  # Should not lose more than 2x spend

    def test_boundary_conditions(self):
        """Test calculations at boundary conditions."""
        # Test with zero budgets
        decision_zero = MonthlyDecision(
            ads_budget=0.0,
            seo_budget=0.0,
            dev_budget=0.0,
            partner_budget=0.0,
            outreach_budget=0.0,
        )
        monthly_zero = calculate_new_monthly_data(self.state, self.a, decision_zero)
        
        # Should still have some organic users
        self.assertGreater(monthly_zero.website_users, 0)
        self.assertGreaterEqual(monthly_zero.website_users, self.a.base_organic_users_per_month)
        
        # Test with very high budgets
        decision_high = MonthlyDecision(
            ads_budget=100000.0,
            seo_budget=100000.0,
            dev_budget=100000.0,
            partner_budget=100000.0,
            outreach_budget=100000.0,
        )
        monthly_high = calculate_new_monthly_data(self.state, self.a, decision_high)
        
        # Values should be high but not infinite
        self.assertLess(monthly_high.website_users, 10000000.0)  # Reasonable upper bound
        self.assertLess(monthly_high.revenue_total, 100000000.0)  # Reasonable upper bound


if __name__ == "__main__":
    unittest.main()
