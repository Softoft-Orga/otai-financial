"""Centralized plotting functions for OTAI financial simulation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PLOTLY_TEMPLATE = "plotly_white"
PLOTLY_COLORWAY = [
    "#2563EB",
    "#10B981",
    "#F97316",
    "#EF4444",
    "#8B5CF6",
    "#0EA5E9",
    "#F59E0B",
    "#14B8A6",
]


def _series_or_zeros(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series(np.zeros(len(df)), index=df.index)


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return (numerator / denominator.replace(0, np.nan)).fillna(0)


def _apply_currency_axis(
    fig: go.Figure,
    *,
    title: str | None = None,
    row: int | None = None,
    col: int | None = None,
    secondary_y: bool = False,
) -> None:
    # Only use row/col if the figure has subplots
    if row is not None or col is not None or secondary_y:
        # Check if figure has subplot grid
        try:
            fig.update_yaxes(
                title_text=title,
                tickprefix="€",
                tickformat="~s",
                row=row,
                col=col,
                secondary_y=secondary_y,
            )
        except Exception:
            # Fallback for figures without subplots
            fig.update_yaxes(
                title_text=title,
                tickprefix="€",
                tickformat="~s",
            )
    else:
        fig.update_yaxes(
            title_text=title,
            tickprefix="€",
            tickformat="~s",
        )


def _apply_count_axis(
    fig: go.Figure,
    *,
    title: str | None = None,
    row: int | None = None,
    col: int | None = None,
    secondary_y: bool = False,
) -> None:
    # Only use row/col if the figure has subplots
    if row is not None or col is not None or secondary_y:
        try:
            fig.update_yaxes(
                title_text=title,
                tickformat="~s",
                row=row,
                col=col,
                secondary_y=secondary_y,
            )
        except Exception:
            # Fallback for figures without subplots
            fig.update_yaxes(
                title_text=title,
                tickformat="~s",
            )
    else:
        fig.update_yaxes(
            title_text=title,
            tickformat="~s",
        )


def _apply_percent_axis(
    fig: go.Figure,
    *,
    title: str | None = None,
    row: int | None = None,
    col: int | None = None,
    secondary_y: bool = False,
) -> None:
    # Only use row/col if the figure has subplots
    if row is not None or col is not None or secondary_y:
        try:
            fig.update_yaxes(
                title_text=title,
                tickformat=".1%",
                row=row,
                col=col,
                secondary_y=secondary_y,
            )
        except Exception:
            # Fallback for figures without subplots
            fig.update_yaxes(
                title_text=title,
                tickformat=".1%",
            )
    else:
        fig.update_yaxes(
            title_text=title,
            tickformat=".1%",
        )


def _add_traces_from_fig(
    target_fig: go.Figure,
    source_fig: go.Figure,
    *,
    row: int,
    col: int,
) -> None:
    for trace in source_fig.data:
        secondary = getattr(trace, "yaxis", "y") == "y2"
        target_fig.add_trace(trace, row=row, col=col, secondary_y=secondary)


def plot_cash_debt_spend(df: pd.DataFrame) -> go.Figure:
    """Plot cash position, debt, and spend over time."""
    total_spend = (
        _series_or_zeros(df, "ads_spend")
        + _series_or_zeros(df, "organic_marketing_spend")
        + _series_or_zeros(df, "dev_spend")
        + _series_or_zeros(df, "partner_spend")
        + _series_or_zeros(df, "direct_candidate_outreach_spend")
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=df["month"],
            y=total_spend,
            name="Total Spend",
            marker_color="#F97316",
            opacity=0.4,
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "cash"),
            name="Cash Position",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "debt"),
            name="Debt",
            mode="lines+markers",
            line=dict(color="#EF4444", width=3),
            fill="tozeroy",
            fillcolor="rgba(239, 68, 68, 0.2)",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Cash Position, Debt, and Monthly Spend",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Cash / Spend (€)", row=1, col=1)
    _apply_currency_axis(fig, title="Debt (€)", row=1, col=1, secondary_y=True)
    return fig


def plot_costs_breakdown(df: pd.DataFrame) -> go.Figure:
    """Plot cost breakdown by expense type over time."""
    cost_categories = [
        "cost_sales_marketing",
        "cost_rd_expense",
        "cost_ga",
        "cost_customer_support",
        "cost_it_tools",
        "cost_payment_processing",
        "cost_outreach_conversion",
        "cost_partner_commission",
    ]
    category_labels = [
        "Sales & Marketing",
        "R&D Expense",
        "General & Admin",
        "Customer Support",
        "IT & Tools",
        "Payment Processing",
        "Outreach Conversion",
        "Partner Commission",
    ]
    colors = [
        "#F97316",
        "#2563EB",
        "#10B981",
        "#EC4899",
        "#14B8A6",
        "#F59E0B",
        "#8B5CF6",
        "#64748B",
    ]

    fig = go.Figure()
    for column, label, color in zip(cost_categories, category_labels, colors, strict=True):
        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=_series_or_zeros(df, column),
                name=label,
                stackgroup="costs",
                mode="lines",
                line=dict(width=0.5, color=color),
            )
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Cost Breakdown by Expense Type",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Costs (€)")
    return fig


def plot_revenue_split(df: pd.DataFrame, *, embedded: bool = False) -> go.Figure:
    """Plot revenue split by source and type."""
    license_cols = [
        "revenue_pro_website",
        "revenue_pro_outreach",
        "revenue_pro_partner",
        "revenue_ent_website",
        "revenue_ent_outreach",
        "revenue_ent_partner",
    ]
    license_labels = [
        "Pro (Website)",
        "Pro (Outreach)",
        "Pro (Partner)",
        "Ent (Website)",
        "Ent (Outreach)",
        "Ent (Partner)",
    ]
    license_colors = [
        "#2563EB",
        "#1D4ED8",
        "#1E40AF",
        "#EF4444",
        "#DC2626",
        "#991B1B",
    ]

    recurring_cols = [
        "revenue_renewal_pro",
        "revenue_renewal_ent",
        "revenue_support_pro",
        "revenue_support_ent",
    ]
    recurring_labels = [
        "Renewals (Pro)",
        "Renewals (Ent)",
        "Support (Pro)",
        "Support (Ent)",
    ]
    recurring_colors = ["#10B981", "#059669", "#F59E0B", "#D97706"]

    if embedded:
        fig = go.Figure()
        for column, label, color in zip(
            license_cols, license_labels, license_colors, strict=True
        ):
            fig.add_trace(
                go.Scatter(
                    x=df["month"],
                    y=_series_or_zeros(df, column),
                    name=label,
                    stackgroup="license",
                    mode="lines",
                    line=dict(width=0.5, color=color),
                )
            )
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            title="License Sales Revenue",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        fig.update_xaxes(title_text="Month")
        _apply_currency_axis(fig, title="Revenue (€)")
        return fig

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("License Sales Revenue", "Recurring Revenue"),
    )
    for column, label, color in zip(
        license_cols, license_labels, license_colors, strict=True
    ):
        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=_series_or_zeros(df, column),
                name=label,
                stackgroup="license",
                mode="lines",
                line=dict(width=0.5, color=color),
            ),
            row=1,
            col=1,
        )
    for column, label, color in zip(
        recurring_cols, recurring_labels, recurring_colors, strict=True
    ):
        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=_series_or_zeros(df, column),
                name=label,
                stackgroup="recurring",
                mode="lines",
                line=dict(width=0.5, color=color),
            ),
            row=1,
            col=2,
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Revenue Breakdown by Source and Type",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=1, col=2)
    _apply_currency_axis(fig, title="Revenue (€)", row=1, col=1)
    _apply_currency_axis(fig, title="Revenue (€)", row=1, col=2)
    return fig


def plot_results(df: pd.DataFrame, save_path: str | None = None) -> go.Figure:
    """Create plots for the simulation results."""
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "User Growth Over Time",
            "Revenue and Net Cashflow",
            "Cash Position",
            "Market Cap (TTM Revenue × Multiple)",
        ),
        specs=[[{}, {"secondary_y": True}], [{}, {}]],
    )

    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "free_active"),
            name="Free Users",
            mode="lines+markers",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "pro_active"),
            name="Pro Users",
            mode="lines+markers",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "ent_active"),
            name="Enterprise Users",
            mode="lines+markers",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "revenue_total"),
            name="Revenue",
            mode="lines+markers",
            line=dict(color="#10B981"),
        ),
        row=1,
        col=2,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "net_cashflow"),
            name="Net Cashflow",
            mode="lines+markers",
            line=dict(color="#2563EB"),
        ),
        row=1,
        col=2,
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "cash"),
            name="Cash Position",
            mode="lines+markers",
            line=dict(color="#8B5CF6"),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "market_cap"),
            name="Market Cap",
            mode="lines+markers",
            line=dict(color="#F97316"),
        ),
        row=2,
        col=2,
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="OTAI Financial Simulation Results",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
        colorway=PLOTLY_COLORWAY,
        height=750,
    )
    for row in (1, 2):
        for col in (1, 2):
            fig.update_xaxes(title_text="Month", row=row, col=col)
    _apply_count_axis(fig, title="Active Users", row=1, col=1)
    _apply_currency_axis(fig, title="Revenue (€)", row=1, col=2, secondary_y=False)
    _apply_currency_axis(fig, title="Net Cashflow (€)", row=1, col=2, secondary_y=True)
    _apply_currency_axis(fig, title="Cash (€)", row=2, col=1)
    _apply_currency_axis(fig, title="Market Cap (€)", row=2, col=2)

    if save_path:
        fig.write_image(save_path, scale=2)

    return fig


def plot_user_growth(df: pd.DataFrame) -> go.Figure:
    """Plot user growth over time."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "free_active"),
            name="Free Users",
            mode="lines+markers",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "pro_active"),
            name="Pro Users",
            mode="lines+markers",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "ent_active"),
            name="Enterprise Users",
            mode="lines+markers",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="User Growth Over Time",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        colorway=PLOTLY_COLORWAY,
    )
    fig.update_xaxes(title_text="Month")
    _apply_count_axis(fig, title="Active Users")
    return fig


