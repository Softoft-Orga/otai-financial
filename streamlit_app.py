from __future__ import annotations

import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

import pandas as pd
import streamlit as st

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.decision_optimizer import choose_best_decisions_by_market_cap
from otai_forecast.docs_streamlit import render_documentation
from otai_forecast.export import export
from otai_forecast.models import MonthlyDecision
from otai_forecast.plots import (
    plot_cash_burn_rate,
    plot_cash_debt_spend,
    plot_conversion_funnel,
    plot_costs_breakdown,
    plot_enhanced_dashboard,
    plot_financial_health_score,
    plot_leads,
    plot_ltv_cac_analysis,
    plot_market_cap,
    plot_monthly_revenue,
    plot_net_cashflow,
    plot_product_value,
    plot_revenue_split,
    plot_ttm_revenue,
    plot_unit_economics,
    plot_user_growth_stacked,
)

sys.path.append(str(Path(__file__).parent))

MetricSpec = tuple[str, str, Callable[[float], str]]


def _format_int(value: float) -> str:
    return f"{int(value):,}"


def _format_currency(value: float) -> str:
    return f"€{int(value):,}"


def _format_float(value: float) -> str:
    return f"{value:.2f}"


def _format_percent_1(value: float) -> str:
    return f"{value:.1%}"


def _format_percent_2(value: float) -> str:
    return f"{value:.2%}"


def _format_multiplier(value: float) -> str:
    return f"{value:.1f}x"


def _format_milestones(value: object) -> str:
    if not isinstance(value, list):
        return ""
    parts = []
    for idx, milestone in enumerate(value):
        if not isinstance(milestone, dict):
            continue
        pro_price = milestone.get("pro_price")
        ent_price = milestone.get("ent_price")
        pv_min = milestone.get("product_value_min")
        if pro_price is None or ent_price is None or pv_min is None:
            continue
        parts.append(
            f"v{idx} (pv≥{int(pv_min):,}): €{int(pro_price):,}/€{int(ent_price):,}"
        )
    return " | ".join(parts)


def _render_metrics(metrics: Iterable[MetricSpec], values: dict[str, float]) -> None:
    for label, key, formatter in metrics:
        st.metric(label, formatter(values[key]))


DEFAULT_DECISION = MonthlyDecision(
    ads_budget=10_000.0,
    seo_budget=10_000.0,
    dev_budget=50_000.0,
    partner_budget=1_000.0,
    outreach_budget=10_000.0,
    pro_price_override=None,
    ent_price_override=None,
)

DECISION_TOP_METRICS: list[MetricSpec] = [
    ("Simulation Period (months)", "months", _format_int),
    ("Starting Cash (€)", "starting_cash", _format_currency),
]

DECISION_COL_A_METRICS: list[MetricSpec] = [
    ("Ads Budget", "ads_budget", _format_currency),
    ("Organic Marketing (SEO) Budget", "seo_budget", _format_currency),
    ("Direct Outreach Budget", "outreach_budget", _format_currency),
]

DECISION_COL_B_METRICS: list[MetricSpec] = [
    ("Development Budget", "dev_budget", _format_currency),
    ("Partner Budget", "partner_budget", _format_currency),
]

GROWTH_COL_A_METRICS: list[MetricSpec] = [
    ("Base organic users / month", "base_organic_users_per_month", _format_int),
    ("CPC base (€)", "cpc_base", _format_float),
    ("CPC growth k", "cpc_sensitivity_factor", _format_float),
    ("CPC ref spend", "cpc_ref_spend", _format_int),
    ("SEO effectiveness (users/€)", "seo_users_per_eur", _format_float),
    ("Domain rating init", "domain_rating_init", _format_int),
    ("Domain rating max", "domain_rating_max", _format_int),
]

GROWTH_COL_B_METRICS: list[MetricSpec] = [
    ("Domain rating growth k", "domain_rating_spend_sensitivity", _format_float),
    (
        "Domain rating ref spend",
        "domain_rating_reference_spend_eur",
        _format_int,
    ),
    ("Domain rating decay", "domain_rating_decay", _format_float),
    ("Qualified pool", "qualified_pool_total", _format_int),
    ("Scraping efficiency k", "scraping_efficiency_k", _format_float),
    ("Scraping ref spend", "scraping_ref_spend", _format_int),
]

FINANCE_COL_A_METRICS: list[MetricSpec] = [
    ("Website → Lead", "conv_web_to_lead", _format_percent_1),
    ("Website lead → Free", "conv_website_lead_to_free", _format_percent_1),
    ("Website lead → Pro", "conv_website_lead_to_pro", _format_percent_1),
    ("Website lead → Ent", "conv_website_lead_to_ent", _format_percent_2),
    ("Direct lead → Demo", "direct_contacted_demo_conversion", _format_percent_1),
    ("Demo → Free", "direct_demo_appointment_conversion_to_free", _format_percent_1),
    ("Demo → Pro", "direct_demo_appointment_conversion_to_pro", _format_percent_1),
    ("Demo → Ent", "direct_demo_appointment_conversion_to_ent", _format_percent_2),
    ("Free → Pro", "conv_free_to_pro", _format_percent_1),
    ("Pro → Ent", "conv_pro_to_ent", _format_percent_1),
    ("Free churn", "churn_free", _format_percent_1),
    ("Pro churn", "churn_pro", _format_percent_1),
    ("Ent churn", "churn_ent", _format_percent_1),
]

