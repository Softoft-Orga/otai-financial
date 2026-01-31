from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from otai_forecast.config import DEFAULT_ASSUMPTIONS, DEFAULT_DEV_PARAMS, DEFAULT_PRICES
from otai_forecast.models import (
    Assumptions,
    Policy,
    PolicyParams,
)
from otai_forecast.optimize import PolicyOptimizer
from otai_forecast.roadmap import create_otai_roadmap
from otai_forecast.simulator import DetailedSimulator, Simulator


def run_simulation(params: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the simulation with given parameters."""
    # Create assumptions
    a = Assumptions(
        months=params["months"],
        dev_day_cost_eur=params["dev_day_cost_eur"],
        starting_cash_eur=params["starting_cash_eur"],
        ops_fixed_eur_per_month=params["ops_fixed_eur_per_month"],
        ads_cost_per_lead_base=params["ads_cost_per_lead_base"],
        monthly_ads_expense=params["monthly_ads_expense"],
        brand_popularity=params["brand_popularity"],
        conv_lead_to_free=params["conv_lead_to_free"],
        conv_free_to_pro=params["conv_free_to_pro"],
        conv_pro_to_ent=params["conv_pro_to_ent"],
        churn_free=params["churn_free"],
        churn_pro=params["churn_pro"],
        churn_ent=params["churn_ent"],
        referral_leads_per_active_free=0.01,
        partner_commission_rate=0.20,
        pro_deals_per_partner_per_month=0.02,
        ent_deals_per_partner_per_month=0.002,
        new_partners_base_per_month=0.1,
        valuation_multiple_arr=10.0,
        credit_interest_rate_annual=0.10,
        credit_draw_amount=100_000.0,
        credit_cash_threshold=50_000.0,
    )

    # Create policy
    policy = Policy(
        p=PolicyParams(
            ads_start=params["ads_start"],
            ads_growth=params["ads_growth"],
            ads_cap=params["ads_cap"],
            social_baseline=params["social_baseline"],
            additional_dev_days=params.get(
                "additional_dev_days", DEFAULT_DEV_PARAMS["additional_dev_days"]
            ),
            **DEFAULT_PRICES,
        ),
    )

    # Create roadmap
    roadmap = create_otai_roadmap()

    # Run simulations
    sim = Simulator(a=a, roadmap=roadmap, policy=policy)
    rows = sim.run()
    df = pd.DataFrame([r.__dict__ for r in rows])

    sim_detailed = DetailedSimulator(a=a, roadmap=roadmap, policy=policy)
    detailed_log = sim_detailed.run()
    df_detailed = pd.DataFrame(detailed_log)

    return df, df_detailed


def main():
    st.set_page_config(
        page_title="OTAI Financial Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🚀 OTAI Financial Simulation Dashboard")

    # Sidebar inputs
    st.sidebar.header("Simulation Parameters")

    # Check if we have optimized values to use
    optimized_values = st.session_state.get("update_optimization_params", {})

    # Basic parameters
    st.sidebar.subheader("Basic Settings")
    months = st.sidebar.slider("Simulation Period (months)", 6, 60, 24)
    dev_day_cost_eur = st.sidebar.slider("Dev Day Cost (€)", 300, 1000, 600)
    starting_cash_eur = st.sidebar.slider("Starting Cash (€)", 50000, 500000, 100000)
    fixed_overhead_eur_per_month = st.sidebar.slider(
        "Fixed Overhead (€/month)", 0, 50000, 0
    )

    # Marketing parameters
    st.sidebar.subheader("Marketing")
    ads_start = st.sidebar.slider(
        "Initial Ad Spend (€/month)",
        0,
        5000,
        int(optimized_values.get("ads_start", 500)),
    )
    ads_growth = st.sidebar.slider(
        "Ad Growth Rate", 0.0, 0.5, optimized_values.get("ads_growth", 0.0), 0.05
    )
    ads_cap = st.sidebar.slider(
        "Ad Spend Cap (€/month)",
        1000,
        20000,
        int(optimized_values.get("ads_cap", 5000)),
    )
    social_baseline = st.sidebar.slider(
        "Social Media Spend (€/month)",
        0,
        1000,
        int(optimized_values.get("social_baseline", 150)),
    )

    # Pricing
    st.sidebar.subheader("Pricing")
    pro_price = st.sidebar.slider("Pro Price (€/month)", 1000, 10000, 3500)
    ent_price = st.sidebar.slider("Enterprise Price (€/month)", 5000, 50000, 20000)
    st.sidebar.caption("💡 Pricing is fixed and not optimized")

    # Development
    st.sidebar.subheader("Development")
    additional_dev_days = st.sidebar.slider(
        "Additional Dev Days (for new features)",
        0,
        20,
        int(
            optimized_values.get(
                "additional_dev_days", DEFAULT_DEV_PARAMS["additional_dev_days"]
            )
        ),
    )

    # Conversion rates
    st.sidebar.subheader("Conversion Rates")
    conv_lead_to_free = st.sidebar.slider("Lead → Free", 0.1, 0.5, 0.25, 0.05)
    conv_free_to_pro = st.sidebar.slider("Free → Pro", 0.05, 0.3, 0.10, 0.01)
    conv_pro_to_ent = st.sidebar.slider("Pro → Ent", 0.01, 0.1, 0.02, 0.01)

    # Churn rates
    st.sidebar.subheader("Churn Rates")
    churn_free = st.sidebar.slider("Free Churn", 0.05, 0.3, 0.15, 0.01)
    churn_pro = st.sidebar.slider("Pro Churn", 0.01, 0.1, 0.03, 0.01)
    churn_ent = st.sidebar.slider("Ent Churn", 0.005, 0.05, 0.01, 0.005)

    # Show if optimized values are being used
    if optimized_values:
        st.sidebar.success("✨ Using optimized parameters")
        if st.sidebar.button("Reset to Default Values"):
            st.session_state.pop("update_optimization_params", None)
            st.rerun()

    # Other default parameters
    params = {
        **DEFAULT_ASSUMPTIONS.__dict__,
        "months": months,
        "dev_day_cost_eur": dev_day_cost_eur,
        "starting_cash_eur": starting_cash_eur,
        "ops_fixed_eur_per_month": 5000.0,  # Fixed ops cost
        "ads_cost_per_lead_base": 2.0,  # Base cost per lead from ads
        "monthly_ads_expense": 500.0,  # Will be overridden by ads_start
        "brand_popularity": 1.0,  # Starting brand popularity
        "conv_lead_to_free": conv_lead_to_free,
        "conv_free_to_pro": conv_free_to_pro,
        "conv_pro_to_ent": conv_pro_to_ent,
        "churn_free": churn_free,
        "churn_pro": churn_pro,
        "churn_ent": churn_ent,
        "additional_dev_days": additional_dev_days,
        **optimized_values,
        **DEFAULT_PRICES,
    }

    # Run simulation button
    if st.sidebar.button("🚀 Run Simulation", type="primary"):
        with st.spinner("Running simulation..."):
            df, df_detailed = run_simulation(params)
            st.session_state.df = df
            st.session_state.df_detailed = df_detailed

    # Display results if available
    if "df" in st.session_state:
        df = st.session_state.df
        df_detailed = st.session_state.df_detailed

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
            final_market_cap = df["market_cap"].iloc[-1]
            st.metric("Final Market Cap", f"€{final_market_cap:,.0f}")

        # Additional KPIs
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_revenue = df["revenue_total"].sum()
            st.metric("Total Revenue", f"€{total_revenue:,.0f}")

        with col2:
            final_arr = df["arr"].iloc[-1]
            st.metric("Final ARR", f"€{final_arr:,.0f}")

        with col3:
            total_profit = df["profit_after_tax"].sum()
            st.metric("Total Profit", f"€{total_profit:,.0f}")

        with col4:
            final_debt = df["debt"].iloc[-1]
            st.metric("Final Debt", f"€{final_debt:,.0f}")

        # Charts
        st.header("📈 Visualizations")

        # Cash and Revenue
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["cash"], marker="o", color="purple")
            ax.set_title("Cash Position Over Time")
            ax.set_xlabel("Month")
            ax.set_ylabel("Cash (€)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["revenue_total"], marker="o", color="green")
            ax.set_title("Monthly Revenue")
            ax.set_xlabel("Month")
            ax.set_ylabel("Revenue (€)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        # User Growth and Market Cap
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["free_active"], label="Free Users", marker="o")
            ax.plot(df["t"], df["pro_active"], label="Pro Users", marker="o")
            ax.plot(df["t"], df["ent_active"], label="Ent Users", marker="o")
            ax.set_title("User Growth")
            ax.set_xlabel("Month")
            ax.set_ylabel("Users")
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["market_cap"], marker="o", color="red")
            ax.set_title("Market Cap Over Time")
            ax.set_xlabel("Month")
            ax.set_ylabel("Market Cap (€)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        # Leads & Traffic
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["leads"], label="Total Leads", marker="o")
            ax.set_title("Leads Over Time")
            ax.set_xlabel("Month")
            ax.set_ylabel("Count")
            ax.legend()
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["profit_after_tax"], marker="o", color="orange")
            ax.set_title("Monthly Profit After Tax")
            ax.set_xlabel("Month")
            ax.set_ylabel("Profit (€)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        # Debt and Interest
        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["debt"], marker="o", color="red")
            ax.set_title("Debt Over Time")
            ax.set_xlabel("Month")
            ax.set_ylabel("Debt (€)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["t"], df["interest_payment"], marker="o", color="brown")
            ax.set_title("Monthly Interest Payments")
            ax.set_xlabel("Month")
            ax.set_ylabel("Interest (€)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

        # Tables
        st.header("📋 Detailed Tables")

        # Overview table
        st.subheader("Monthly Overview")
        st.dataframe(
            df[
                [
                    "t",
                    "cash",
                    "debt",
                    "free_active",
                    "pro_active",
                    "ent_active",
                    "revenue_total",
                    "net_cashflow",
                    "interest_payment",
                ]
            ].round(2),
            use_container_width=True,
        )

        # Finance breakdown (from detailed simulation)
        st.subheader("Finance Breakdown")
        finance_cols = [
            "month",
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
        st.dataframe(df_detailed[finance_cols].round(2), use_container_width=True)

        # Export button
        st.header("💾 Export Results")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Create Excel files in memory
            overview_excel = io.BytesIO()
            with pd.ExcelWriter(overview_excel, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Overview")
            overview_excel.seek(0)

            st.download_button(
                label="📊 Download Overview",
                data=overview_excel.getvalue(),
                file_name="OTAI_Overview.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with col2:
            detailed_excel = io.BytesIO()
            with pd.ExcelWriter(detailed_excel, engine="openpyxl") as writer:
                df_detailed.to_excel(writer, index=False, sheet_name="Detailed")
            detailed_excel.seek(0)

            st.download_button(
                label="📈 Download Detailed",
                data=detailed_excel.getvalue(),
                file_name="OTAI_Detailed.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with col3:
            # Combined export
            combined_excel = io.BytesIO()
            with pd.ExcelWriter(combined_excel, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Overview")
                df_detailed.to_excel(writer, index=False, sheet_name="Detailed")
            combined_excel.seek(0)

            st.download_button(
                label="📚 Download Combined",
                data=combined_excel.getvalue(),
                file_name="OTAI_Simulation_Results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Optimization section
    st.header("🎯 Parameter Optimization")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Optimize Policy Parameters")
        st.write("Objective: Maximize Final Market Cap (while avoiding negative cash)")

        n_iterations = st.slider("Number of Iterations", 10, 100, 50)

        if st.button("🚀 Run Optimization", type="primary"):
            with st.spinner("Running optimization..."):
                # Create assumptions and roadmap
                a = DEFAULT_ASSUMPTIONS

                roadmap = create_otai_roadmap()

                # Create optimizer
                optimizer = PolicyOptimizer(
                    assumptions=a,
                    roadmap=roadmap,
                )

                # Run optimization
                result = optimizer.optimize(n_iterations=n_iterations)

                # Store results
                st.session_state.optimization_result = result

                # Update sidebar parameters to best values
                best = result.best_params
                st.session_state.update_optimization_params = {
                    "ads_start": best.ads_start,
                    "ads_growth": best.ads_growth,
                    "ads_cap": best.ads_cap,
                    "social_baseline": best.social_baseline,
                    "additional_dev_days": best.additional_dev_days,
                    # Note: pro_price and ent_price are fixed and not optimized
                }
                st.success(
                    "✅ Optimization complete! Parameters updated to best values."
                )

                # Auto-run simulation with optimized parameters
                optimized_params = {
                    **DEFAULT_ASSUMPTIONS.__dict__,
                    **st.session_state.update_optimization_params,
                    **DEFAULT_PRICES,
                }

                df, df_detailed = run_simulation(optimized_params)
                st.session_state.df = df
                st.session_state.df_detailed = df_detailed
                st.rerun()

    # Display optimization results if available
    if "optimization_result" in st.session_state:
        result = st.session_state.optimization_result

        with col2:
            st.subheader("Best Result")
            st.metric("Best Market Cap", f"€{result.best_score:,.2f}")

            st.subheader("Optimal Parameters")
            st.write(f"**Ad Start:** €{result.best_params.ads_start:,.2f}")
            st.write(f"**Ad Growth:** {result.best_params.ads_growth:.1%}")
            st.write(f"**Ad Cap:** €{result.best_params.ads_cap:,.2f}")
            st.write(f"**Social Baseline:** €{result.best_params.social_baseline:,.2f}")
            st.write(
                f"**Additional Dev Days:** {result.best_params.additional_dev_days:.1f} days/month"
            )
            st.write(f"**Pro Price:** €{result.best_params.pro_price:,.2f} (fixed)")
            st.write(f"**Ent Price:** €{result.best_params.ent_price:,.2f} (fixed)")


if __name__ == "__main__":
    main()
