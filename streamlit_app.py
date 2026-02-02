from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import tempfile

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.decision_optimizer import (
    choose_best_decisions_by_market_cap,
    run_simulation_df,
)
from otai_forecast.export import export_detailed, export_nice, export_simulation_output
from otai_forecast.models import Assumptions, MonthlyDecision
from otai_forecast.plots import (
    plot_cash_burn_rate,
    plot_conversion_funnel,
    plot_financial_health_score,
    plot_leads,
    plot_ltv_cac_analysis,
    plot_market_cap,
    plot_monthly_revenue,
    plot_net_cashflow,
    plot_product_value,
    plot_ttm_revenue,
    plot_unit_economics,
    plot_user_growth_stacked,
)


def main():
    st.set_page_config(
        page_title="OTAI Financial Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🚀 OTAI Financial Simulation Dashboard")

    tab_inputs, tab_results = st.tabs(["Assumptions", "Results"])

    with tab_inputs:
        with st.form("assumptions_form"):
            t_decisions, t_growth, t_finance, t_product = st.tabs([
                "Decisions",
                "Growth",
                "Finance",
                "Product Value",
            ])

            with t_decisions:
                months = st.slider(
                    "Simulation Period (months)", 6, 60, int(DEFAULT_ASSUMPTIONS.months)
                )
                starting_cash = st.slider(
                    "Starting Cash (€)",
                    0,
                    500000,
                    int(DEFAULT_ASSUMPTIONS.starting_cash),
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    ads_spend = st.slider("Ads", 0, 50000, 500)
                    seo_spend = st.slider("SEO", 0, 50000, 300)
                    social_spend = st.slider("Social", 0, 50000, 150)
                    direct_candidate_outreach_spend = st.slider(
                        "Direct candidate outreach spend", 0, 200000, 0
                    )
                with col_b:
                    dev_spend = st.slider("Development", 0, 200000, 5000)
                    partner_spend = st.slider("Partner spend", 0, 200000, 0)

                max_evals = st.number_input(
                    "Optimization trials",
                    min_value=1000,
                    max_value=250000,
                    value=2000,
                    step=1000,
                )

            with t_growth:
                base_organic_users_per_month = st.slider(
                    "Base organic users / month",
                    0,
                    50000,
                    int(DEFAULT_ASSUMPTIONS.base_organic_users_per_month),
                )
                cpc_eur = st.slider(
                    "CPC (€)", 0.0, 20.0, float(DEFAULT_ASSUMPTIONS.cpc_eur), 0.1
                )
                cpc_base = st.slider(
                    "CPC base (€)",
                    0.0,
                    20.0,
                    float(DEFAULT_ASSUMPTIONS.cpc_base),
                    0.1,
                )
                cpc_k = st.slider(
                    "CPC growth k", 0.0, 2.0, float(DEFAULT_ASSUMPTIONS.cpc_k), 0.05
                )
                cpc_ref_spend = st.slider(
                    "CPC ref spend",
                    1.0,
                    20000.0,
                    float(DEFAULT_ASSUMPTIONS.cpc_ref_spend),
                    100.0,
                )
                seo_eff_users_per_eur = st.slider(
                    "SEO effectiveness (users/€)",
                    0.0,
                    10.0,
                    float(DEFAULT_ASSUMPTIONS.seo_eff_users_per_eur),
                    0.1,
                )
                seo_decay = st.slider(
                    "SEO decay", 0.0, 1.0, float(DEFAULT_ASSUMPTIONS.seo_decay), 0.01
                )

                domain_rating_init = st.slider(
                    "Domain rating init",
                    0.0,
                    100.0,
                    float(DEFAULT_ASSUMPTIONS.domain_rating_init),
                    1.0,
                )
                domain_rating_max = st.slider(
                    "Domain rating max",
                    1.0,
                    200.0,
                    float(DEFAULT_ASSUMPTIONS.domain_rating_max),
                    1.0,
                )
                domain_rating_growth_k = st.slider(
                    "Domain rating growth k",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.domain_rating_growth_k),
                    0.01,
                )
                domain_rating_growth_ref_spend = st.slider(
                    "Domain rating ref spend",
                    1.0,
                    100000.0,
                    float(DEFAULT_ASSUMPTIONS.domain_rating_growth_ref_spend),
                    100.0,
                )
                domain_rating_decay = st.slider(
                    "Domain rating decay",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.domain_rating_decay),
                    0.01,
                )

                qualified_pool_total = st.slider(
                    "Qualified pool",
                    0,
                    500000,
                    int(DEFAULT_ASSUMPTIONS.qualified_pool_total),
                    1000,
                )
                scraping_efficiency_k = st.slider(
                    "Scraping efficiency k",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.scraping_efficiency_k),
                    0.05,
                )
                scraping_ref_spend = st.slider(
                    "Scraping ref spend",
                    1.0,
                    5000.0,
                    float(DEFAULT_ASSUMPTIONS.scraping_ref_spend),
                    50.0,
                )

            with t_finance:
                conv_web_to_lead = st.slider(
                    "Website → Lead",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_web_to_lead),
                    0.005,
                )
                conv_website_lead_to_free = st.slider(
                    "Website lead → Free",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_website_lead_to_free),
                    0.01,
                )
                conv_website_lead_to_pro = st.slider(
                    "Website lead → Pro",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_website_lead_to_pro),
                    0.01,
                )
                conv_website_lead_to_ent = st.slider(
                    "Website lead → Ent",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_website_lead_to_ent),
                    0.001,
                )

                conv_outreach_lead_to_free = st.slider(
                    "Outreach lead → Free",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_outreach_lead_to_free),
                    0.01,
                )
                conv_outreach_lead_to_pro = st.slider(
                    "Outreach lead → Pro",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_outreach_lead_to_pro),
                    0.01,
                )
                conv_outreach_lead_to_ent = st.slider(
                    "Outreach lead → Ent",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_outreach_lead_to_ent),
                    0.001,
                )
                conv_free_to_pro = st.slider(
                    "Free → Pro",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_free_to_pro),
                    0.01,
                )
                conv_pro_to_ent = st.slider(
                    "Pro → Ent",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.conv_pro_to_ent),
                    0.005,
                )

                churn_free = st.slider(
                    "Free churn", 0.0, 1.0, float(DEFAULT_ASSUMPTIONS.churn_free), 0.01
                )
                churn_pro = st.slider(
                    "Pro churn", 0.0, 1.0, float(DEFAULT_ASSUMPTIONS.churn_pro), 0.01
                )
                churn_ent = st.slider(
                    "Ent churn", 0.0, 1.0, float(DEFAULT_ASSUMPTIONS.churn_ent), 0.01
                )
                churn_pro_floor = st.slider(
                    "Pro churn floor",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.churn_pro_floor),
                    0.01,
                )

                pro_price_base = st.slider(
                    "Pro base price",
                    0,
                    20000,
                    int(DEFAULT_ASSUMPTIONS.pro_price_base),
                    100,
                )
                ent_price_base = st.slider(
                    "Ent base price",
                    0,
                    100000,
                    int(DEFAULT_ASSUMPTIONS.ent_price_base),
                    500,
                )
                pro_price_k = st.slider(
                    "Pro price elasticity",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.pro_price_k),
                    0.01,
                )
                ent_price_k = st.slider(
                    "Ent price elasticity",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.ent_price_k),
                    0.01,
                )

                tax_rate = st.slider(
                    "Tax rate", 0.0, 1.0, float(DEFAULT_ASSUMPTIONS.tax_rate), 0.01
                )
                market_cap_multiple = st.slider(
                    "Market cap multiple (TTM revenue)",
                    0.0,
                    30.0,
                    float(DEFAULT_ASSUMPTIONS.market_cap_multiple),
                    0.5,
                )

                sales_cost_per_new_pro = st.slider(
                    "Sales cost / new Pro",
                    0,
                    5000,
                    int(DEFAULT_ASSUMPTIONS.sales_cost_per_new_pro),
                    50,
                )
                sales_cost_per_new_ent = st.slider(
                    "Sales cost / new Ent",
                    0,
                    20000,
                    int(DEFAULT_ASSUMPTIONS.sales_cost_per_new_ent),
                    100,
                )
                support_cost_per_pro = st.slider(
                    "Support cost / Pro",
                    0,
                    1000,
                    int(DEFAULT_ASSUMPTIONS.support_cost_per_pro),
                    10,
                )
                support_cost_per_ent = st.slider(
                    "Support cost / Ent",
                    0,
                    5000,
                    int(DEFAULT_ASSUMPTIONS.support_cost_per_ent),
                    50,
                )

                credit_cash_threshold = st.slider(
                    "Cash threshold for credit draw",
                    0,
                    500000,
                    int(DEFAULT_ASSUMPTIONS.credit_cash_threshold),
                    1000,
                )
                credit_draw_amount = st.slider(
                    "Credit draw amount",
                    0,
                    500000,
                    int(DEFAULT_ASSUMPTIONS.credit_draw_amount),
                    1000,
                )
                debt_interest_rate_base_annual = st.slider(
                    "Base interest rate (annual)",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.debt_interest_rate_base_annual),
                    0.01,
                )
                debt_interest_rate_k = st.slider(
                    "Interest rate debt sensitivity",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.debt_interest_rate_k),
                    0.01,
                )
                debt_interest_rate_ref = st.slider(
                    "Interest rate reference debt",
                    1_000,
                    1_000_000,
                    int(DEFAULT_ASSUMPTIONS.debt_interest_rate_ref),
                    1000,
                )

            with t_product:
                pv_init = st.slider(
                    "PV init", 1.0, 1000.0, float(DEFAULT_ASSUMPTIONS.pv_init), 1.0
                )
                pv_min = st.slider(
                    "PV min", 1.0, 1000.0, float(DEFAULT_ASSUMPTIONS.pv_min), 1.0
                )
                pv_ref = st.slider(
                    "PV ref", 1.0, 1000.0, float(DEFAULT_ASSUMPTIONS.pv_ref), 1.0
                )
                pv_decay_shape = st.slider(
                    "PV decay shape",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.pv_decay_shape),
                    0.01,
                )
                pv_growth_scale = st.slider(
                    "PV growth scale",
                    0.0,
                    1.0,
                    float(DEFAULT_ASSUMPTIONS.pv_growth_scale),
                    0.01,
                )
                k_pv_web_to_lead = st.slider(
                    "k PV web→lead",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.k_pv_web_to_lead),
                    0.05,
                )
                k_pv_lead_to_free = st.slider(
                    "k PV lead→free",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.k_pv_lead_to_free),
                    0.05,
                )
                k_pv_free_to_pro = st.slider(
                    "k PV free→pro",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.k_pv_free_to_pro),
                    0.05,
                )
                k_pv_pro_to_ent = st.slider(
                    "k PV pro→ent",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.k_pv_pro_to_ent),
                    0.05,
                )
                k_pv_churn_pro = st.slider(
                    "k PV churn pro",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.k_pv_churn_pro),
                    0.05,
                )
                k_pv_churn_free = st.slider(
                    "k PV churn free",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.k_pv_churn_free),
                    0.05,
                )
                k_pv_churn_ent = st.slider(
                    "k PV churn ent",
                    0.0,
                    2.0,
                    float(DEFAULT_ASSUMPTIONS.k_pv_churn_ent),
                    0.05,
                )

            col_run_1, col_run_2 = st.columns(2)
            with col_run_1:
                run_sim = st.form_submit_button("🚀 Run Simulation")
            with col_run_2:
                run_opt = st.form_submit_button(
                    "🧠 Run Optimization (maximize market cap)"
                )

        params = {
            **DEFAULT_ASSUMPTIONS.__dict__,
            "months": int(months),
            "starting_cash": float(starting_cash),
            "ads_spend": float(ads_spend),
            "seo_spend": float(seo_spend),
            "social_spend": float(social_spend),
            "dev_spend": float(dev_spend),
            "partner_spend": float(partner_spend),
            "direct_candidate_outreach_spend": float(direct_candidate_outreach_spend),
            "base_organic_users_per_month": float(base_organic_users_per_month),
            "cpc_eur": float(cpc_eur),
            "cpc_base": float(cpc_base),
            "cpc_k": float(cpc_k),
            "cpc_ref_spend": float(cpc_ref_spend),
            "seo_eff_users_per_eur": float(seo_eff_users_per_eur),
            "seo_decay": float(seo_decay),
            "domain_rating_init": float(domain_rating_init),
            "domain_rating_max": float(domain_rating_max),
            "domain_rating_growth_k": float(domain_rating_growth_k),
            "domain_rating_growth_ref_spend": float(domain_rating_growth_ref_spend),
            "domain_rating_decay": float(domain_rating_decay),
            "conv_web_to_lead": float(conv_web_to_lead),
            "conv_website_lead_to_free": float(conv_website_lead_to_free),
            "conv_website_lead_to_pro": float(conv_website_lead_to_pro),
            "conv_website_lead_to_ent": float(conv_website_lead_to_ent),
            "conv_outreach_lead_to_free": float(conv_outreach_lead_to_free),
            "conv_outreach_lead_to_pro": float(conv_outreach_lead_to_pro),
            "conv_outreach_lead_to_ent": float(conv_outreach_lead_to_ent),
            "conv_free_to_pro": float(conv_free_to_pro),
            "conv_pro_to_ent": float(conv_pro_to_ent),
            "churn_free": float(churn_free),
            "churn_pro": float(churn_pro),
            "churn_ent": float(churn_ent),
            "churn_pro_floor": float(churn_pro_floor),
            "pro_price_base": float(pro_price_base),
            "ent_price_base": float(ent_price_base),
            "pro_price_k": float(pro_price_k),
            "ent_price_k": float(ent_price_k),
            "tax_rate": float(tax_rate),
            "market_cap_multiple": float(market_cap_multiple),
            "sales_cost_per_new_pro": float(sales_cost_per_new_pro),
            "sales_cost_per_new_ent": float(sales_cost_per_new_ent),
            "support_cost_per_pro": float(support_cost_per_pro),
            "support_cost_per_ent": float(support_cost_per_ent),
            "qualified_pool_total": float(qualified_pool_total),
            "scraping_efficiency_k": float(scraping_efficiency_k),
            "scraping_ref_spend": float(scraping_ref_spend),
            "credit_cash_threshold": float(credit_cash_threshold),
            "credit_draw_amount": float(credit_draw_amount),
            "debt_interest_rate_base_annual": float(debt_interest_rate_base_annual),
            "debt_interest_rate_k": float(debt_interest_rate_k),
            "debt_interest_rate_ref": float(debt_interest_rate_ref),
            "pv_init": float(pv_init),
            "pv_min": float(pv_min),
            "pv_ref": float(pv_ref),
            "pv_decay_shape": float(pv_decay_shape),
            "pv_growth_scale": float(pv_growth_scale),
            "k_pv_web_to_lead": float(k_pv_web_to_lead),
            "k_pv_lead_to_free": float(k_pv_lead_to_free),
            "k_pv_free_to_pro": float(k_pv_free_to_pro),
            "k_pv_pro_to_ent": float(k_pv_pro_to_ent),
            "k_pv_churn_pro": float(k_pv_churn_pro),
            "k_pv_churn_free": float(k_pv_churn_free),
            "k_pv_churn_ent": float(k_pv_churn_ent),
        }

        assumption_keys = set(Assumptions.__dataclass_fields__.keys())
        a_kwargs = {k: params[k] for k in assumption_keys}

        if run_sim:
            with st.spinner("Running simulation..."):
                a = Assumptions(**a_kwargs)
                decisions = [
                    MonthlyDecision(
                        ads_spend=params["ads_spend"],
                        seo_spend=params["seo_spend"],
                        social_spend=params["social_spend"],
                        dev_spend=params["dev_spend"],
                        partner_spend=params["partner_spend"],
                        direct_candidate_outreach_spend=params[
                            "direct_candidate_outreach_spend"
                        ],
                        pro_price_override=params.get("pro_price_override"),
                        ent_price_override=params.get("ent_price_override"),
                    )
                    for _ in range(a.months)
                ]
                df = run_simulation_df(a, decisions)
                st.session_state.df = df
                st.session_state.decisions = decisions
                st.session_state.assumptions = a

        if run_opt:
            with st.spinner("Running optimization..."):
                a = Assumptions(**a_kwargs)
                base_decisions = [
                    MonthlyDecision(
                        ads_spend=params["ads_spend"],
                        seo_spend=params["seo_spend"],
                        social_spend=params["social_spend"],
                        dev_spend=params["dev_spend"],
                        partner_spend=params["partner_spend"],
                        direct_candidate_outreach_spend=params[
                            "direct_candidate_outreach_spend"
                        ],
                        pro_price_override=params.get("pro_price_override"),
                        ent_price_override=params.get("ent_price_override"),
                    )
                    for _ in range(a.months)
                ]
                decisions, df = choose_best_decisions_by_market_cap(
                    a, base_decisions, max_evals=int(max_evals)
                )
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
            st.dataframe(decisions_df, use_container_width=True)

        if "assumptions" in st.session_state:
            st.header("Assumptions")
            a_tbl = pd.DataFrame([
                {"Parameter": k, "Value": v}
                for k, v in st.session_state.assumptions.__dict__.items()
            ])
            st.dataframe(a_tbl, use_container_width=True)

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
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_cash_burn_rate(df, ax=ax)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_monthly_revenue(df, ax=ax)
            st.pyplot(fig)

        # User Growth and Market Cap
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_user_growth_stacked(df, ax=ax)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_product_value(df, ax=ax)
            st.pyplot(fig)

        # Leads & Traffic
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_leads(df, ax=ax)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_net_cashflow(df, ax=ax)
            st.pyplot(fig)

        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_ttm_revenue(df, ax=ax)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            plot_market_cap(df, ax=ax)
            st.pyplot(fig)

        # Enhanced Analytics
        st.header("🎯 Enhanced Analytics")

        # First row of enhanced plots
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_ltv_cac_analysis(df, ax=ax)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_unit_economics(df, ax=ax)
            st.pyplot(fig)

        # Second row of enhanced plots
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_conversion_funnel(df, ax=ax)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_financial_health_score(df, ax=ax)
            st.pyplot(fig)

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
            use_container_width=True,
        )

        st.subheader("Monthly Full (all columns)")
        st.dataframe(df.round(2), use_container_width=True)

        # Export button
        st.header("💾 Export Results")

        col1, col2, col3 = st.columns(3)

        a = st.session_state.get("assumptions")
        decisions = st.session_state.get("decisions")

        with tempfile.TemporaryDirectory() as td:
            out_path_output = str(Path(td) / "OTAI_Simulation_Output.xlsx")
            out_path_detailed = str(Path(td) / "OTAI_Simulation_Detailed.xlsx")
            out_path_nice = str(Path(td) / "OTAI_Simulation_Nice.xlsx")

            export_simulation_output(
                df, out_path=out_path_output, assumptions=a, monthly_decisions=decisions
            )
            export_detailed(
                df,
                out_path=out_path_detailed,
                assumptions=a,
                monthly_decisions=decisions,
            )
            export_nice(
                df, out_path=out_path_nice, assumptions=a, monthly_decisions=decisions
            )

            with open(out_path_output, "rb") as f:
                b_output = f.read()
            with open(out_path_detailed, "rb") as f:
                b_detailed = f.read()
            with open(out_path_nice, "rb") as f:
                b_nice = f.read()

        with col1:
            st.download_button(
                label="📄 Download Output",
                data=b_output,
                file_name="OTAI_Simulation_Output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with col2:
            st.download_button(
                label="🧾 Download Detailed",
                data=b_detailed,
                file_name="OTAI_Simulation_Detailed.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with col3:
            st.download_button(
                label="✨ Download Nice",
                data=b_nice,
                file_name="OTAI_Simulation_Nice.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


if __name__ == "__main__":
    main()
