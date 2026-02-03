"""Tests for the plotting module."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import pytest

from otai_forecast.plots import (
    plot_cash_burn_rate,
    plot_cash_position,
    plot_conversion_funnel,
    plot_customer_acquisition_channels,
    plot_enhanced_dashboard,
    plot_financial_health_score,
    plot_growth_insights,
    plot_growth_metrics_heatmap,
    plot_leads,
    plot_ltv_cac_analysis,
    plot_market_cap,
    plot_monthly_revenue,
    plot_net_cashflow,
    plot_product_value,
    plot_results,
    plot_revenue_breakdown,
    plot_ttm_revenue,
    plot_unit_economics,
    plot_user_growth,
    plot_user_growth_stacked,
)


@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "month": range(12),
        "cash": [100000 + i * 5000 for i in range(12)],
        "revenue_total": [1000 * i for i in range(1, 13)],
        "revenue_ttm": [
            sum([1000 * j for j in range(1, min(i + 1, 13))]) for i in range(12)
        ],
        "free_active": [100 * i for i in range(1, 13)],
        "pro_active": [10 * i for i in range(1, 13)],
        "ent_active": list(range(1, 13)),
        "product_value": [100 + i * 2 for i in range(12)],
        "leads_total": [50 * i for i in range(1, 13)],
        "net_cashflow": [5000 - i * 100 for i in range(12)],
        "market_cap": [10000 * i for i in range(1, 13)],
        "debt": [0 for i in range(12)],
        "sales_spend": [1000 + i * 50 for i in range(12)],
        "costs_ex_tax": [800 * i for i in range(1, 13)],
        "ads_spend": [500 + i * 25 for i in range(12)],
        "organic_marketing_spend": [300 + i * 15 for i in range(12)],
        "dev_spend": [5000 + i * 100 for i in range(12)],
        "partner_spend": [0 for i in range(12)],
        "direct_candidate_outreach_spend": [0 for i in range(12)],
        "ads_clicks": [100 * i for i in range(1, 13)],
        "website_leads": [30 * i for i in range(1, 13)],
        "new_direct_leads": [10 * i for i in range(1, 13)],
        "new_pro": [5 * i for i in range(1, 13)],
        "new_ent": list(range(1, 13)),
        "cost_sales_marketing": [500 * i for i in range(1, 13)],
        "cost_rd_expense": [3000 + i * 100 for i in range(12)],
        "cost_ga": [1000 + i * 50 for i in range(12)],
        "cost_customer_support": [200 * i for i in range(1, 13)],
        "cost_it_tools": [100 * i for i in range(1, 13)],
        "cost_payment_processing": [50 * i for i in range(1, 13)],
        "cost_outreach_conversion": [0 for i in range(12)],
        "cost_partner_commission": [0 for i in range(12)],
        "revenue_pro_website": [2000 * i for i in range(1, 13)],
        "revenue_pro_outreach": [500 * i for i in range(1, 13)],
        "revenue_pro_partner": [0 for i in range(12)],
        "revenue_ent_website": [5000 * i for i in range(1, 13)],
        "revenue_ent_outreach": [1000 * i for i in range(1, 13)],
        "revenue_ent_partner": [0 for i in range(12)],
    })


def test_plot_results(sample_df):
    """Test the main plot_results function."""
    fig = plot_results(sample_df)
    assert isinstance(fig, go.Figure)


def test_individual_plots(sample_df):
    """Test all individual plot functions."""
    plots = [
        plot_cash_position,
        plot_leads,
        plot_market_cap,
        plot_monthly_revenue,
        plot_net_cashflow,
        plot_product_value,
        plot_ttm_revenue,
        plot_user_growth,
    ]

    for plot_func in plots:
        fig = plot_func(sample_df)
        assert isinstance(fig, go.Figure)


def test_plot_results_with_save(sample_df, tmp_path):
    """Test plot_results with file saving."""
    save_path = tmp_path / "test_plot.png"
    fig = plot_results(sample_df, save_path=str(save_path))
    assert save_path.exists()
    assert isinstance(fig, go.Figure)


def test_enhanced_plots(sample_df):
    """Test all new enhanced plotting functions."""
    enhanced_plots = [
        plot_user_growth_stacked,
        plot_revenue_breakdown,
        plot_cash_burn_rate,
        plot_conversion_funnel,
        plot_ltv_cac_analysis,
        plot_unit_economics,
        plot_growth_metrics_heatmap,
        plot_customer_acquisition_channels,
        plot_financial_health_score,
    ]

    for plot_func in enhanced_plots:
        fig = plot_func(sample_df)
        assert isinstance(fig, go.Figure)


def test_dashboard_functions(sample_df, tmp_path):
    """Test dashboard functions."""
    # Test enhanced dashboard
    save_path = tmp_path / "enhanced_dashboard.png"
    fig = plot_enhanced_dashboard(sample_df, save_path=str(save_path))
    assert isinstance(fig, go.Figure)
    assert save_path.exists()

    # Test growth insights
    save_path = tmp_path / "growth_insights.png"
    fig = plot_growth_insights(sample_df, save_path=str(save_path))
    assert isinstance(fig, go.Figure)
    assert save_path.exists()