def plot_revenue_cashflow(df: pd.DataFrame) -> go.Figure:
    """Plot revenue and cashflow over time."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "revenue_total"),
            name="Revenue",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "net_cashflow"),
            name="Net Cashflow",
            mode="lines+markers",
            line=dict(color="#2563EB", width=3),
        ),
        secondary_y=True,
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Revenue and Net Cashflow",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Revenue (€)", row=1, col=1, secondary_y=False)
    _apply_currency_axis(fig, title="Net Cashflow (€)", row=1, col=1, secondary_y=True)
    return fig


def plot_cash_position(df: pd.DataFrame) -> go.Figure:
    """Plot cash position over time."""
    fig = go.Figure(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "cash"),
            mode="lines+markers",
            name="Cash",
            line=dict(color="#8B5CF6", width=3),
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Cash Position",
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Cash (€)")
    return fig


def plot_market_cap(df: pd.DataFrame) -> go.Figure:
    """Plot market cap with TTM Revenue, Cash, and Debt over time."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Primary Y-axis - Market Cap and TTM Revenue
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "market_cap"),
            name="Market Cap",
            mode="lines+markers",
            line=dict(color="#F97316", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "revenue_ttm"),
            name="TTM Revenue",
            mode="lines+markers",
            line=dict(color="#14B8A6", width=2, dash="dot"),
        ),
        secondary_y=False,
    )
    
    # Secondary Y-axis - Cash and Debt
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "cash"),
            name="Cash",
            mode="lines+markers",
            line=dict(color="#10B981", width=2),
        ),
        secondary_y=True,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "debt"),
            name="Debt",
            mode="lines+markers",
            line=dict(color="#EF4444", width=2),
            fill="tozeroy",
            fillcolor="rgba(239, 68, 68, 0.1)",
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Market Cap with TTM Revenue, Cash, and Debt",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Market Cap / TTM Revenue (€)", row=1, col=1, secondary_y=False)
    _apply_currency_axis(fig, title="Cash / Debt (€)", row=1, col=1, secondary_y=True)
    return fig


