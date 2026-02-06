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

    def test_cpc_calculation_strict_bounds(self):
        """Test that CPC calculations are within strict realistic bounds."""
        # Test zero spend
        cpc_zero = _effective_cpc(0.0, self.a)
        self.assertGreaterEqual(cpc_zero, 0.5)  # Minimum realistic CPC
        self.assertLessEqual(cpc_zero, 5.0)     # Maximum at zero spend
        
        # Test low spend (€100)
        cpc_low = _effective_cpc(100.0, self.a)
        self.assertGreater(cpc_low, 0.5)
        self.assertLess(cpc_low, 7.0)
        
        # Test medium spend (€5,000)
        cpc_medium = _effective_cpc(5000.0, self.a)
        self.assertGreater(cpc_medium, 1.0)
        self.assertLess(cpc_medium, 15.0)
        
        # Test high spend (€50,000)
        cpc_high = _effective_cpc(50000.0, self.a)
        self.assertGreater(cpc_high, 2.0)
        self.assertLess(cpc_high, 30.0)  # Still reasonable for B2B
        
        # Test extreme spend (€500,000)
        cpc_extreme = _effective_cpc(500000.0, self.a)
        self.assertGreater(cpc_extreme, 5.0)
        self.assertLess(cpc_extreme, 50.0)  # Upper bound for sanity
        
        # CPC should never exceed €100 even at extreme spend
        self.assertLess(cpc_extreme, 100.0)
        
        # Test diminishing returns
        cpc_1k = _effective_cpc(1000.0, self.a)
        cpc_10k = _effective_cpc(10000.0, self.a)
        cpc_100k = _effective_cpc(100000.0, self.a)
        
        # Each 10x increase should less than 10x CPC increase
        self.assertLess(cpc_10k / cpc_1k, 10.0)
        self.assertLess(cpc_100k / cpc_10k, 10.0)

    def test_seo_metrics_strict_bounds(self):
        """Test that SEO metrics are within realistic bounds."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # SEO users should be reasonable relative to spend
        seo_users_per_eur = self.a.seo_users_per_eur
        self.assertGreater(seo_users_per_eur, 0.01)  # At least 1 user per €100
        self.assertLess(seo_users_per_eur, 10.0)     # Not more than 10 users per €1
        
        # Domain rating should be within bounds
        self.assertGreaterEqual(monthly.domain_rating_next, 0.0)
        self.assertLessEqual(monthly.domain_rating_next, self.a.domain_rating_max)
        
        # Domain rating should not jump too much in one month
        max_monthly_dr_growth = 5.0  # Max 5 points per month
        self.assertLessEqual(
            monthly.domain_rating_next - self.state.domain_rating,
            max_monthly_dr_growth
        )
        
        # Website users should be reasonable
        # With €1500 SEO spend and base organic, should be in thousands
        self.assertGreater(monthly.website_users, 50)   # At least base organic
        self.assertLess(monthly.website_users, 100000)  # Not insane high

    def test_conversion_rates_strict_bounds(self):
        """Test that all conversion rates are within strict realistic bounds."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Web-to-lead conversion (typical B2B: 1-5%)
        self.assertGreaterEqual(monthly.conv_web_to_lead_eff, 0.001)  # Min 0.1%
        self.assertLessEqual(monthly.conv_web_to_lead_eff, 0.10)      # Max 10%
        
        # Lead-to-free conversion (typical: 5-20%)
        self.assertGreaterEqual(monthly.conv_website_lead_to_free_eff, 0.01)  # Min 1%
        self.assertLessEqual(monthly.conv_website_lead_to_free_eff, 0.40)     # Max 40%
        
        # Lead-to-pro conversion (typical: 0.5-3%)
        self.assertGreaterEqual(monthly.conv_website_lead_to_pro_eff, 0.001)  # Min 0.1%
        self.assertLessEqual(monthly.conv_website_lead_to_pro_eff, 0.05)      # Max 5%
        
        # Lead-to-enterprise conversion (typical: 0.05-0.5%)
        self.assertGreaterEqual(monthly.conv_website_lead_to_ent_eff, 0.0001)  # Min 0.01%
        self.assertLessEqual(monthly.conv_website_lead_to_ent_eff, 0.01)       # Max 1%
        
        # Free-to-pro upgrade (typical: 1-5%)
        self.assertGreaterEqual(monthly.upgrade_free_to_pro_eff, 0.001)  # Min 0.1%
        self.assertLessEqual(monthly.upgrade_free_to_pro_eff, 0.10)      # Max 10%
        
        # Pro-to-enterprise upgrade (typical: 0.1-1%)
        self.assertGreaterEqual(monthly.upgrade_pro_to_ent_eff, 0.0001)  # Min 0.01%
        self.assertLessEqual(monthly.upgrade_pro_to_ent_eff, 0.02)       # Max 2%
        
        # Demo-to-pro conversion should stay within realistic bounds
        self.assertLessEqual(
            monthly.direct_demo_appointment_conversion_to_pro_eff,
            0.5,
        )

    def test_churn_rates_strict_bounds(self):
        """Test that churn rates are within strict realistic bounds."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Free user churn (high: 15-30% monthly)
        self.assertGreaterEqual(monthly.churn_free_eff, 0.05)  # Min 5%
        self.assertLessEqual(monthly.churn_free_eff, 0.50)     # Max 50%
        
        # Pro user churn (medium: 2-8% monthly)
        self.assertGreaterEqual(monthly.churn_pro_eff, 0.005)  # Min 0.5%
        self.assertLessEqual(monthly.churn_pro_eff, 0.15)      # Max 15%
        
        # Enterprise churn (low: 0.5-3% monthly)
        self.assertGreaterEqual(monthly.churn_ent_eff, 0.001)  # Min 0.1%
        self.assertLessEqual(monthly.churn_ent_eff, 0.05)      # Max 5%
        
        # Churn hierarchy: free > pro > enterprise
        self.assertGreater(monthly.churn_free_eff, monthly.churn_pro_eff)
        self.assertGreater(monthly.churn_pro_eff, monthly.churn_ent_eff)
        
        # Pro churn should respect floor

    def test_pricing_strict_bounds(self):
        """Test that pricing is within realistic bounds."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Pro pricing should be reasonable for B2B SaaS
        self.assertGreater(monthly.pro_price, 100)      # Min €100
        self.assertLess(monthly.pro_price, 50000)       # Max €50k
        
        # Enterprise pricing should be higher than pro
        self.assertGreater(monthly.ent_price, monthly.pro_price)
        self.assertLess(monthly.ent_price, 500000)       # Max €500k
        
        # Price ratio should be reasonable (typically 3-10x)
        price_ratio = monthly.ent_price / monthly.pro_price
        self.assertGreater(price_ratio, 1.5)   # Min 1.5x
        self.assertLess(price_ratio, 20.0)     # Max 20x
        
        # Renewal rates should stay within bounds
        self.assertGreaterEqual(monthly.renewal_upgrade_rate, 0.0)
        self.assertLessEqual(monthly.renewal_upgrade_rate, 1.0)
        self.assertGreaterEqual(monthly.renewal_discount_rate, 0.0)
        self.assertLessEqual(monthly.renewal_discount_rate, 1.0)

    def test_user_acquisition_strict_bounds(self):
        """Test that user acquisition numbers are realistic."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # New users should be positive and reasonable
        self.assertGreaterEqual(monthly.new_free, 0)
        self.assertGreaterEqual(monthly.new_pro, 0)
        self.assertGreaterEqual(monthly.new_ent, 0)
        
        # With given spend and conversion rates, should acquire some users
        self.assertGreater(monthly.new_free, 0.1)  # At least some free users
        
        # Funnel ratios should make sense
        if monthly.new_free > 0:
            self.assertLessEqual(monthly.new_pro, monthly.new_free)  # Pro <= Free
            self.assertLessEqual(monthly.new_ent, monthly.new_pro)   # Ent <= Pro
        
        # Conversion efficiency should be reasonable
        if monthly.leads_total > 0:
            total_conversion_rate = (monthly.new_free + monthly.new_pro + monthly.new_ent) / monthly.leads_total
            self.assertLessEqual(total_conversion_rate, 0.5)  # Max 50% total conversion
        
        # Should not acquire more enterprise than pro in typical B2B
        if monthly.new_pro > 0:
            self.assertLessEqual(monthly.new_ent, monthly.new_pro * 0.5)  # Enterprise <= 50% of Pro

    def test_revenue_strict_bounds(self):
        """Test that revenue calculations are realistic."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Revenue should be positive
        self.assertGreaterEqual(monthly.revenue_total, 0)
        
        # Revenue per customer should be reasonable
        if monthly.new_pro > 0:
            revenue_per_pro = monthly.revenue_pro / monthly.new_pro
            self.assertGreater(revenue_per_pro, 100)    # Min €100
            self.assertLess(revenue_per_pro, 100000)    # Max €100k
        
        if monthly.new_ent > 0:
            revenue_per_ent = monthly.revenue_ent / monthly.new_ent
            self.assertGreater(revenue_per_ent, 1000)   # Min €1k
            self.assertLess(revenue_per_ent, 1000000)   # Max €1M
        
        # Revenue composition should make sense
        self.assertAlmostEqual(
            monthly.revenue_total,
            monthly.revenue_pro + monthly.revenue_ent + monthly.monthly_renewal_fee + monthly.support_subscription_revenue_total,
            places=6
        )
        
        # Revenue should not be insanely high relative to spend
        total_spend = (
            self.decision.ads_budget + self.decision.seo_budget + 
            self.decision.dev_budget + self.decision.partner_budget + 
            self.decision.outreach_budget
        )
        # Revenue could be high due to one-time licenses, but not absurdly high
        self.assertLess(monthly.revenue_total, total_spend * 1000)  # Max 1000x spend

    def test_costs_strict_bounds(self):
        """Test that costs are within realistic bounds."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Cost components should be positive
        self.assertGreaterEqual(monthly.costs_ex_tax, 0)
        self.assertGreaterEqual(monthly.cost_of_goods_sold, 0)
        self.assertGreaterEqual(monthly.operating_expenses, 0)
        
        # COGS should be reasonable percentage of revenue
        if monthly.revenue_total > 0:
            cogs_ratio = monthly.cost_of_goods_sold / monthly.revenue_total
            self.assertLessEqual(cogs_ratio, 0.30)  # Max 30% for SaaS
        
        # Payment processing should be exactly 2% of revenue
        expected_payment_processing = monthly.revenue_total * self.a.payment_processing_rate
        self.assertAlmostEqual(monthly.cost_payment_processing, expected_payment_processing, places=6)
        
        # Sales costs should be reasonable per customer
        if monthly.new_pro > 0:
            sales_cost_per_pro = monthly.sales_spend / monthly.new_pro
            self.assertGreater(sales_cost_per_pro, 50)    # Min €50
            self.assertLess(sales_cost_per_pro, 10000)    # Max €10k
        
        # Support costs should be reasonable per active user
        if self.state.pro_active > 0:
            support_cost_per_pro = monthly.support_spend / self.state.pro_active
            self.assertGreater(support_cost_per_pro, 5)     # Min €5
            self.assertLess(support_cost_per_pro, 500)      # Max €500

    def test_partner_program_strict_bounds(self):
        """Test that partner program metrics are realistic."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Partner acquisition should be reasonable
        self.assertGreaterEqual(monthly.new_partners, 0)
        if self.decision.partner_budget > 0:
            # With €200 spend, should get some partners but not too many
            self.assertLess(monthly.new_partners, 10)  # Max 10 new partners with €200
        
        # Partner deals should be reasonable per partner
        if self.state.partners_active > 0:
            deals_per_partner_pro = monthly.partner_pro_deals / self.state.partners_active
            deals_per_partner_ent = monthly.partner_ent_deals / self.state.partners_active
            
            # Should match assumptions closely
            self.assertAlmostEqual(
                deals_per_partner_pro, 
                self.a.partner_pro_deals_per_partner_per_month,
                delta=0.1
            )
            self.assertAlmostEqual(
                deals_per_partner_ent,
                self.a.partner_ent_deals_per_partner_per_month,
                delta=0.05
            )
        
        # Commission should be reasonable percentage of partner revenue
        partner_revenue = monthly.partner_pro_deals * monthly.pro_price + monthly.partner_ent_deals * monthly.ent_price
        if partner_revenue > 0:
            commission_rate = monthly.partner_commission_cost / partner_revenue
            self.assertAlmostEqual(commission_rate, self.a.partner_commission_rate, places=6)

    def test_debt_interest_strict_bounds(self):
        """Test that debt interest is within realistic bounds."""
        # Test with no debt
        state_no_debt = self.state.model_copy(update={"debt": 0.0})
        monthly_no_debt = calculate_new_monthly_data(state_no_debt, self.a, self.decision)
        self.assertEqual(monthly_no_debt.interest_payment, 0.0)
        
        # Test with moderate debt (€50k) and no revenue history
        state_mod_debt = self.state.model_copy(
            update={"debt": 50000.0, "revenue_history": ()}
        )
        monthly_mod_debt = calculate_new_monthly_data(state_mod_debt, self.a, self.decision)
        
        # Interest rate should match base when revenue history is empty
        self.assertAlmostEqual(
            monthly_mod_debt.interest_rate_annual_eff,
            self.a.debt_interest_rate_base_annual,
            places=6,
        )
        
        # Test with high debt (€500k) and no revenue history
        state_high_debt = self.state.model_copy(
            update={"debt": 500000.0, "revenue_history": ()}
        )
        monthly_high_debt = calculate_new_monthly_data(state_high_debt, self.a, self.decision)
        
        self.assertAlmostEqual(
            monthly_high_debt.interest_rate_annual_eff,
            self.a.debt_interest_rate_base_annual,
            places=6,
        )

    def test_scraping_funnel_strict_bounds(self):
        """Test that scraping/outreach funnel is realistic."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Should not find more leads than exist in pool
        self.assertLessEqual(monthly.new_direct_leads, self.state.qualified_pool_remaining)
        
        # With €2000 spend, should find some prospects but not all
        self.assertGreater(monthly.new_direct_leads, 0)
        self.assertLess(
            monthly.new_direct_leads, self.state.qualified_pool_remaining * 0.5
        )  # Max 50% of pool
        
        # Scraping efficiency should have diminishing returns
        decision_low = self.decision.model_copy(update={"outreach_budget": 500.0})
        monthly_low = calculate_new_monthly_data(self.state, self.a, decision_low)
        
        decision_high = self.decision.model_copy(update={"outreach_budget": 5000.0})
        monthly_high = calculate_new_monthly_data(self.state, self.a, decision_high)
        
        # 10x spend should not give 10x results
        if monthly_low.new_direct_leads > 0:
            efficiency_ratio = (
                (monthly_high.new_direct_leads / 5000.0)
                / (monthly_low.new_direct_leads / 500.0)
            )
            self.assertLess(efficiency_ratio, 2.0)  # High spend should be less efficient

    def test_cash_flow_strict_bounds(self):
        """Test that cash flow is realistic."""
        monthly = calculate_new_monthly_data(self.state, self.a, self.decision)
        
        # Net cash flow should match calculation
        expected_net_cashflow = monthly.profit_bt - monthly.tax
        self.assertAlmostEqual(monthly.net_cashflow, expected_net_cashflow, places=6)
        
        # With initial growth spend, might be negative but not catastrophically
        total_spend = (
            self.decision.ads_budget + self.decision.seo_budget + 
            self.decision.dev_budget + self.decision.partner_budget + 
            self.decision.outreach_budget
        )
        
        # Should not lose more than total spend in a month
        self.assertGreater(monthly.net_cashflow, -total_spend)
        
        # If revenue is positive, cash flow shouldn't be insanely negative
        if monthly.revenue_total > 0:
            self.assertGreater(monthly.net_cashflow, -monthly.revenue_total * 2)

    def test_assumption_values_direct_validation(self):
        """Test critical assumption values directly for realism."""
        # CPC assumptions
        self.assertGreater(self.a.cpc_base, 0.1)      # Min €0.10
        self.assertLess(self.a.cpc_base, 10.0)         # Max €10
        self.assertGreater(self.a.cpc_ref_spend, 100)   # Min €100
        self.assertLess(self.a.cpc_ref_spend, 10000)    # Max €10k
        
        # Conversion rates should be realistic
        self.assertLess(self.a.conv_web_to_lead, 0.10)           # Max 10%
        self.assertLess(self.a.conv_website_lead_to_free, 0.50)   # Max 50%
        self.assertLess(self.a.conv_website_lead_to_pro, 0.05)    # Max 5%
        self.assertLess(self.a.conv_website_lead_to_ent, 0.01)    # Max 1%
        
        # Churn rates
        self.assertLess(self.a.churn_free, 0.50)      # Max 50% monthly
        self.assertLess(self.a.churn_pro, 0.20)       # Max 20% monthly
        self.assertLess(self.a.churn_ent, 0.10)       # Max 10% monthly
        
        # Pricing milestones
        self.assertGreaterEqual(len(self.a.pricing_milestones), 1)
        self.assertGreater(self.a.pricing_milestones[0].pro_price, 100)
        self.assertGreater(self.a.pricing_milestones[0].ent_price, 1000)
        
        # Domain rating
        self.assertGreater(self.a.domain_rating_init, 1)    # Min 1
        self.assertLess(self.a.domain_rating_init, 50)      # Max 50
        self.assertLessEqual(self.a.domain_rating_max, 100)      # Max 100
        
        # Market size
        self.assertGreater(self.a.qualified_pool_total, 1000)   # Min 1k prospects
        self.assertLess(self.a.qualified_pool_total, 10000000)  # Max 10M prospects
        
        # Product value parameters
        self.assertGreater(self.a.pv_init, 10)      # Min 10
        self.assertLess(self.a.pv_init, 1_000_000_000)  # Max 1B
        self.assertLessEqual(self.a.pv_min, self.a.pv_init)
        
        # Financial parameters
        self.assertLess(self.a.tax_rate, 0.50)      # Max 50% tax
        self.assertLess(self.a.market_cap_multiple, 50)   # Max 50x revenue
        
        # Cost parameters
        self.assertLess(self.a.payment_processing_rate, 0.05)  # Max 5%
        self.assertLess(self.a.sales_cost_per_new_pro, 10000)  # Max €10k
        self.assertLess(self.a.sales_cost_per_new_ent, 50000)  # Max €50k

    def test_boundary_conditions_extreme(self):
        """Test behavior at extreme boundary conditions."""
        # Test with zero budgets
        decision_zero = MonthlyDecision(
            ads_budget=0.0,
            seo_budget=0.0,
            dev_budget=0.0,
            partner_budget=0.0,
            outreach_budget=0.0,
        )
        monthly_zero = calculate_new_monthly_data(self.state, self.a, decision_zero)
        
        # Should have 0 users with zero budgets
        self.assertEqual(monthly_zero.website_users, 0)
        
        # Test with maximum reasonable budgets
        decision_max = MonthlyDecision(
            ads_budget=100000.0,    # €100k
            seo_budget=50000.0,     # €50k
            dev_budget=200000.0,    # €200k
            partner_budget=10000.0, # €10k
            outreach_budget=50000.0, # €50k
        )
        monthly_max = calculate_new_monthly_data(self.state, self.a, decision_max)
        
        # Values should be high but not infinite
        self.assertLess(monthly_max.website_users, 10000000)     # Max 10M visitors
        self.assertLess(monthly_max.revenue_total, 100000000)    # Max €100M revenue
        self.assertLess(monthly_max.costs_ex_tax, 50000000)      # Max €50M costs


if __name__ == "__main__":
    unittest.main()
