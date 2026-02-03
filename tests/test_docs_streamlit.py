from __future__ import annotations

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.docs_streamlit import (
    _base_state,
    _build_mermaid_html,
    _map_rates_prices_preview,
    _with_decision_overrides,
)
from otai_forecast.models import MonthlyDecision


def test_build_mermaid_html_wraps_diagram() -> None:
    diagram = "graph TD\nA-->B"
    html = _build_mermaid_html(diagram)
    assert "mermaid" in html
    assert diagram in html


def test_base_state_defaults_to_assumptions() -> None:
    state = _base_state(DEFAULT_ASSUMPTIONS)
    assert state.cash == DEFAULT_ASSUMPTIONS.starting_cash
    assert state.domain_rating == DEFAULT_ASSUMPTIONS.domain_rating_init
    assert state.product_value == DEFAULT_ASSUMPTIONS.pv_init
    assert state.qualified_pool_remaining == DEFAULT_ASSUMPTIONS.qualified_pool_total


def test_with_decision_overrides_updates_fields() -> None:
    decision = MonthlyDecision(
        ads_budget=1.0,
        seo_budget=2.0,
        dev_budget=3.0,
        partner_budget=4.0,
        outreach_budget=5.0,
        pro_price_override=None,
        ent_price_override=None,
    )
    updated = _with_decision_overrides(decision, ads_budget=10.0)
    assert updated.ads_budget == 10.0
    assert updated.seo_budget == decision.seo_budget


def test_map_rates_prices_preview_respects_base_values() -> None:
    decision = MonthlyDecision(
        ads_budget=10_000.0,
        seo_budget=10_000.0,
        dev_budget=50_000.0,
        partner_budget=1_000.0,
        outreach_budget=10_000.0,
        pro_price_override=None,
        ent_price_override=None,
    )
    rates = _map_rates_prices_preview(DEFAULT_ASSUMPTIONS.pv_init, DEFAULT_ASSUMPTIONS, decision)
    milestone = DEFAULT_ASSUMPTIONS.pricing_milestones[-1]
    assert rates["pro_price"] == milestone.pro_price
    assert rates["ent_price"] == milestone.ent_price
    assert rates["conv_web_to_lead_eff"] == DEFAULT_ASSUMPTIONS.conv_web_to_lead
    assert (
        rates["conv_website_lead_to_free_eff"]
        == DEFAULT_ASSUMPTIONS.conv_website_lead_to_free
    )