def plot_debt_interest_cash(df: pd.DataFrame) -> go.Figure:
    """Plot debt with effective interest rate and cash position."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Primary Y-axis - Debt and Cash
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "debt"),
            name="Debt",
            mode="lines+markers",
            line=dict(color="#EF4444", width=3),
            fill="tozeroy",
            fillcolor="rgba(239, 68, 68, 0.2)",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "cash"),
            name="Cash",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
        ),
        secondary_y=False,
    )
    
    # Secondary Y-axis - Effective Interest Rate
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "interest_rate_annual_eff"),
            name="Effective Interest Rate",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=2, dash="dash"),
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Debt, Cash Position & Effective Interest Rate",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Debt / Cash (€)", row=1, col=1, secondary_y=False)
    _apply_percent_axis(fig, title="Effective Interest Rate", row=1, col=1, secondary_y=True)
    return fig


def plot_monthly_revenue(df: pd.DataFrame) -> go.Figure:
    """Plot monthly revenue over time."""
    fig = go.Figure(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "revenue_total"),
            mode="lines+markers",
            name="Revenue",
            line=dict(color="#10B981", width=3),
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Monthly Revenue",
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Revenue (€)")
    return fig


def plot_product_value(df: pd.DataFrame) -> go.Figure:
    """Plot product value and development budget over time."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Primary Y-axis - Product Value
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "product_value"),
            name="Product Value",
            mode="lines+markers",
            line=dict(color="#EF4444", width=3),
        ),
        secondary_y=False,
    )
    
    # Secondary Y-axis - Development Budget
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "dev_budget"),
            name="Dev Budget",
            mode="lines+markers",
            line=dict(color="#F97316", width=2, dash="dot"),
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Product Value & Development Budget Over Time",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Product Value", secondary_y=False)
    _apply_currency_axis(fig, title="Dev Budget (€)", row=1, col=1, secondary_y=True)
    return fig




