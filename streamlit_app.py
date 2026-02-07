from __future__ import annotations

import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

import pandas as pd
import streamlit as st

from otai_forecast.config import (
    DEFAULT_DECISION,
    OPTIMIZER_KNOT_HIGHS,
    OPTIMIZER_KNOT_LOWS,
    SCENARIO_ASSUMPTIONS,
    build_base_decisions, OPTIMIZER_NUM_KNOTS,
)
from otai_forecast.decision_optimizer import (
    choose_best_decisions_by_market_cap,
    run_simulation_df,
)
from otai_forecast.export import export
from otai_forecast.models import Assumptions, MonthlyDecision, ScenarioAssumptions
from otai_forecast.optimization_storage import (
    assumptions_hash,
    load_optimization,
    save_optimization,
)
from otai_forecast.plots import (
    plot_cash_burn_rate,
    plot_cash_debt_spend,
    plot_conversion_funnel,
    plot_costs_breakdown,
    plot_decision_attributes,
    plot_debt_interest_cash,
    plot_enhanced_dashboard,
    plot_financial_health_score,
    plot_ltv_cac_analysis,
    plot_market_cap,
    plot_net_cashflow,
    plot_product_value,
    plot_revenue_split,
    plot_unit_economics,
    plot_user_growth_stacked,
)

sys.path.append(str(Path(__file__).parent))

# Generate documentation at startup
from scripts.generate_assumptions_markdown import write_markdown

DOC_DIR = Path(__file__).parent / "docs"
DOC_DIR.mkdir(exist_ok=True)
write_markdown(DOC_DIR)

MetricSpec = tuple[str, str, Callable[[float], str]]

OPTIMIZATION_DIR = Path(__file__).parent / "data" / "optimizations"
OPTIMIZATION_DIR.mkdir(parents=True, exist_ok=True)


def _scenario_map(
        scenarios: Iterable[ScenarioAssumptions],
) -> dict[str, ScenarioAssumptions]:
    return {scenario.name: scenario for scenario in scenarios}


def _load_scenario_assumptions(payload: dict | None) -> list[ScenarioAssumptions]:
    if payload is None:
        return list(SCENARIO_ASSUMPTIONS)
    raw_scenarios = payload.get("assumption_scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        return list(SCENARIO_ASSUMPTIONS)
    scenarios: list[ScenarioAssumptions] = []
    for scenario in raw_scenarios:
        if not isinstance(scenario, dict):
            continue
        try:
            scenarios.append(ScenarioAssumptions(**scenario))
        except Exception:
            return list(SCENARIO_ASSUMPTIONS)
    return scenarios or list(SCENARIO_ASSUMPTIONS)


def _apply_optimization_payload(payload: dict) -> None:
    assumptions = Assumptions(**payload["assumptions"])
    decisions = [
        MonthlyDecision(**decision)
        for decision in payload["decisions"]
    ]
    st.session_state.assumptions = assumptions
    st.session_state.decisions = decisions
    st.session_state.df = run_simulation_df(assumptions, decisions)
    st.session_state.assumption_key = payload.get("assumption_hash") or assumptions_hash(
        assumptions
    )
    st.session_state.scenario_assumptions = _load_scenario_assumptions(payload)
    for scenario in st.session_state.scenario_assumptions:
        if assumptions_hash(scenario.assumptions) == st.session_state.assumption_key:
            st.session_state.selected_scenario_name = scenario.name
            break


def _clear_results(assumptions: Assumptions) -> None:
    st.session_state.assumptions = assumptions
    st.session_state.assumption_key = assumptions_hash(assumptions)
    st.session_state.pop("df", None)
    st.session_state.pop("decisions", None)


def _activate_scenario(scenario: ScenarioAssumptions) -> None:
    st.session_state.selected_scenario_name = scenario.name
    assumption_key = assumptions_hash(scenario.assumptions)
    st.session_state.assumption_key = assumption_key
    payload = load_optimization(OPTIMIZATION_DIR, assumption_key)
    if payload:
        _apply_optimization_payload(payload)
        return
    _clear_results(scenario.assumptions)


def _format_int(value: float) -> str:
    return f"{int(value):,}"


def _format_currency(value: float) -> str:
    return f"€{int(value):,}"


def _format_optional_currency(value: float | None) -> str:
    if value is None:
        return "—"
    return _format_currency(value)


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


def _format_assumption_value(key: str, value: object) -> object:
    if key == "pricing_milestones":
        if isinstance(value, tuple):
            value = list(value)
        return _format_milestones(value)
    if isinstance(value, tuple):
        value = list(value)
    if isinstance(value, (list, dict)):
        return str(value)
    return value


def _render_metrics(metrics: Iterable[MetricSpec], values: dict[str, float]) -> None:
    for label, key, formatter in metrics:
        st.metric(label, formatter(values[key]))


def _render_plotly(fig: object) -> None:
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"scrollZoom": False},
    )


