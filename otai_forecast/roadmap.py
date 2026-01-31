"""Roadmap definition for Open Ticket AI Products."""

from otai_forecast.effects import (
    effect_boost_conversion,
    effect_boost_free_to_pro,
    effect_boost_pro_to_ent,
    effect_increase_price,
    effect_reduce_churn,
)
from otai_forecast.models import Feature, Roadmap


def create_otai_roadmap() -> Roadmap:
    """Create the comprehensive roadmap for OTAI products."""

    features: list[Feature] = [
        # Pre-Product Phase (Jan-Mar 2026)
        Feature(
            name="Tagging System",
            dev_days=30 * 3,  # 3 months
            maintenance_days_per_month=5.0,
            effect=effect_boost_conversion(0.05),  # 5% boost to lead conversion
        ),
        Feature(
            name="Mapping Engine",
            dev_days=30 * 3,  # 3 months
            maintenance_days_per_month=5.0,
            effect=effect_boost_conversion(0.03),  # 3% boost to lead conversion
        ),
        Feature(
            name="Studio V1",
            dev_days=30 * 3,  # 3 months
            maintenance_days_per_month=8.0,
            effect=effect_boost_free_to_pro(0.10),  # 10% boost to free->pro conversion
        ),
        # V1 Launch (Apr-Jun 2026)
        Feature(
            name="AI Summaries",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=6.0,
            effect=effect_increase_price(0.10),  # 10% price increase
        ),
        Feature(
            name="Insights Dashboard",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=6.0,
            effect=effect_boost_pro_to_ent(0.15),  # 15% boost to pro->ent conversion
        ),
        Feature(
            name="Advanced Tags (Synthetic)",
            dev_days=30 * 1.5,  # 1.5 months
            maintenance_days_per_month=4.0,
            effect=effect_boost_conversion(0.04),  # 4% boost to lead conversion
        ),
        # Observatory (Jul-Sep 2026)
        Feature(
            name="Statistics Engine",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=7.0,
            effect=effect_reduce_churn("pro", 0.20),  # 20% reduction in pro churn
        ),
        Feature(
            name="Analytics Suite",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=7.0,
            effect=effect_increase_price(0.15),  # 15% price increase
        ),
        Feature(
            name="Reporting Tools",
            dev_days=30 * 1,  # 1 month
            maintenance_days_per_month=5.0,
            effect=effect_boost_pro_to_ent(0.10),  # 10% boost to pro->ent conversion
        ),
        # Studio Update (Oct-Dec 2026)
        Feature(
            name="Visual Editor",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=8.0,
            effect=effect_boost_free_to_pro(0.20),  # 20% boost to free->pro conversion
        ),
        Feature(
            name="Flow Builder",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=8.0,
            effect=effect_increase_price(0.20),  # 20% price increase
        ),
        Feature(
            name="Template Library",
            dev_days=30 * 1,  # 1 month
            maintenance_days_per_month=4.0,
            effect=effect_reduce_churn("free", 0.15),  # 15% reduction in free churn
        ),
        # Automation Suite (Jan-Mar 2027)
        Feature(
            name="Draft Generation",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=8.0,
            effect=effect_increase_price(0.25),  # 25% price increase
        ),
        Feature(
            name="Auto-Categorization",
            dev_days=30 * 1.5,  # 1.5 months
            maintenance_days_per_month=6.0,
            effect=effect_boost_conversion(0.08),  # 8% boost to lead conversion
        ),
        Feature(
            name="Smart Routing",
            dev_days=30 * 1.5,  # 1.5 months
            maintenance_days_per_month=6.0,
            effect=effect_reduce_churn("ent", 0.25),  # 25% reduction in ent churn
        ),
        # V2 Neural (Apr-Jun 2027)
        Feature(
            name="Custom Bot Builder",
            dev_days=30 * 2.5,  # 2.5 months
            maintenance_days_per_month=10.0,
            effect=effect_increase_price(0.30),  # 30% price increase
        ),
        Feature(
            name="Neural Search",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=8.0,
            effect=effect_boost_conversion(0.10),  # 10% boost to lead conversion
        ),
        Feature(
            name="Predictive Analytics",
            dev_days=30 * 1.5,  # 1.5 months
            maintenance_days_per_month=7.0,
            effect=effect_boost_pro_to_ent(0.25),  # 25% boost to pro->ent conversion
        ),
        # Chatbot Expansion (Jul-Sep 2027)
        Feature(
            name="User-Facing Chatbot",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=9.0,
            effect=effect_increase_price(0.20),  # 20% price increase
        ),
        Feature(
            name="Multi-Language Support",
            dev_days=30 * 1.5,  # 1.5 months
            maintenance_days_per_month=6.0,
            effect=effect_boost_conversion(0.12),  # 12% boost to lead conversion
        ),
        Feature(
            name="Chat Analytics",
            dev_days=30 * 1,  # 1 month
            maintenance_days_per_month=5.0,
            effect=effect_reduce_churn("pro", 0.15),  # 15% reduction in pro churn
        ),
        # Internal Bot (Oct-Dec 2027)
        Feature(
            name="Internal Support Bot",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=8.0,
            effect=effect_boost_conversion(0.06),  # 6% boost to lead conversion
        ),
        Feature(
            name="Knowledge Base Integration",
            dev_days=30 * 1.5,  # 1.5 months
            maintenance_days_per_month=6.0,
            effect=effect_reduce_churn("ent", 0.20),  # 20% reduction in ent churn
        ),
        Feature(
            name="Workflow Automation",
            dev_days=30 * 2,  # 2 months
            maintenance_days_per_month=9.0,
            effect=effect_increase_price(0.15),  # 15% price increase
        ),
    ]

    return Roadmap(features=features)