def plot_net_cashflow(df: pd.DataFrame) -> go.Figure:
    """Plot net cashflow over time."""
    fig = go.Figure(
        go.Bar(
            x=df["month"],
            y=_series_or_zeros(df, "net_cashflow"),
            name="Net Cashflow",
            marker_color="#F59E0B",
        )
    )
    fig.add_hline(y=0, line_width=1, line_dash="dash", line_color="#94A3B8")
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Monthly Net Cashflow",
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Net Cashflow (€)")
    return fig


def plot_ttm_revenue(df: pd.DataFrame) -> go.Figure:
    """Plot TTM revenue over time."""
    fig = go.Figure(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "revenue_ttm"),
            mode="lines+markers",
            name="TTM Revenue",
            line=dict(color="#14B8A6", width=3),
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="TTM Revenue",
        hovermode="x unified",
        showlegend=False,
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="TTM Revenue (€)")
    return fig


# ===== IMPROVED AND NEW PLOTTING FUNCTIONS =====


def plot_user_growth_stacked(df: pd.DataFrame) -> go.Figure:
    """Plot user growth as stacked area chart for composition insights."""
    fig = go.Figure()
    colors = ["#2563EB", "#10B981", "#EF4444"]
    for series, label, color in zip(
        ["free_active", "pro_active", "ent_active"],
        ["Free Users", "Pro Users", "Enterprise Users"],
        colors,
        strict=True,
    ):
        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=_series_or_zeros(df, series),
                name=label,
                stackgroup="users",
                mode="lines",
                line=dict(width=0.5, color=color),
            )
        )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="User Growth - Stacked View",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_count_axis(fig, title="Active Users")
    return fig


def plot_revenue_breakdown(df: pd.DataFrame) -> go.Figure:
    """Plot revenue breakdown by tier using stacked bars."""
    revenue_total = _series_or_zeros(df, "revenue_total")
    if "revenue_pro" in df.columns and "revenue_ent" in df.columns:
        revenue_pro = _series_or_zeros(df, "revenue_pro")
        revenue_ent = _series_or_zeros(df, "revenue_ent")
    else:
        revenue_pro = revenue_total * 0.7
        revenue_ent = revenue_total * 0.3

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df["month"],
            y=revenue_pro,
            name="Pro Revenue",
            marker_color="#10B981",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df["month"],
            y=revenue_ent,
            name="Enterprise Revenue",
            marker_color="#EF4444",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Revenue Breakdown by Tier",
        barmode="stack",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Revenue (€)")
    return fig


def plot_cash_burn_rate(df: pd.DataFrame) -> go.Figure:
    """Plot cash burn rate with runway analysis."""
    burn_rate = -_series_or_zeros(df, "net_cashflow").clip(upper=0)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "cash"),
            name="Cash Position",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=df["month"],
            y=burn_rate,
            name="Burn Rate",
            marker_color="#EF4444",
            opacity=0.6,
        ),
        secondary_y=True,
    )

    min_cash_idx = df["cash"].idxmin() if df["cash"].min() < 0 else None
    if min_cash_idx is not None:
        fig.add_vline(
            x=df.loc[min_cash_idx, "month"],
            line_dash="dash",
            line_color="#EF4444",
            annotation_text="Cash depleted",
            annotation_position="top",
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Cash Position & Burn Rate Analysis",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Cash (€)", row=1, col=1, secondary_y=False)
    _apply_currency_axis(fig, title="Burn Rate (€ / month)", row=1, col=1, secondary_y=True)
    return fig


