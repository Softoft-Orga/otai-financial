from __future__ import annotations

import inspect
from collections.abc import Callable

import streamlit as st

from otai_forecast.compute import (
    _effective_cpc,
    _effective_interest_rate_annual,
    _map_value_to_rates_prices,
    _update_domain_rating,
    _update_product_value,
)
from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.models import Assumptions, MonthlyDecision, State

MERMAID_TEMPLATE = """
<div class="mermaid">
{diagram}
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
mermaid.initialize({{ startOnLoad: true }});
</script>
"""

DEFAULT_DOC_DECISION = MonthlyDecision(
    ads_budget=10_000.0,
    seo_budget=10_000.0,
    dev_budget=50_000.0,
    partner_budget=1_000.0,
    outreach_budget=10_000.0,
    pro_price_override=None,
    ent_price_override=None,
)


def _build_mermaid_html(diagram: str) -> str:
    return MERMAID_TEMPLATE.format(diagram=diagram.strip())


def _base_state(
    assumptions: Assumptions,
    *,
    cash: float | None = None,
    domain_rating: float | None = None,
    product_value: float | None = None,
) -> State:
    return State(
        month=0,
        cash=assumptions.starting_cash if cash is None else cash,
        debt=0.0,
        domain_rating=(
            assumptions.domain_rating_init if domain_rating is None else domain_rating
        ),
        product_value=assumptions.pv_init if product_value is None else product_value,
        free_active=0.0,
        pro_active=0.0,
        ent_active=0.0,
        partners_active=0.0,
        qualified_pool_remaining=assumptions.qualified_pool_total,
    )


def _with_decision_overrides(
    decision: MonthlyDecision, **updates: float | None
) -> MonthlyDecision:
    return decision.model_copy(update=updates)


def _map_rates_prices_preview(
    product_value_factor: float, assumptions: Assumptions, decision: MonthlyDecision
) -> dict[str, float]:
    values = _map_value_to_rates_prices(product_value_factor, assumptions, decision)
    keys = [
        "pro_price",
        "ent_price",
        "conv_web_to_lead_eff",
        "conv_website_lead_to_free_eff",
        "conv_website_lead_to_pro_eff",
        "conv_website_lead_to_ent_eff",
        "conv_outreach_lead_to_free_eff",
        "conv_outreach_lead_to_pro_eff",
        "conv_outreach_lead_to_ent_eff",
        "upgrade_free_to_pro_eff",
        "upgrade_pro_to_ent_eff",
        "churn_free_eff",
        "churn_pro_eff",
        "churn_ent_eff",
    ]
    return dict(zip(keys, values, strict=True))


def render_documentation(assumptions: Assumptions | None = None) -> None:
    a = assumptions or DEFAULT_ASSUMPTIONS

    st.title("OTAI Simulation Documentation")
    st.markdown(
        "Use this page to explore the live calculations from ``compute.py`` without "
        "duplicating logic. Adjust inputs below to see how core formulas behave."
    )

    st.subheader("Monthly flow")
    st.caption("Mermaid renders via a CDN script. If blocked, view the source below.")
    diagram = """
    graph TD
        A[Monthly decision] --> B[Update product value]
        B --> C[Effective conversions and pricing]
        C --> D[Lead generation]
        D --> E[Customer changes]
        E --> F[Revenue and costs]
        F --> G[State update]
    """
    st.html(_build_mermaid_html(diagram), unsafe_allow_javascript=True)
    with st.expander("Mermaid source"):
        st.code(diagram.strip(), language="mermaid")

    st.subheader("Interactive calculators")
    tabs = st.tabs(
        [
            "CPC",
            "Domain rating",
            "Product value",
            "Conversions and pricing",
            "Debt interest",
        ]
    )

    with tabs[0]:
        _render_cpc_calculator(a)
    with tabs[1]:
        _render_domain_rating_calculator(a)
    with tabs[2]:
        _render_product_value_calculator(a)
    with tabs[3]:
        _render_conversion_pricing_calculator(a)
    with tabs[4]:
        _render_interest_calculator(a)


def _render_cpc_calculator(assumptions: Assumptions) -> None:
    st.markdown("#### Effective CPC")
    st.latex(
        r"CPC_{eff} = CPC_{base} \times (1 + k \times \ln(1 + spend / spend_{ref}))"
    )
    ads_spend = st.slider(
        "Ads budget (EUR)",
        min_value=0.0,
        max_value=200_000.0,
        value=float(DEFAULT_DOC_DECISION.ads_budget),
        step=1_000.0,
    )
    result = _effective_cpc(ads_spend, assumptions)
    st.metric("Effective CPC (EUR)", f"{result:,.2f}")
    col1, col2, col3 = st.columns(3)
    col1.metric("CPC base", f"{assumptions.cpc_base:.2f}")
    col2.metric("Sensitivity k", f"{assumptions.cpc_sensitivity_factor:.2f}")
    col3.metric("Reference spend", f"{assumptions.cpc_ref_spend:,.0f} EUR")
    _render_source(_effective_cpc)