FINANCE_COL_B_METRICS: list[MetricSpec] = [
    ("Renewal upgrade rate", "milestone_achieved_renewal_percentage", _format_percent_1),
    ("Renewal discount", "product_renewal_discount_percentage", _format_percent_1),
    ("Tax rate", "tax_rate", _format_percent_1),
    ("Market cap multiple", "market_cap_multiple", _format_multiplier),
    ("Sales cost / new Pro", "sales_cost_per_new_pro", _format_currency),
    ("Sales cost / new Ent", "sales_cost_per_new_ent", _format_currency),
    ("Support cost / Pro", "support_cost_per_pro", _format_currency),
    ("Support cost / Ent", "support_cost_per_ent", _format_currency),
    ("Cost per direct lead", "cost_per_direct_lead", _format_currency),
    ("Cost per direct demo", "cost_per_direct_demo", _format_currency),
    ("Base interest rate (annual)", "debt_interest_rate_base_annual", _format_percent_1),
    ("Credit draw factor", "credit_draw_factor", _format_float),
    ("Debt repay factor", "debt_repay_factor", _format_float),
]

PRODUCT_COL_A_METRICS: list[MetricSpec] = [
    ("PV init", "pv_init", _format_int),
    ("PV min", "pv_min", _format_int),
    ("PV depreciation", "product_value_depreciation_rate", _format_percent_1),
]

PRODUCT_COL_B_METRICS: list[MetricSpec] = [
    ("Pricing milestones", "pricing_milestones", _format_milestones),
]


