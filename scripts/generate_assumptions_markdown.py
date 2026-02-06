"""Generate a markdown report for the current DEFAULT_ASSUMPTIONS."""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from otai_forecast.config import DEFAULT_ASSUMPTIONS
from otai_forecast.compute import (
    _effective_cpc,
    _effective_interest_rate_annual,
    _milestone_for_value,
    _prices_for_value,
    _update_domain_rating,
    _update_product_value,
)
from otai_forecast.models import Assumptions, MonthlyDecision, State


def _format_percent(value: float) -> str:
    return f"{value:.2%}"


def _format_number(value: float) -> str:
    return f"{value:,.2f}"


def _format_currency(value: float) -> str:
    return f"{value:,.2f} EUR"


def build_documentation() -> str:
    """Build the documentation content with static mermaid diagrams."""
    lines = []
    
    lines.append("# OTAI Simulation Documentation")
    lines.append("")
    lines.append("Use this page to explore the calculations from ``compute.py`` without duplicating logic.")
    lines.append("")
    
    lines.append("## How the app works")
    lines.append("")
    lines.append("""
The Streamlit app exposes three main tabs:

- **Assumptions**: Shows the fixed model inputs used by the simulator and the optimizer.
- **Results**: Displays KPIs, charts, and detailed tables after a run.
- **Documentation**: Explains the mechanics behind growth, pricing, and finance.

The simulation follows a monthly loop. For each month, the engine updates product value,
marketing-driven acquisition, conversions, revenue, costs, and then produces a new
immutable state snapshot. The charts and tables in the Results tab are derived directly
from these monthly state rows.
""")
    lines.append("")
    
    lines.append("## Core assumptions")
    lines.append("")
    lines.append("""
Assumptions define the business environment and constraints:

- **Acquisition dynamics**: CPC curves and SEO efficiency control how marketing spend
  translates into new leads and qualified traffic.
- **Conversion funnel**: Web-to-lead, lead-to-tier, and upgrade rates model the journey
  from visitor → free → paid → enterprise.
- **Pricing milestones**: Product value gates determine pro/enterprise pricing tiers.
- **Finance rules**: Taxes, operating costs, and debt mechanics ensure cash flow
  constraints are enforced.
""")
    lines.append("")
    
    lines.append("## Decision inputs")
    lines.append("")
    lines.append("""
Each month, you can adjust five decision levers: ads budget, SEO budget, development
budget, partner budget, and outreach budget. The simulator uses these to compute
marketing efficiency, product value improvements, and revenue growth. Optional price
overrides allow manual pricing experiments while keeping other assumptions intact.
""")
    lines.append("")
    
    lines.append("## Decision optimizer")
    lines.append("")
    lines.append("""
The optimizer (``decision_optimizer.choose_best_decisions_by_market_cap``) uses
Optuna's TPE sampler to search for the monthly budget schedule that maximizes
final market cap. It works by:

1. Sampling **knot values** for each budget lever (ads/SEO/dev/partner/outreach).
2. Interpolating those knots into smooth monthly multipliers.
3. Running the full simulation and scoring the outcome by market cap
   (TTM revenue × multiple + cash − 2×debt).
4. Rejecting trials with invalid states or negative cash flow.
""")
    lines.append("")
    
    lines.append("## Monthly flow")
    lines.append("")
    lines.append("```mermaid")
    lines.append("graph TD")
    lines.append("    A[Monthly decision] --> B[Update product value]")
    lines.append("    B --> C[Effective conversions and pricing]")
    lines.append("    C --> D[Lead generation]")
    lines.append("    D --> E[Customer changes]")
    lines.append("    E --> F[Revenue and costs]")
    lines.append("    F --> G[State update]")
    lines.append("```")
    lines.append("")
    
    lines.append("## Calculation Formulas")
    lines.append("")
    lines.append("### Effective CPC")
    lines.append("")
    lines.append("```")
    lines.append("CPC_eff = CPC_base × (1 + k × ln(1 + spend / spend_ref))")
    lines.append("```")
    lines.append("")
    lines.append(f"- **Base CPC**: {DEFAULT_ASSUMPTIONS.cpc_base:.2f} EUR")
    lines.append(f"- **Sensitivity k**: {DEFAULT_ASSUMPTIONS.cpc_sensitivity_factor:.2f}")
    lines.append(f"- **Reference spend**: {DEFAULT_ASSUMPTIONS.cpc_ref_spend:,.0f} EUR")
    lines.append("")
    
    lines.append("### Domain rating update")
    lines.append("")
    lines.append("```")
    lines.append("DR_next = DR × (1 - decay) + (DR_max - DR) × k × ln(1 + spend / spend_ref)")
    lines.append("```")
    lines.append("")
    lines.append(f"- **DR max**: {DEFAULT_ASSUMPTIONS.domain_rating_max:.0f}")
    lines.append(f"- **Sensitivity k**: {DEFAULT_ASSUMPTIONS.domain_rating_spend_sensitivity:.2f}")
    lines.append(f"- **Reference spend**: {DEFAULT_ASSUMPTIONS.domain_rating_reference_spend_eur:,.0f} EUR")
    lines.append(f"- **Monthly decay**: {DEFAULT_ASSUMPTIONS.domain_rating_decay:.1%}")
    lines.append("")
    
    lines.append("### Product value update")
    lines.append("")
    lines.append("Product value accumulates with dev spend and depreciates at a fixed monthly rate.")
    lines.append("")
    lines.append(f"- **PV min**: {DEFAULT_ASSUMPTIONS.pv_min:.0f}")
    lines.append(f"- **Depreciation rate**: {DEFAULT_ASSUMPTIONS.product_value_depreciation_rate:.1%}")
    lines.append("")
    
    lines.append("### Conversions and pricing")
    lines.append("")
    lines.append("Conversion rates and pricing are determined by product value milestones.")
    lines.append("")
    lines.append("| Metric | Rate |")
    lines.append("| --- | --- |")
    lines.append(f"| Web -> Lead | {DEFAULT_ASSUMPTIONS.conv_web_to_lead:.2%} |")
    lines.append(f"| Lead -> Free | {DEFAULT_ASSUMPTIONS.conv_website_lead_to_free:.2%} |")
    lines.append(f"| Lead -> Pro | {DEFAULT_ASSUMPTIONS.conv_website_lead_to_pro:.2%} |")
    lines.append(f"| Lead -> Enterprise | {DEFAULT_ASSUMPTIONS.conv_website_lead_to_ent:.2%} |")
    lines.append(f"| Free -> Pro | {DEFAULT_ASSUMPTIONS.conv_free_to_pro:.2%} |")
    lines.append(f"| Pro -> Enterprise | {DEFAULT_ASSUMPTIONS.conv_pro_to_ent:.2%} |")
    lines.append(f"| Churn (Free) | {DEFAULT_ASSUMPTIONS.churn_free:.2%} |")
    lines.append(f"| Churn (Pro) | {DEFAULT_ASSUMPTIONS.churn_pro:.2%} |")
    lines.append(f"| Churn (Enterprise) | {DEFAULT_ASSUMPTIONS.churn_ent:.2%} |")
    lines.append("")
    
    lines.append("### Debt interest rate")
    lines.append("")
    lines.append(f"- **Base annual rate**: {DEFAULT_ASSUMPTIONS.debt_interest_rate_base_annual:.2%}")
    lines.append("")
    
    return "\n".join(lines)