def _render_domain_rating_calculator(assumptions: Assumptions) -> None:
    st.markdown("#### Domain rating update")
    st.latex(
        r"DR_{next} = DR \times (1 - decay) + (DR_{max} - DR)"
        r" \times k \times \ln(1 + spend / spend_{ref})"
    )
    domain_rating = st.slider(
        "Starting domain rating",
        min_value=0.0,
        max_value=float(assumptions.domain_rating_max),
        value=float(assumptions.domain_rating_init),
        step=1.0,
    )
    seo_budget = st.slider(
        "SEO budget (EUR)",
        min_value=0.0,
        max_value=200_000.0,
        value=float(DEFAULT_DOC_DECISION.seo_budget),
        step=1_000.0,
    )
    state = _base_state(assumptions, domain_rating=domain_rating)
    decision = _with_decision_overrides(DEFAULT_DOC_DECISION, seo_budget=seo_budget)
    next_rating = _update_domain_rating(state, assumptions, decision)
    st.metric("Next domain rating", f"{next_rating:.2f}")
    col1, col2, col3 = st.columns(3)
    col1.metric("DR max", f"{assumptions.domain_rating_max:.0f}")
    col2.metric("Sensitivity k", f"{assumptions.domain_rating_spend_sensitivity:.2f}")
    col3.metric(
        "Reference spend", f"{assumptions.domain_rating_reference_spend_eur:,.0f} EUR"
    )
    _render_source(_update_domain_rating)


def _render_product_value_calculator(assumptions: Assumptions) -> None:
    st.markdown("#### Product value update")
    st.caption(
        "Product value decays when dev spend is below maintenance, and grows with "
        "diminishing returns above it."
    )
    product_value = st.slider(
        "Starting product value",
        min_value=float(assumptions.pv_min),
        max_value=float(assumptions.pv_ref * 2.0),
        value=float(assumptions.pv_init),
        step=1.0,
    )
    dev_budget = st.slider(
        "Dev budget (EUR)",
        min_value=0.0,
        max_value=200_000.0,
        value=float(DEFAULT_DOC_DECISION.dev_budget),
        step=1_000.0,
    )
    state = _base_state(assumptions, product_value=product_value)
    decision = _with_decision_overrides(DEFAULT_DOC_DECISION, dev_budget=dev_budget)
    pv_next, pv_factor = _update_product_value(state, assumptions, decision)
    st.metric("Next product value", f"{pv_next:.2f}")
    st.metric("Product value factor", f"{pv_factor:.4f}")
    col1, col2 = st.columns(2)
    col1.metric("PV min", f"{assumptions.pv_min:.0f}")
    col2.metric("Growth efficiency", f"{assumptions.dev_spend_growth_efficiency:.3f}")
    _render_source(_update_product_value)


def _render_conversion_pricing_calculator(assumptions: Assumptions) -> None:
    st.markdown("#### Conversions and pricing")
    product_value = st.slider(
        "Product value",
        min_value=float(assumptions.pv_min),
        max_value=float(assumptions.pv_ref * 2.0),
        value=float(assumptions.pv_init),
        step=1.0,
    )
    dev_budget = st.slider(
        "Dev budget (EUR)",
        min_value=0.0,
        max_value=200_000.0,
        value=float(DEFAULT_DOC_DECISION.dev_budget),
        step=1_000.0,
        key="docs_dev_budget_rates",
    )
    state = _base_state(assumptions, product_value=product_value)
    decision = _with_decision_overrides(DEFAULT_DOC_DECISION, dev_budget=dev_budget)
    _, pv_factor = _update_product_value(state, assumptions, decision)
    rates = _map_rates_prices_preview(pv_factor, assumptions, decision)

    rows = []
    for key, label in _rate_price_labels().items():
        value = rates[key]
        if key in {"pro_price", "ent_price"}:
            formatted = f"{value:,.2f} EUR"
        else:
            formatted = f"{value:.2%}"
        rows.append({"Metric": label, "Value": formatted})

    st.dataframe(rows, use_container_width=True)
    _render_source(_map_value_to_rates_prices)


def _render_interest_calculator(assumptions: Assumptions) -> None:
    st.markdown("#### Debt interest rate")
    debt = st.slider(
        "Outstanding debt (EUR)",
        min_value=0.0,
        max_value=1_000_000.0,
        value=0.0,
        step=10_000.0,
    )
    rate = _effective_interest_rate_annual(debt, assumptions)
    st.metric("Annual interest rate", f"{rate:.2%}")
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Base annual rate", f"{assumptions.debt_interest_rate_base_annual:.2%}"
    )
    col2.metric("Sensitivity k", f"{assumptions.debt_interest_rate_k:.2f}")
    col3.metric("Reference debt", f"{assumptions.debt_interest_rate_ref:,.0f} EUR")
    _render_source(_effective_interest_rate_annual)


def _render_source(func: Callable[..., object]) -> None:
    with st.expander(f"View source: {func.__name__}"):
        try:
            source = inspect.getsource(func)
        except OSError:
            source = "Source unavailable."
        st.code(source, language="python")


def _rate_price_labels() -> dict[str, str]:
    return {
        "pro_price": "Pro price",
        "ent_price": "Enterprise price",
        "conv_web_to_lead_eff": "Web to lead conversion",
        "conv_website_lead_to_free_eff": "Website lead to free",
        "conv_website_lead_to_pro_eff": "Website lead to pro",
        "conv_website_lead_to_ent_eff": "Website lead to enterprise",
        "conv_outreach_lead_to_free_eff": "Outreach lead to free",
        "conv_outreach_lead_to_pro_eff": "Outreach lead to pro",
        "conv_outreach_lead_to_ent_eff": "Outreach lead to enterprise",
        "upgrade_free_to_pro_eff": "Free to pro upgrade",
        "upgrade_pro_to_ent_eff": "Pro to enterprise upgrade",
        "churn_free_eff": "Free churn",
        "churn_pro_eff": "Pro churn",
        "churn_ent_eff": "Enterprise churn",
    }