def _build_scenario_summary(
    scenarios: Iterable[ScenarioAssumptions],
) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for scenario in scenarios:
        payload = load_optimization(
            OPTIMIZATION_DIR,
            assumptions_hash(scenario.assumptions),
        )
        end_market_cap = None
        if isinstance(payload, dict):
            summary = payload.get("summary")
            if isinstance(summary, dict):
                value = summary.get("end_market_cap")
                if isinstance(value, (int, float)):
                    end_market_cap = float(value)
        rows.append(
            {
                "Scenario": scenario.name,
                "Min liquidity ratio": _format_percent_2(
                    scenario.assumptions.minimum_liquidity_ratio
                ),
                "End Market Cap": _format_optional_currency(end_market_cap),
            }
        )
    return pd.DataFrame(rows)


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
    ("IT infra cost / new Free", "it_infra_cost_per_free_deal", _format_currency),
    ("IT infra cost / new Pro", "it_infra_cost_per_pro_deal", _format_currency),
    ("IT infra cost / new Ent", "it_infra_cost_per_ent_deal", _format_currency),
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

    # Handle query parameters for tab navigation
    query_params = st.query_params
    selected_tab = query_params.get("tab", ["documentation"])[0] if query_params.get("tab") else "documentation"

    if "scenario_assumptions" not in st.session_state:
        st.session_state.scenario_assumptions = list(SCENARIO_ASSUMPTIONS)

    scenarios = st.session_state.scenario_assumptions
    scenario_map = _scenario_map(scenarios)
    default_scenario = next(
        (
            scenario
            for scenario in scenarios
            if scenario.name.lower() == "realistic (without investment)"
        ),
        scenarios[0],
    )
    if "selected_scenario_name" not in st.session_state:
        st.session_state.selected_scenario_name = default_scenario.name
    selected_scenario = scenario_map.get(
        st.session_state.selected_scenario_name,
        default_scenario,
    )
    if selected_scenario.name != st.session_state.selected_scenario_name:
        st.session_state.selected_scenario_name = selected_scenario.name

    if "assumption_key" not in st.session_state:
        st.session_state.assumption_key = assumptions_hash(selected_scenario.assumptions)

    if "df" not in st.session_state:
        payload = load_optimization(OPTIMIZATION_DIR, st.session_state.assumption_key)
        if payload:
            _apply_optimization_payload(payload)
        else:
            _clear_results(selected_scenario.assumptions)

    # Check if we need to initialize session state for documentation
    if "docs_initialized" not in st.session_state:
        st.session_state.docs_initialized = True
        st.session_state.current_docs_tab = 0

    tab_docs, tab_inputs, tab_results = st.tabs(["Documentation", "Optimization", "Results"])

    with tab_inputs:
        st.header("🎛️ Optimization Parameters")
        scenario_names = [scenario.name for scenario in scenarios]
        selected_name = st.selectbox(
            "Scenario assumptions",
            scenario_names,
            index=scenario_names.index(selected_scenario.name),
        )
        if selected_name != selected_scenario.name:
            selected_scenario = scenario_map[selected_name]
            _activate_scenario(selected_scenario)

        t_decisions, t_growth, t_finance, t_product = st.tabs([
            "Decisions",
            "Growth",
            "Finance",
            "Product Value",
        ])

        assumption_values = selected_scenario.assumptions.model_dump()
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
                value=100,
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

        a = selected_scenario.assumptions

        if run_opt:
            with st.spinner("Running optimization..."):
                base_decisions = build_base_decisions(a.months, DEFAULT_DECISION)
                decisions, df = choose_best_decisions_by_market_cap(
                    a,
                    base_decisions,
                    num_knots=OPTIMIZER_NUM_KNOTS,
                    knot_lows=OPTIMIZER_KNOT_LOWS,
                    knot_highs=OPTIMIZER_KNOT_HIGHS,
                    max_evals=int(max_evals),
                )
                st.session_state.df = df
                st.session_state.decisions = decisions
                st.session_state.assumptions = a
                st.session_state.scenario_assumptions = list(SCENARIO_ASSUMPTIONS)
                st.session_state.assumption_key = save_optimization(
                    a,
                    decisions,
                    df,
                    base_dir=OPTIMIZATION_DIR,
                    scenario_assumptions=st.session_state.scenario_assumptions,
                )
                st.session_state.selected_scenario_name = selected_scenario.name

    with tab_results:
        # Display currently selected scenario
        if "selected_scenario_name" in st.session_state:
            st.success(f"📊 Currently Selected Scenario: **{st.session_state.selected_scenario_name}**")
            st.markdown("---")
        
        if "scenario_assumptions" in st.session_state:
            st.header("Scenario Results")
            scenario_cols = st.columns(len(st.session_state.scenario_assumptions))
            for col, scenario in zip(scenario_cols, st.session_state.scenario_assumptions):
                with col:
                    if st.button(
                            scenario.name,
                            key=f"scenario_result_{scenario.name}",
                            use_container_width=True,
                    ):
                        _activate_scenario(scenario)

        if "df" not in st.session_state:
            st.info("Run a simulation or optimization to see results.")
            return

        df = st.session_state.df

        if "decisions" in st.session_state:
            st.header("🗓️ Monthly Decisions")
            decisions_df = pd.DataFrame(
                [
                    {"month": i, **d.model_dump()}
                    for i, d in enumerate(st.session_state.decisions)
                ]
            )
            st.dataframe(decisions_df, use_container_width=True)

            # Add Decision Attributes plot
            st.subheader("📊 Decision Attributes Visualization")
            fig = plot_decision_attributes(df)
            _render_plotly(fig)

        if "assumptions" in st.session_state:
            st.header("Assumptions")
            assumptions_dict = st.session_state.assumptions.model_dump()
            a_tbl = pd.DataFrame(
                [
                    {"Parameter": k, "Value": _format_assumption_value(k, v)}
                    for k, v in assumptions_dict.items()
                ]
            )
            a_tbl["Value"] = a_tbl["Value"].astype(str)
            st.dataframe(a_tbl, use_container_width=True)

        if "scenario_assumptions" in st.session_state:
            st.header("Scenario Assumptions")
            scenario_summary = _build_scenario_summary(
                st.session_state.scenario_assumptions
            )
            st.dataframe(scenario_summary, use_container_width=True, hide_index=True)
            for scenario in st.session_state.scenario_assumptions:
                with st.expander(scenario.name):
                    scenario_dict = scenario.assumptions.model_dump()
                    scenario_tbl = pd.DataFrame(
                        [
                            {
                                "Parameter": k,
                                "Value": _format_assumption_value(k, v),
                            }
                            for k, v in scenario_dict.items()
                        ]
                    )
                    scenario_tbl["Value"] = scenario_tbl["Value"].astype(str)
                    st.dataframe(scenario_tbl, use_container_width=True)

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
            _render_plotly(fig)

        with col2:
            fig = plot_net_cashflow(df)
            _render_plotly(fig)

        # User Growth and Product Value
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_user_growth_stacked(df)
            _render_plotly(fig)

        with col2:
            fig = plot_product_value(df)
            _render_plotly(fig)

        # Market Cap and Debt
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_debt_interest_cash(df)
            _render_plotly(fig)

        with col2:
            fig = plot_market_cap(df)
            _render_plotly(fig)

        # Enhanced Analytics
        st.header("🎯 Enhanced Analytics")

        # First row of enhanced plots
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_ltv_cac_analysis(df)
            _render_plotly(fig)

        with col2:
            fig = plot_unit_economics(df)
            _render_plotly(fig)

        # Second row of enhanced plots
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_conversion_funnel(df)
            _render_plotly(fig)

        with col2:
            fig = plot_financial_health_score(df)
            _render_plotly(fig)

        # New Enhanced Plots
        st.header("📊 Enhanced Financial Visualizations")

        # First row - Cash, Debt, Spend and Cost Breakdown
        col1, col2 = st.columns(2)

        with col1:
            fig = plot_cash_debt_spend(df)
            _render_plotly(fig)

        with col2:
            fig = plot_costs_breakdown(df)
            _render_plotly(fig)

        # Second row - Revenue Split (full width)
        fig = plot_revenue_split(df)
        _render_plotly(fig)

        # Enhanced Dashboard (full width)
        st.subheader("Complete Enhanced Dashboard")
        fig = plot_enhanced_dashboard(df)
        _render_plotly(fig)

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
        # Read and display the documentation markdown
        documentation_path = Path(__file__).parent / "docs" / "documentation.md"
        if documentation_path.exists():
            with open(documentation_path, "r", encoding="utf-8") as f:
                doc_content = f.read()
                st.markdown(doc_content)
        else:
            st.error("Documentation not found. Please ensure the documentation generation script has run.")

        st.markdown("---")

        # Navigation section
        st.markdown("### 📍 Quick Navigation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 Go to Optimization", use_container_width=True, key="nav_opt_docs"):
                st.query_params.from_dict({"tab": "optimization"})
                st.rerun()
        with col2:
            if st.button("📊 Go to Results", use_container_width=True, key="nav_res_docs"):
                st.query_params.from_dict({"tab": "results"})
                st.rerun()

        st.markdown("---")
        st.header("📋 Default Assumptions Documentation")

        # Read and display the assumptions markdown file
        assumptions_md_path = Path(__file__).parent / "docs" / "default_assumptions.md"
        if assumptions_md_path.exists():
            with open(assumptions_md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            st.markdown(md_content)
        else:
            st.warning("Default assumptions documentation not found. Run the markdown generation script to create it.")
            st.code("uv run python scripts/generate_assumptions_markdown.py")


if __name__ == "__main__":
    main()