def plot_conversion_funnel(df: pd.DataFrame) -> go.Figure:
    """Plot conversion funnel for the latest month."""
    latest = df.iloc[-1]
    stages = ["Website Users", "Leads", "Free Users", "Pro Users", "Enterprise Users"]
    values = [
        latest.get("website_users", latest.get("leads_total", 0) * 10),
        latest.get("leads_total", 0),
        latest.get("free_active", 0),
        latest.get("pro_active", 0),
        latest.get("ent_active", 0),
    ]

    fig = go.Figure(
        go.Funnel(
            y=stages,
            x=values,
            textinfo="value+percent previous",
            marker=dict(color=["#2563EB", "#8B5CF6", "#10B981", "#F59E0B", "#EF4444"]),
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title=f"Conversion Funnel - Month {latest.get('month', '')}",
        hovermode="y",
    )
    _apply_count_axis(fig, title="Count")
    return fig


def plot_ltv_cac_analysis(df: pd.DataFrame) -> go.Figure:
    """Plot LTV vs CAC analysis over time."""
    new_pro = (
        df["new_pro"]
        if "new_pro" in df.columns
        else _series_or_zeros(df, "pro_active").diff().fillna(0)
    )
    new_ent = (
        df["new_ent"]
        if "new_ent" in df.columns
        else _series_or_zeros(df, "ent_active").diff().fillna(0)
    )
    total_new_customers = new_pro + new_ent
    if "sales_spend" in df.columns:
        cac = _safe_divide(_series_or_zeros(df, "sales_spend"), total_new_customers)
    else:
        cac = _series_or_zeros(df, "revenue_total") * 0.2

    active_paid = _series_or_zeros(df, "pro_active") + _series_or_zeros(df, "ent_active")
    avg_monthly_revenue = _safe_divide(_series_or_zeros(df, "revenue_total"), active_paid)

    if "churn_pro" in df.columns:
        ltv_pro = _safe_divide(avg_monthly_revenue, _series_or_zeros(df, "churn_pro"))
    else:
        ltv_pro = avg_monthly_revenue * 24
    ltv_ent = ltv_pro * 5
    ltv = _safe_divide(
        ltv_pro * _series_or_zeros(df, "pro_active")
        + ltv_ent * _series_or_zeros(df, "ent_active"),
        active_paid,
    )

    ltv_cac_ratio = _safe_divide(ltv, cac)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=ltv,
            name="LTV",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=cac,
            name="CAC",
            mode="lines+markers",
            line=dict(color="#EF4444", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=ltv_cac_ratio,
            name="LTV:CAC Ratio",
            mode="lines+markers",
            line=dict(color="#8B5CF6", width=2, dash="dot"),
        ),
        secondary_y=True,
    )
    fig.add_shape(
        type="line",
        xref="x",
        yref="y2",
        x0=df["month"].min(),
        x1=df["month"].max(),
        y0=3,
        y1=3,
        line=dict(color="#94A3B8", dash="dash"),
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="LTV vs CAC Analysis",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_currency_axis(fig, title="Value (€)", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="LTV:CAC Ratio", row=1, col=1, secondary_y=True)
    return fig


def plot_unit_economics(df: pd.DataFrame) -> go.Figure:
    """Plot detailed unit economics including ARPU, costs, and margins."""
    total_users = (
        _series_or_zeros(df, "free_active")
        + _series_or_zeros(df, "pro_active")
        + _series_or_zeros(df, "ent_active")
    )
    arpu = _safe_divide(_series_or_zeros(df, "revenue_total"), total_users)
    if "costs_ex_tax" in df.columns:
        cost_per_user = _safe_divide(_series_or_zeros(df, "costs_ex_tax"), total_users)
        margin_per_user = arpu - cost_per_user
    else:
        cost_per_user = arpu * 0.7
        margin_per_user = arpu * 0.3
    margin_pct = _safe_divide(margin_per_user, arpu)

    # Scale values to be more visible (multiply by 1000)
    arpu_scaled = arpu * 1000
    cost_per_user_scaled = cost_per_user * 1000
    margin_per_user_scaled = margin_per_user * 1000

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=arpu_scaled,
            name="ARPU (×1000)",
            mode="lines+markers",
            line=dict(color="#10B981", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=cost_per_user_scaled,
            name="Cost per User (×1000)",
            mode="lines+markers",
            line=dict(color="#EF4444", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=margin_per_user_scaled,
            name="Margin per User (×1000)",
            mode="lines+markers",
            line=dict(color="#2563EB", width=3),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=margin_pct,
            name="Margin %",
            mode="lines+markers",
            line=dict(color="#8B5CF6", width=2, dash="dot"),
        ),
        secondary_y=True,
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Unit Economics Analysis (Values scaled by 1000 for visibility)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Per User (€×1000)", row=1, col=1, secondary_y=False)
    _apply_percent_axis(fig, title="Margin %", row=1, col=1, secondary_y=True)
    return fig


def plot_growth_metrics_heatmap(df: pd.DataFrame) -> go.Figure:
    """Plot growth metrics as a heatmap for quick insights."""
    metrics = {
        "Revenue Growth": _series_or_zeros(df, "revenue_total").pct_change().fillna(0),
        "User Growth": (
            _series_or_zeros(df, "pro_active") + _series_or_zeros(df, "ent_active")
        )
        .pct_change()
        .fillna(0),
        "Cash Growth": _series_or_zeros(df, "cash").pct_change().fillna(0),
        "Market Cap Growth": _series_or_zeros(df, "market_cap").pct_change().fillna(0),
        "Net Cashflow (K€)": _series_or_zeros(df, "net_cashflow") / 1000,
        "Profit Margin": _safe_divide(
            _series_or_zeros(df, "net_cashflow"),
            _series_or_zeros(df, "revenue_total"),
        ),
    }
    metrics_df = pd.DataFrame(metrics)
    normalized = (metrics_df - metrics_df.mean()) / metrics_df.std().replace(0, np.nan)
    normalized = normalized.fillna(0)

    text_rows: list[list[str]] = []
    for metric in metrics_df.columns:
        values = metrics_df[metric]
        if "Cashflow" in metric:
            text_rows.append([f"€{value:,.1f}K" for value in values])
        else:
            text_rows.append([f"{value:.1%}" for value in values])

    fig = go.Figure(
        go.Heatmap(
            z=normalized.T,
            x=df["month"],
            y=metrics_df.columns.tolist(),
            text=text_rows,
            texttemplate="%{text}",
            colorscale="RdYlGn",
            zmid=0,
            hovertemplate="%{y}<br>Month %{x}<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Growth Metrics Heatmap",
        xaxis_title="Month",
        yaxis_title="Metric",
    )
    return fig


def plot_customer_acquisition_channels(df: pd.DataFrame) -> go.Figure:
    """Plot customer acquisition channels over time."""
    fig = go.Figure()
    if "ads_clicks" in df.columns:
        conv_web_to_lead = (
            df["conv_web_to_lead"] if "conv_web_to_lead" in df.columns else 0.03
        )
        ads_leads = _series_or_zeros(df, "ads_clicks") * conv_web_to_lead
        direct_leads = _series_or_zeros(df, "new_direct_leads")
        organic_leads = (
            _series_or_zeros(df, "leads_total") - ads_leads - direct_leads
        ).clip(lower=0)
        for series, label, color in zip(
            [organic_leads, ads_leads, direct_leads],
            ["Organic", "Paid Ads", "Direct Outreach"],
            ["#10B981", "#2563EB", "#EF4444"],
            strict=True,
        ):
            fig.add_trace(
                go.Scatter(
                    x=df["month"],
                    y=series,
                    name=label,
                    stackgroup="channels",
                    mode="lines",
                    line=dict(width=0.5, color=color),
                )
            )
    else:
        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=_series_or_zeros(df, "leads_total"),
                name="Total Leads",
                mode="lines+markers",
                line=dict(color="#8B5CF6", width=3),
            )
        )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Customer Acquisition Channels",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title_text="Month")
    _apply_count_axis(fig, title="Leads")
    return fig


def plot_financial_health_score(df: pd.DataFrame) -> go.Figure:
    """Plot a simplified financial health score."""
    cash_months = _safe_divide(
        _series_or_zeros(df, "cash"),
        -_series_or_zeros(df, "net_cashflow").clip(upper=0).replace(0, 1),
    )
    cash_score = np.clip(cash_months / 24 * 100, 0, 100)
    revenue_growth = _series_or_zeros(df, "revenue_total").pct_change().fillna(0)
    growth_score = np.clip(revenue_growth * 100 + 50, 0, 100)
    profit_margin = _safe_divide(
        _series_or_zeros(df, "net_cashflow"),
        _series_or_zeros(df, "revenue_total"),
    )
    profitability_score = np.clip(profit_margin * 100 + 50, 0, 100)
    health_score = cash_score * 0.4 + growth_score * 0.3 + profitability_score * 0.3

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=health_score,
            name="Overall Health Score",
            mode="lines+markers",
            line=dict(color="#8B5CF6", width=3),
        )
    )

    # Add simplified zones
    fig.add_hrect(y0=0, y1=30, fillcolor="#FEE2E2", opacity=0.4, line_width=0)
    fig.add_hrect(y0=30, y1=70, fillcolor="#FEF3C7", opacity=0.4, line_width=0)
    fig.add_hrect(y0=70, y1=100, fillcolor="#DCFCE7", opacity=0.4, line_width=0)

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Financial Health Score",
        hovermode="x unified",
        showlegend=False,
        annotations=[
            dict(x=0.02, y=15, text="Poor", showarrow=False, font=dict(size=12)),
            dict(x=0.02, y=50, text="Fair", showarrow=False, font=dict(size=12)),
            dict(x=0.02, y=85, text="Good", showarrow=False, font=dict(size=12)),
        ]
    )
    fig.update_xaxes(title_text="Month")
    fig.update_yaxes(title_text="Score (0-100)", range=[0, 100])
    return fig


