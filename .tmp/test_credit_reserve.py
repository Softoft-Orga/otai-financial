"""Test the new credit draw mechanism based on cash reserves."""

import sys
sys.path.append('..')

from otai_forecast.models import Assumptions, MonthlyDecision, State, PricingMilestone
from otai_forecast.compute import calculate_new_monthly_data, calculate_new_state


def test_credit_draw_cash_reserve_mechanism():
    """Test that credit is drawn when cash falls below minimum reserve threshold."""
    # Create assumptions with 3 months cash reserve requirement
    a = Assumptions(
        months=12,
        starting_cash=10000.0,
        min_months_cash_reserve=3.0,
        credit_draw_factor=0.5,  # This should no longer be used
        debt_repay_factor=0.0,  # No repayment for this test
        tax_rate=0.0,
        # Minimal required fields
        cpc_base=1.0,
        cpc_sensitivity_factor=0.1,
        cpc_ref_spend=1000.0,
        seo_users_per_eur=0.1,
        domain_rating_init=1.0,
        domain_rating_max=100.0,
        domain_rating_spend_sensitivity=0.1,
        domain_rating_reference_spend_eur=1000.0,
        domain_rating_decay=0.01,
        conv_web_to_lead=0.1,
        conv_website_lead_to_free=0.1,
        conv_website_lead_to_pro=0.0,
        conv_website_lead_to_ent=0.0,
        direct_contacted_demo_conversion=0.0,
        direct_demo_appointment_conversion_to_free=0.0,
        direct_demo_appointment_conversion_to_pro=0.0,
        direct_demo_appointment_conversion_to_ent=0.0,
        conv_free_to_pro=0.0,
        conv_pro_to_ent=0.0,
        churn_free=0.0,
        churn_pro=0.0,
        churn_ent=0.0,
        pricing_milestones=(
            PricingMilestone(product_value_min=0.0, pro_price=100.0, ent_price=500.0),
        ),
        market_cap_multiple=1.0,
        sales_cost_per_new_pro=0.0,
        sales_cost_per_new_ent=0.0,
        it_infra_cost_per_free_deal=0.0,
        it_infra_cost_per_pro_deal=0.0,
        it_infra_cost_per_ent_deal=0.0,
        support_cost_per_pro=0.0,
        support_cost_per_ent=0.0,
        support_subscription_fee_pct_pro=0.0,
        support_subscription_fee_pct_ent=0.0,
        support_subscription_take_rate_pro=0.0,
        support_subscription_take_rate_ent=0.0,
        partner_spend_ref=1000.0,
        partner_product_value_ref=1000.0,
        partner_commission_rate=0.0,
        partner_churn_per_month=0.0,
        partner_pro_deals_per_partner_per_month=0.0,
        partner_ent_deals_per_partner_per_month=0.0,
        operating_baseline=0.0,
        operating_per_user=0.0,
        operating_per_dev=0.0,
        qualified_pool_total=0.0,
        scraping_efficiency_k=0.1,
        scraping_ref_spend=1000.0,
        cost_per_direct_lead=0.0,
        cost_per_direct_demo=0.0,
        debt_interest_rate_base_annual=0.0,
        pv_init=0.0,
        pv_min=0.0,
        product_value_depreciation_rate=0.0,
        milestone_achieved_renewal_percentage=0.0,
        product_renewal_discount_percentage=0.0,
        payment_processing_rate=0.0,
        dev_capex_ratio=0.0,
    )
    
    # Create a state with low cash
    state = State(
        month=0,
        cash=1000.0,  # Low cash
        debt=0.0,
        domain_rating=1.0,
        product_value=0.0,
        free_active=0.0,
        pro_active=0.0,
        ent_active=0.0,
        partners_active=0.0,
        qualified_pool_remaining=0.0,
        website_leads=0.0,
        direct_demo_appointments=0.0,
        revenue_history=(),
    )
    
    # Create a decision that results in negative cashflow
    d = MonthlyDecision(
        ads_budget=0.0,
        seo_budget=0.0,
        dev_budget=0.0,
        outreach_budget=0.0,
        partner_budget=0.0,
        pro_price_override=None,
        ent_price_override=None,
    )
    
    # Calculate monthly data with high operating costs to create negative cashflow
    a.operating_baseline = 5000.0  # High costs to create negative cashflow
    
    monthly = calculate_new_monthly_data(state, a, d)
    
    # With -5000 net cashflow and 3 months reserve requirement:
    # min_cash_required = -(-5000) * 3 = 15000
    # credit_draw = max(0, 15000 - 1000) = 14000
    expected_min_cash = -monthly.net_cashflow_pre_financing * a.min_months_cash_reserve
    expected_credit_draw = max(0.0, expected_min_cash - state.cash)
    
    print(f"Net cashflow pre-financing: {monthly.net_cashflow_pre_financing}")
    print(f"Min cash required: {expected_min_cash}")
    print(f"Current cash: {state.cash}")
    print(f"Expected credit draw: {expected_credit_draw}")
    print(f"Actual credit draw: {monthly.new_credit_draw}")
    
    assert abs(monthly.new_credit_draw - expected_credit_draw) < 0.01, \
        f"Credit draw should be {expected_credit_draw}, got {monthly.new_credit_draw}"
    
    # Test that no credit is drawn when cash is sufficient
    state_high_cash = state.model_copy(update={"cash": 50000.0})
    monthly_high_cash = calculate_new_monthly_data(state_high_cash, a, d)
    
    expected_credit_draw_high = max(0.0, expected_min_cash - 50000.0)
    assert expected_credit_draw_high == 0.0, "No credit should be drawn when cash is sufficient"
    assert monthly_high_cash.new_credit_draw == 0.0, \
        f"Credit draw should be 0 when cash is sufficient, got {monthly_high_cash.new_credit_draw}"
    
    print("✓ Credit draw mechanism works correctly!")


if __name__ == "__main__":
    test_credit_draw_cash_reserve_mechanism()