# Quarterly roadmap summaries for easier viewing
QUARTERLY_ROADMAP = {
    "Q1 2026 (Pre-Product)": [
        "Tagging System",
        "Mapping Engine",
        "Studio V1",
    ],
    "Q2 2026 (V1 Launch)": [
        "AI Summaries",
        "Insights Dashboard",
        "Advanced Tags (Synthetic)",
    ],
    "Q3 2026 (Observatory)": [
        "Statistics Engine",
        "Analytics Suite",
        "Reporting Tools",
    ],
    "Q4 2026 (Studio Update)": [
        "Visual Editor",
        "Flow Builder",
        "Template Library",
    ],
    "Q1 2027 (Automation Suite)": [
        "Draft Generation",
        "Auto-Categorization",
        "Smart Routing",
    ],
    "Q2 2027 (V2 Neural)": [
        "Custom Bot Builder",
        "Neural Search",
        "Predictive Analytics",
    ],
    "Q3 2027 (Chatbot Expansion)": [
        "User-Facing Chatbot",
        "Multi-Language Support",
        "Chat Analytics",
    ],
    "Q4 2027 (Internal Bot)": [
        "Internal Support Bot",
        "Knowledge Base Integration",
        "Workflow Automation",
    ],
}


# Feature impact summary
FEATURE_IMPACTS = {
    "Price Increases": [
        "AI Summaries (+10%)",
        "Analytics Suite (+15%)",
        "Flow Builder (+20%)",
        "Draft Generation (+25%)",
        "Custom Bot Builder (+30%)",
        "User-Facing Chatbot (+20%)",
        "Workflow Automation (+15%)",
    ],
    "Conversion Boosts": [
        "Tagging System (+5% leads)",
        "Mapping Engine (+3% leads)",
        "Advanced Tags (+4% leads)",
        "Auto-Categorization (+8% leads)",
        "Neural Search (+10% leads)",
        "Multi-Language Support (+12% leads)",
        "Internal Support Bot (+6% leads)",
    ],
    "Churn Reduction": [
        "Statistics Engine (-20% pro churn)",
        "Template Library (-15% free churn)",
        "Smart Routing (-25% ent churn)",
        "Chat Analytics (-15% pro churn)",
        "Knowledge Base Integration (-20% ent churn)",
    ],
    "Upgrade Conversion": [
        "Studio V1 (+10% free to pro)",
        "Insights Dashboard (+15% pro to ent)",
        "Reporting Tools (+10% pro to ent)",
        "Visual Editor (+20% free to pro)",
        "Predictive Analytics (+25% pro to ent)",
    ],
}