def plot_enhanced_dashboard(df: pd.DataFrame, save_path: str | None = None) -> go.Figure:
    """Create an enhanced dashboard with improved visualizations."""
    fig = make_subplots(
        rows=4,
        cols=2,
        subplot_titles=(
            "User Growth - Stacked View",
            "Revenue Breakdown by Tier",
            "Cash Position & Burn Rate",
            "LTV vs CAC Analysis",
            "Unit Economics",
            "Conversion Funnel",
            "Acquisition Channels",
            "Financial Health Score",
        ),
        specs=[
            [{}, {}],
            [{"secondary_y": True}, {"secondary_y": True}],
            [{"secondary_y": True}, {}],
            [{}, {}],
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08,
    )

    _add_traces_from_fig(fig, plot_user_growth_stacked(df), row=1, col=1)
    _add_traces_from_fig(fig, plot_revenue_breakdown(df), row=1, col=2)
    _add_traces_from_fig(fig, plot_cash_burn_rate(df), row=2, col=1)
    _add_traces_from_fig(fig, plot_ltv_cac_analysis(df), row=2, col=2)
    _add_traces_from_fig(fig, plot_unit_economics(df), row=3, col=1)
    _add_traces_from_fig(fig, plot_conversion_funnel(df), row=3, col=2)
    _add_traces_from_fig(fig, plot_customer_acquisition_channels(df), row=4, col=1)
    _add_traces_from_fig(fig, plot_financial_health_score(df), row=4, col=2)

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="OTAI Financial Simulation - Enhanced Dashboard",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=1200,
    )

    for row, col in [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (4, 1), (4, 2)]:
        fig.update_xaxes(title_text="Month", row=row, col=col)
    fig.update_xaxes(title_text="Count", row=3, col=2)
    fig.update_yaxes(title_text="Stage", row=3, col=2)

    _apply_count_axis(fig, title="Active Users", row=1, col=1)
    _apply_currency_axis(fig, title="Revenue (€)", row=1, col=2)
    _apply_currency_axis(fig, title="Cash (€)", row=2, col=1, secondary_y=False)
    _apply_currency_axis(fig, title="Burn Rate (€ / month)", row=2, col=1, secondary_y=True)
    _apply_currency_axis(fig, title="Value (€)", row=2, col=2, secondary_y=False)
    fig.update_yaxes(title_text="LTV:CAC Ratio", row=2, col=2, secondary_y=True)
    _apply_currency_axis(fig, title="Per User (€)", row=3, col=1, secondary_y=False)
    _apply_percent_axis(fig, title="Margin %", row=3, col=1, secondary_y=True)
    _apply_count_axis(fig, title="Leads", row=4, col=1)
    fig.update_yaxes(title_text="Score (0-100)", row=4, col=2, range=[0, 100])

    if save_path:
        fig.write_image(save_path, scale=2)

    return fig