def build_markdown() -> str:
    a = DEFAULT_ASSUMPTIONS
    lines: list[str] = []

    lines.append("# OTAI Default Assumptions")
    lines.append("")
    lines.append("This document outlines the default assumptions and parameters used in the OTAI Financial Forecasting System. These values drive the simulation's behavior and represent realistic business metrics for a B2B SaaS company.")
    lines.append("")
    lines.append("The simulation models monthly business operations including customer acquisition, conversion funnels, pricing strategies, operating costs, and financial dynamics. Each section below explains a key aspect of the business model.")
    lines.append("")

    lines.append("## Simulation Overview")
    lines.append("")
    lines.append("The simulation runs on a monthly basis for a specified period, starting with initial cash and tracking all financial metrics. Users are acquired through paid ads and SEO efforts.")
    lines.append("")
    lines.append("The market cap multiple determines the company's valuation based on trailing twelve-month (TTM) revenue, while the tax rate is applied to profits for cash flow calculations.")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Months | {a.months} |")
    lines.append(f"| Starting cash | {_format_currency(a.starting_cash)} |")
    lines.append(f"| Market cap multiple | {_format_number(a.market_cap_multiple)}x |")
    lines.append(f"| Tax rate | {_format_percent(a.tax_rate)} |")
    lines.append("")

    lines.append("## Acquisition Levers")
    lines.append("")
    lines.append("The simulation models three primary customer acquisition channels, each with distinct cost structures and effectiveness metrics.")
    lines.append("")
    lines.append("### Ads (CPC model)")
    lines.append("")
    lines.append("Paid advertising operates on a cost-per-click (CPC) model with diminishing returns. As spend increases, the effective CPC rises due to increased competition and audience saturation.")
    lines.append("")
    lines.append("The sensitivity factor determines how quickly CPC increases with spend, while the reference spend provides a baseline for calculations.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Base CPC | {_format_currency(a.cpc_base)} |")
    lines.append(f"| CPC sensitivity | {_format_number(a.cpc_sensitivity_factor)} |")
    lines.append(f"| CPC reference spend | {_format_currency(a.cpc_ref_spend)} |")
    lines.append("")

    lines.append("### SEO (Domain rating + organic lift)")
    lines.append("")
    lines.append("SEO investment improves domain authority and organic search visibility. The domain rating (DR) starts at an initial value and can increase up to a maximum based on SEO spend.")
    lines.append("")
    lines.append("DR naturally decays over time without ongoing investment, requiring consistent spend to maintain rankings. The users per EUR ratio represents the organic traffic generated per euro of SEO investment.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Users per EUR | {_format_number(a.seo_users_per_eur)} |")
    lines.append(f"| Domain rating init | {_format_number(a.domain_rating_init)} |")
    lines.append(f"| Domain rating max | {_format_number(a.domain_rating_max)} |")
    lines.append(f"| DR spend sensitivity | {_format_number(a.domain_rating_spend_sensitivity)} |")
    lines.append(f"| DR reference spend | {_format_currency(a.domain_rating_reference_spend_eur)} |")
    lines.append(f"| DR monthly decay | {_format_percent(a.domain_rating_decay)} |")
    lines.append("")

    lines.append("## Conversion Funnel")
    lines.append("")
    lines.append("The conversion funnel tracks user progression through various stages, from initial website visit to paid subscription. The model includes both website-driven conversions and direct outreach efforts.")
    lines.append("")
    lines.append("### Website funnel")
    lines.append("")
    lines.append("Website visitors convert to leads at a base rate, then can be acquired as free, pro, or enterprise users. The conversion rates reflect typical B2B SaaS metrics where free trials have higher conversion than paid plans.")
    lines.append("")
    lines.append("| Step | Conversion |")
    lines.append("| --- | --- |")
    lines.append(f"| Web -> Lead | {_format_percent(a.conv_web_to_lead)} |")
    lines.append(f"| Lead -> Free | {_format_percent(a.conv_website_lead_to_free)} |")
    lines.append(f"| Lead -> Pro | {_format_percent(a.conv_website_lead_to_pro)} |")
    lines.append(f"| Lead -> Enterprise | {_format_percent(a.conv_website_lead_to_ent)} |")
    lines.append("")

    lines.append("### Direct outreach funnel")
    lines.append("")
    lines.append("Direct outreach targets qualified leads through personalized contact. This channel typically has higher conversion rates but requires more manual effort. The funnel progresses from contacted leads to demo appointments to conversions.")
    lines.append("")
    lines.append("| Step | Conversion |")
    lines.append("| --- | --- |")
    lines.append(f"| Direct lead -> Demo | {_format_percent(a.direct_contacted_demo_conversion)} |")
    lines.append(f"| Demo -> Free | {_format_percent(a.direct_demo_appointment_conversion_to_free)} |")
    lines.append(f"| Demo -> Pro | {_format_percent(a.direct_demo_appointment_conversion_to_pro)} |")
    lines.append(f"| Demo -> Enterprise | {_format_percent(a.direct_demo_appointment_conversion_to_ent)} |")
    lines.append("")

    lines.append("### Upgrades and churn")
    lines.append("")
    lines.append("Users can upgrade between tiers over time, with free users potentially becoming pro users, and pro users upgrading to enterprise. Churn represents the monthly percentage of users who cancel their subscriptions in each tier.")
    lines.append("")
    lines.append("| Step | Rate |")
    lines.append("| --- | --- |")
    lines.append(f"| Free -> Pro | {_format_percent(a.conv_free_to_pro)} |")
    lines.append(f"| Pro -> Enterprise | {_format_percent(a.conv_pro_to_ent)} |")
    lines.append(f"| Churn (Free) | {_format_percent(a.churn_free)} |")
    lines.append(f"| Churn (Pro) | {_format_percent(a.churn_pro)} |")
    lines.append(f"| Churn (Enterprise) | {_format_percent(a.churn_ent)} |")
    lines.append("")

    lines.append("### Conversion diagrams")
    lines.append("")
    lines.append("```mermaid")
    lines.append("flowchart LR")
    lines.append("    WebVisitors[Website Visitors] -->|conv_web_to_lead| WebLeads[Website Leads]")
    lines.append("    WebLeads -->|lead_to_free| FreeUsers[Free Users]")
    lines.append("    WebLeads -->|lead_to_pro| ProUsers[Pro Users]")
    lines.append("    WebLeads -->|lead_to_ent| EntUsers[Enterprise Users]")
    lines.append("    FreeUsers -->|conv_free_to_pro| ProUsers")
    lines.append("    ProUsers -->|conv_pro_to_ent| EntUsers")
    lines.append("    DirectLeads[Direct Leads] -->|direct_demo| Demo[Demo Appointment]")
    lines.append("    Demo -->|demo_to_free| FreeUsers")
    lines.append("    Demo -->|demo_to_pro| ProUsers")
    lines.append("    Demo -->|demo_to_ent| EntUsers")
    lines.append("    FreeUsers -. churn_free .-> Churn[Churned]")
    lines.append("    ProUsers -. churn_pro .-> Churn")
    lines.append("    EntUsers -. churn_ent .-> Churn")
    lines.append("```")
    lines.append("")

    lines.append("## Pricing Milestones")
    lines.append("")
    lines.append("Pricing evolves as the product gains value through development. Each milestone represents a stage where the product value justifies higher pricing. The pro and enterprise prices increase as the minimum product value threshold is met.")
    lines.append("")
    lines.append("This models a real-world scenario where SaaS companies increase prices as their product becomes more valuable and feature-rich.")
    lines.append("")
    lines.append("| Milestone | Product value min | Pro price | Enterprise price |")
    lines.append("| --- | --- | --- | --- |")
    for idx, milestone in enumerate(a.pricing_milestones, start=1):
        lines.append(
            f"| v{idx} | {_format_currency(milestone.product_value_min)} |"
            f" {_format_currency(milestone.pro_price)} | {_format_currency(milestone.ent_price)} |"
        )
    lines.append("")

    lines.append("## Sales & Support Costs")
    lines.append("")
    lines.append("Sales costs are incurred when acquiring new paid customers, reflecting the effort needed to close deals. Support costs are ongoing expenses per customer, with some covered by subscription fees and take rates.")
    lines.append("")
    lines.append("The support fee percentage represents what customers pay for premium support, while the take rate shows what percentage actually opt for paid support.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Sales cost / new pro | {_format_currency(a.sales_cost_per_new_pro)} |")
    lines.append(f"| Sales cost / new enterprise | {_format_currency(a.sales_cost_per_new_ent)} |")
    lines.append(f"| Support cost / pro | {_format_currency(a.support_cost_per_pro)} |")
    lines.append(f"| Support cost / enterprise | {_format_currency(a.support_cost_per_ent)} |")
    lines.append(f"| Support fee pct (pro) | {_format_percent(a.support_subscription_fee_pct_pro)} |")
    lines.append(f"| Support fee pct (ent) | {_format_percent(a.support_subscription_fee_pct_ent)} |")
    lines.append(f"| Support take rate (pro) | {_format_percent(a.support_subscription_take_rate_pro)} |")
    lines.append(f"| Support take rate (ent) | {_format_percent(a.support_subscription_take_rate_ent)} |")
    lines.append("")

    lines.append("## Partner Program")
    lines.append("")
    lines.append("The partner program leverages third-party resellers to acquire customers. Partners generate deals based on their investment and the product's value proposition. The commission rate reflects the partner's share of revenue.")
    lines.append("")
    lines.append("Partner churn represents the monthly loss of partners, while deals per partner per month show the expected sales velocity from active partners.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Partner spend ref | {_format_currency(a.partner_spend_ref)} |")
    lines.append(f"| Partner product value ref | {_format_currency(a.partner_product_value_ref)} |")
    lines.append(f"| Partner commission rate | {_format_percent(a.partner_commission_rate)} |")
    lines.append(f"| Partner churn / month | {_format_percent(a.partner_churn_per_month)} |")
    lines.append(f"| Pro deals / partner / month | {_format_number(a.partner_pro_deals_per_partner_per_month)} |")
    lines.append(f"| Enterprise deals / partner / month | {_format_number(a.partner_ent_deals_per_partner_per_month)} |")
    lines.append("")

    lines.append("## Operating Costs")
    lines.append("")
    lines.append("Operating costs include both fixed baseline expenses and variable costs that scale with user count and development investment. The per-dev cost represents additional overhead for each euro spent on development.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Baseline | {_format_currency(a.operating_baseline)} |")
    lines.append(f"| Per user | {_format_currency(a.operating_per_user)} |")
    lines.append(f"| Per dev spend EUR | {_format_number(a.operating_per_dev)} |")
    lines.append("")

    lines.append("## Outreach + Scraping")
    lines.append("")
    lines.append("The qualified pool represents the total addressable market for direct outreach. Scraping efficiency determines how effectively the company can identify and contact potential customers from this pool.")
    lines.append("")
    lines.append("Costs per lead and demo reflect the manual effort required for direct sales activities, with diminishing returns as the easily reachable prospects are exhausted.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Qualified pool total | {_format_number(a.qualified_pool_total)} |")
    lines.append(f"| Scraping efficiency k | {_format_number(a.scraping_efficiency_k)} |")
    lines.append(f"| Scraping ref spend | {_format_currency(a.scraping_ref_spend)} |")
    lines.append(f"| Cost per direct lead | {_format_currency(a.cost_per_direct_lead)} |")
    lines.append(f"| Cost per direct demo | {_format_currency(a.cost_per_direct_demo)} |")
    lines.append("")

    lines.append("## Debt & Credit")
    lines.append("")
    lines.append("The simulation includes debt financing with variable interest rates based on the company's financial health. The credit draw factor determines how much of available credit is used when cash is low, while the debt repay factor controls repayment speed when cash is available.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Base annual interest rate | {_format_percent(a.debt_interest_rate_base_annual)} |")
    lines.append(f"| Credit draw factor | {_format_number(a.credit_draw_factor)} |")
    lines.append(f"| Debt repay factor | {_format_number(a.debt_repay_factor)} |")
    lines.append("")

    lines.append("## Product Value Dynamics")
    lines.append("")
    lines.append("Product value represents the perceived worth of the software to customers. It starts at an initial level and can depreciate without ongoing development investment. Achieving pricing milestones requires meeting minimum product value thresholds.")
    lines.append("")
    lines.append("When milestones are achieved, a percentage of customers renew at the new pricing, with discounts applied for early renewal to encourage upgrades.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| PV init | {_format_currency(a.pv_init)} |")
    lines.append(f"| PV min | {_format_currency(a.pv_min)} |")
    lines.append(f"| Depreciation rate | {_format_percent(a.product_value_depreciation_rate)} |")
    lines.append(f"| Milestone renewal % | {_format_percent(a.milestone_achieved_renewal_percentage)} |")
    lines.append(f"| Renewal discount % | {_format_percent(a.product_renewal_discount_percentage)} |")
    lines.append("")

    lines.append("## Cost Categories")
    lines.append("")
    lines.append("Payment processing fees are applied to all revenue transactions. The dev CAPEX ratio determines what portion of development spending is treated as capital expenditure rather than operating expense, affecting financial statements.")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Payment processing rate | {_format_percent(a.payment_processing_rate)} |")
    lines.append(f"| Dev CAPEX ratio | {_format_percent(a.dev_capex_ratio)} |")
    lines.append("")

    return "\n".join(lines)


def write_markdown(output_path: Path) -> None:
    """Write both the assumptions documentation and the general documentation."""
    # Write assumptions documentation
    assumptions_path = output_path / "default_assumptions.md"
    assumptions_path.write_text(build_markdown(), encoding="utf-8")
    
    # Write general documentation
    docs_path = output_path / "documentation.md"
    docs_path.write_text(build_documentation(), encoding="utf-8")


def main() -> None:
    output_path = Path(__file__).parent.parent / "docs"
    write_markdown(output_path)
    print(f"Wrote documentation to {output_path}")


if __name__ == "__main__":
    main()