def main():
    st.set_page_config(
        page_title="OTAI Financial Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🚀 OTAI Financial Simulation Dashboard")

    tab_inputs, tab_results, tab_docs = st.tabs(["Assumptions", "Results", "Documentation"])

    with tab_inputs:
        t_decisions, t_growth, t_finance, t_product = st.tabs([
            "Decisions",
            "Growth",
            "Finance",
            "Product Value",
        ])

        assumption_values = DEFAULT_ASSUMPTIONS.model_dump()
        decision_values = DEFAULT_DECISION.model_dump()

        with t_decisions:
            _render_metrics(DECISION_TOP_METRICS, assumption_values)

            col_a, col_b = st.columns(2)
            with col_a:
                _render_metrics(DECISION_COL_A_METRICS, decision_values)
            with col_b:
                _render_metrics(DECISION_COL_B_METRICS, decision_values)

            max_evals = st.number_input(
                "Optimization trials",
                min_value=100,
                max_value=5000,
                value=500,
                step=100,
                help="Number of optimization trials. With TPE sampler, 500 trials usually achieve better results than 25,000 random trials.",
            )

            with t_growth:
                col_a, col_b = st.columns(2)
                with col_a:
                    _render_metrics(GROWTH_COL_A_METRICS, assumption_values)
                with col_b:
                    _render_metrics(GROWTH_COL_B_METRICS, assumption_values)

            with t_finance:
                col_a, col_b = st.columns(2)
                with col_a:
                    _render_metrics(FINANCE_COL_A_METRICS, assumption_values)
                with col_b:
                    _render_metrics(FINANCE_COL_B_METRICS, assumption_values)

            with t_product:
                col_a, col_b = st.columns(2)
                with col_a:
                    _render_metrics(PRODUCT_COL_A_METRICS, assumption_values)
                with col_b:
                    _render_metrics(PRODUCT_COL_B_METRICS, assumption_values)

            # Optimization button (centered)
            st.markdown("---")
            run_opt = st.button("🧠 Run Optimization (maximize market cap)", type="primary")

        # Use DEFAULT_ASSUMPTIONS directly since all inputs are now read-only
        a = DEFAULT_ASSUMPTIONS

        if run_opt:
            with st.spinner("Running optimization..."):
                base_decisions = [
                    DEFAULT_DECISION.model_copy()
                    for _ in range(a.months)
                ]
                decisions, df = choose_best_decisions_by_market_cap(a, base_decisions, num_knots=9, knot_low=0, knot_high=10,
                                                        max_evals=int(max_evals))
                st.session_state.df = df
                st.session_state.decisions = decisions
                st.session_state.assumptions = a

    with tab_results:
        if "df" not in st.session_state:
            st.info("Run a simulation or optimization to see results.")
            return

        df = st.session_state.df

        if "decisions" in st.session_state:
            st.header("🗓️ Monthly Decisions")
            decisions_df = pd.DataFrame([
                {"month": i, **d.__dict__}
                for i, d in enumerate(st.session_state.decisions)
            ])
            st.dataframe(decisions_df, width='stretch')

        if "assumptions" in st.session_state:
            st.header("Assumptions")
            a_tbl = pd.DataFrame([
                {"Parameter": k, "Value": v}
                for k, v in st.session_state.assumptions.__dict__.items()
            ])
            st.dataframe(a_tbl, width='stretch')

        # KPIs
        st.header("📊 Key Performance Indicators")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            end_cash = df["cash"].iloc[-1]
            st.metric("End Cash", f"€{end_cash:,.0f}")

        with col2:
            min_cash = df["cash"].min()
            st.metric("Min Cash", f"€{min_cash:,.0f}")

        with col3:
            end_pro = df["pro_active"].iloc[-1]
            end_ent = df["ent_active"].iloc[-1]
            st.metric("End Pro/Ent", f"{int(end_pro)}/{int(end_ent)}")

        with col4:
            end_pv = df["product_value"].iloc[-1]
            st.metric("End Product Value", f"{end_pv:,.2f}")

        col1, col2 = st.columns(2)

        with col1:
            end_revenue_ttm = df["revenue_ttm"].iloc[-1]
            st.metric("End TTM Revenue", f"€{end_revenue_ttm:,.0f}")

        with col2:
            end_market_cap = df["market_cap"].iloc[-1]
            st.metric("End Market Cap", f"€{end_market_cap:,.0f}")

        # Additional KPIs
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_revenue = df["revenue_total"].sum()
            st.metric("Total Revenue", f"€{total_revenue:,.0f}")

        with col2:
            total_costs = df["costs_ex_tax"].sum()
            st.metric("Total Costs (ex tax)", f"€{total_costs:,.0f}")

        with col3:
            total_profit = df["profit_bt"].sum() - df["tax"].sum()
            st.metric("Total Profit (after tax)", f"€{total_profit:,.0f}")

        with col4:
            total_leads = df["leads_total"].sum()
            st.metric("Total Leads", f"{total_leads:,.0f}")

        # Charts
        st.header("📈 Visualizations")

        # Cash and Revenue
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_cash_burn_rate(df)
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = plot_monthly_revenue(df)
            st.plotly_chart(fig, width='stretch')

        # User Growth and Market Cap
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_user_growth_stacked(df)
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = plot_product_value(df)
            st.plotly_chart(fig, width='stretch')

        # Leads & Traffic
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_leads(df)
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = plot_net_cashflow(df)
            st.plotly_chart(fig, width='stretch')

        col1, col2 = st.columns(2)

        with col1:
            fig = plot_ttm_revenue(df)
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = plot_market_cap(df)
            st.plotly_chart(fig, width='stretch')

        # Enhanced Analytics
        st.header("🎯 Enhanced Analytics")

        # First row of enhanced plots
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_ltv_cac_analysis(df)
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = plot_unit_economics(df)
            st.plotly_chart(fig, width='stretch')

        # Second row of enhanced plots
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_conversion_funnel(df)
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = plot_financial_health_score(df)
            st.plotly_chart(fig, width='stretch')

        # New Enhanced Plots
        st.header("📊 Enhanced Financial Visualizations")

        # First row - Cash, Debt, Spend and Cost Breakdown
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_cash_debt_spend(df)
            st.plotly_chart(fig, width='stretch')

        with col2:
            fig = plot_costs_breakdown(df)
            st.plotly_chart(fig, width='stretch')

        # Second row - Revenue Split (full width)
        fig = plot_revenue_split(df)
        st.plotly_chart(fig, width='stretch')

        # Enhanced Dashboard (full width)
        st.subheader("Complete Enhanced Dashboard")
        fig = plot_enhanced_dashboard(df)
        st.plotly_chart(fig, width='stretch')

        # Tables
        st.header("📋 Detailed Tables")

        # Overview table
        st.subheader("Monthly Overview")
        st.dataframe(
            df[
                [
                    "month",
                    "cash",
                    "debt",
                    "domain_rating",
                    "free_active",
                    "pro_active",
                    "ent_active",
                    "revenue_total",
                    "costs_ex_tax",
                    "tax",
                    "net_cashflow",
                ]
            ].round(2),
            width='stretch',
        )

        st.subheader("Monthly Full (all columns)")
        st.dataframe(df.round(2), width='stretch')

        # Export button
        st.header("💾 Export Results")

        col1, col2, col3 = st.columns(3)

        a = st.session_state.get("assumptions")
        decisions = st.session_state.get("decisions")

        with tempfile.TemporaryDirectory() as td:
            out_path_report = str(Path(td) / "OTAI_Simulation_Report.xlsx")

            export(
                df, out_path=out_path_report, assumptions=a, monthly_decisions=decisions
            )

            with open(out_path_report, "rb") as f:
                b_report = f.read()

        with col1:
            st.download_button(
                label="📊 Download Complete Report",
                data=b_report,
                file_name="OTAI_Simulation_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    with tab_docs:
        render_documentation(DEFAULT_ASSUMPTIONS)


if __name__ == "__main__":
    main()