def plot_decision_attributes(df: pd.DataFrame) -> go.Figure:
    """Plot decision attributes (budgets and price overrides) over time."""
    
    # Budget categories with their colors and labels
    budget_cols = [
        ("ads_budget", "Ads Budget", "#2563EB"),
        ("seo_budget", "SEO Budget", "#10B981"),
        ("dev_budget", "Dev Budget", "#F97316"),
        ("outreach_budget", "Outreach Budget", "#EF4444"),
        ("partner_budget", "Partner Budget", "#8B5CF6"),
    ]
    
    # Create subplot for budgets and prices
    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=(
            "Monthly Budget Allocations",
            "Price Overrides (if set)",
        ),
        vertical_spacing=0.12,
    )
    
    # Plot budgets as stacked area chart
    for col, label, color in budget_cols:
        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=_series_or_zeros(df, col),
                name=label,
                stackgroup="budgets",
                mode="lines",
                line=dict(width=0.5, color=color),
                hovertemplate="%{fullData.name}<br>Month: %{x}<br>Amount: €%{y:,.0f}<extra></extra>",
            ),
            row=1,
            col=1,
        )
    
    # Plot total budget as line overlay
    total_budget = sum(_series_or_zeros(df, col) for col, _, _ in budget_cols)
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=total_budget,
            name="Total Budget",
            mode="lines+markers",
            line=dict(color="#111827", width=2, dash="dash"),
            hovertemplate="Total Budget<br>Month: %{x}<br>Amount: €%{y:,.0f}<extra></extra>",
        ),
        row=1,
        col=1,
    )
    
    # Update layout
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Decision Attributes Over Time",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=650,
    )
    
    # Update axes
    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=2, col=1)
    
    _apply_currency_axis(fig, title="Budget (€)", row=1, col=1)
    _apply_currency_axis(fig, title="Price (€)", row=2, col=1)
    
    # Add budget allocation percentages as annotations on the last month
    if len(df) > 0:
        last_month_idx = len(df) - 1
        total_last = total_budget.iloc[last_month_idx]
        if total_last > 0:
            y_pos = 0
            for col, label, color in budget_cols:
                amount = _series_or_zeros(df, col).iloc[last_month_idx]
                if amount > 0:
                    pct = (amount / total_last) * 100
                    fig.add_annotation(
                        text=f"{label}: {pct:.1f}%",
                        x=df["month"].iloc[last_month_idx],
                        y=y_pos + amount / 2,
                        showarrow=False,
                        font=dict(size=10, color="white"),
                        row=1,
                        col=1,
                    )
                    y_pos += amount
    
    return fig


def plot_growth_insights(df: pd.DataFrame, save_path: str | None = None) -> go.Figure:
    """Create a growth-focused insights dashboard."""
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Growth Metrics Heatmap",
            "Market Cap Growth Phases",
            "Revenue Growth Dynamics",
            "Product Value vs Lead Generation",
        ),
        specs=[[{}, {}], [{}, {"secondary_y": True}]],
        vertical_spacing=0.12,
    )

    _add_traces_from_fig(fig, plot_growth_metrics_heatmap(df), row=1, col=1)

    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "market_cap"),
            name="Market Cap",
            mode="lines+markers",
            line=dict(color="#111827", width=2),
            fill="tozeroy",
            fillcolor="rgba(234, 179, 8, 0.25)",
        ),
        row=1,
        col=2,
    )
    for i in range(0, len(df), 3):
        start = df["month"].iloc[i]
        end = df["month"].iloc[min(i + 3, len(df) - 1)]
        fig.add_vrect(
            x0=start,
            x1=end,
            row=1,
            col=2,
            fillcolor="#22C55E" if i % 6 == 0 else "#3B82F6",
            opacity=0.08,
            line_width=0,
        )

    revenue_growth = _series_or_zeros(df, "revenue_total").pct_change().fillna(0)
    acceleration = revenue_growth.diff().fillna(0)
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=revenue_growth,
            name="Revenue Growth Rate",
            mode="lines+markers",
            line=dict(color="#10B981", width=2),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=acceleration,
            name="Growth Acceleration",
            mode="lines+markers",
            line=dict(color="#F59E0B", width=2, dash="dot"),
        ),
        row=2,
        col=1,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8", row=2, col=1)

    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "product_value"),
            name="Product Value",
            mode="lines+markers",
            line=dict(color="#EF4444", width=2),
        ),
        row=2,
        col=2,
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=df["month"],
            y=_series_or_zeros(df, "leads_total"),
            name="Leads",
            mode="lines+markers",
            line=dict(color="#2563EB", width=2),
        ),
        row=2,
        col=2,
        secondary_y=True,
    )

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title="Growth Insights Dashboard",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        height=850,
    )
    fig.update_xaxes(title_text="Month", row=1, col=1)
    fig.update_xaxes(title_text="Month", row=1, col=2)
    fig.update_xaxes(title_text="Month", row=2, col=1)
    fig.update_xaxes(title_text="Month", row=2, col=2)
    _apply_currency_axis(fig, title="Market Cap (€)", row=1, col=2)
    _apply_percent_axis(fig, title="Rate", row=2, col=1)
    fig.update_yaxes(title_text="Product Value", row=2, col=2, secondary_y=False)
    _apply_count_axis(fig, title="Leads", row=2, col=2, secondary_y=True)

    if save_path:
        fig.write_image(save_path, scale=2)

    return fig


