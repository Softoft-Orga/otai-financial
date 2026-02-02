"""Centralized plotting functions for OTAI financial simulation."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter


def plot_results(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Create plots for the simulation results.
    
    Args:
        df: DataFrame with simulation results
        save_path: If provided, save the plot to this path
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("OTAI Financial Simulation Results", fontsize=16)

    # Plot 1: User Growth
    axes[0, 0].plot(df["month"], df["free_active"], label="Free Users", marker="o")
    axes[0, 0].plot(df["month"], df["pro_active"], label="Pro Users", marker="o")
    axes[0, 0].plot(df["month"], df["ent_active"], label="Enterprise Users", marker="o")
    axes[0, 0].set_title("User Growth Over Time")
    axes[0, 0].set_xlabel("Month")
    axes[0, 0].set_ylabel("Number of Users")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Plot 2: Revenue and Cashflow
    ax2_twin = axes[0, 1].twinx()
    axes[0, 1].plot(
        df["month"], df["revenue_total"], color="green", label="Revenue", marker="o"
    )
    ax2_twin.plot(
        df["month"], df["net_cashflow"], color="blue", label="Net Cashflow", marker="s"
    )
    axes[0, 1].set_title("Revenue and Net Cashflow")
    axes[0, 1].set_xlabel("Month")
    axes[0, 1].set_ylabel("Revenue (€)", color="green")
    ax2_twin.set_ylabel("Net Cashflow (€)", color="blue")
    axes[0, 1].grid(True, alpha=0.3)

    # Combine legends
    lines1, labels1 = axes[0, 1].get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    axes[0, 1].legend(lines1 + lines2, labels1 + labels2)

    # Plot 3: Cash Position
    axes[1, 0].plot(df["month"], df["cash"], marker="o", color="purple")
    axes[1, 0].set_title("Cash Position")
    axes[1, 0].set_xlabel("Month")
    axes[1, 0].set_ylabel("Cash (€)")
    axes[1, 0].grid(True, alpha=0.3)

    # Plot 4: Market Cap
    axes[1, 1].plot(df["month"], df["market_cap"], label="Market Cap", marker="o")
    axes[1, 1].set_title("Market Cap (TTM Revenue × Multiple)")
    axes[1, 1].set_xlabel("Month")
    axes[1, 1].set_ylabel("€")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=160)
    
    return fig


def plot_user_growth(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot user growth over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["free_active"], label="Free Users", marker="o")
    ax.plot(df["month"], df["pro_active"], label="Pro Users", marker="o")
    ax.plot(df["month"], df["ent_active"], label="Enterprise Users", marker="o")
    ax.set_title("User Growth Over Time")
    ax.set_xlabel("Month")
    ax.set_ylabel("Number of Users")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_revenue_cashflow(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot revenue and cashflow over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.figure
    
    ax2_twin = ax.twinx()
    ax.plot(
        df["month"], df["revenue_total"], color="green", label="Revenue", marker="o"
    )
    ax2_twin.plot(
        df["month"], df["net_cashflow"], color="blue", label="Net Cashflow", marker="s"
    )
    ax.set_title("Revenue and Net Cashflow")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (€)", color="green")
    ax2_twin.set_ylabel("Net Cashflow (€)", color="blue")
    ax.grid(True, alpha=0.3)
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2)
    
    return ax


def plot_cash_position(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot cash position over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["cash"], marker="o", color="purple")
    ax.set_title("Cash Position")
    ax.set_xlabel("Month")
    ax.set_ylabel("Cash (€)")
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_market_cap(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot market cap over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["market_cap"], label="Market Cap", marker="o")
    ax.set_title("Market Cap (TTM Revenue × Multiple)")
    ax.set_xlabel("Month")
    ax.set_ylabel("€")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_monthly_revenue(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot monthly revenue over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["revenue_total"], marker="o", color="green")
    ax.set_title("Monthly Revenue")
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (€)")
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_product_value(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot product value over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["product_value"], marker="o", color="red")
    ax.set_title("Product Value Over Time")
    ax.set_xlabel("Month")
    ax.set_ylabel("Product Value")
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_leads(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot leads over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["leads_total"], label="Total Leads", marker="o")
    ax.set_title("Leads Over Time")
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_net_cashflow(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot net cashflow over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["net_cashflow"], marker="o", color="orange")
    ax.set_title("Monthly Net Cashflow")
    ax.set_xlabel("Month")
    ax.set_ylabel("Net cashflow (€)")
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_ttm_revenue(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot TTM revenue over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(df["month"], df["revenue_ttm"], marker="o", color="teal")
    ax.set_title("TTM Revenue")
    ax.set_xlabel("Month")
    ax.set_ylabel("TTM Revenue (€)")
    ax.grid(True, alpha=0.3)
    
    return ax


# ===== IMPROVED AND NEW PLOTTING FUNCTIONS =====

def plot_user_growth_stacked(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot user growth as stacked area chart for better visualization of composition.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    
    # Create stacked area chart
    ax.stackplot(df["month"], df["free_active"], df["pro_active"], df["ent_active"],
                 labels=["Free Users", "Pro Users", "Enterprise Users"],
                 alpha=0.8, colors=['#3498db', '#2ecc71', '#e74c3c'])
    
    ax.set_title("User Growth - Stacked View", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Number of Users", fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Format y-axis to show values in K/M
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1000000 else f'{x/1000000:.1f}M'))
    
    return ax


def plot_revenue_breakdown(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot revenue breakdown by user tier with stacked bars.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate revenue by tier if not present
    if 'revenue_pro' not in df.columns:
        # Estimate based on typical pricing ratios
        df['revenue_pro'] = df['revenue_total'] * 0.7
        df['revenue_ent'] = df['revenue_total'] * 0.3
    
    # Create stacked bar chart
    width = 0.8
    ax.bar(df["month"], df["revenue_pro"], width, label="Pro Revenue", color='#2ecc71', alpha=0.8)
    ax.bar(df["month"], df["revenue_ent"], width, bottom=df["revenue_pro"], 
           label="Enterprise Revenue", color='#e74c3c', alpha=0.8)
    
    ax.set_title("Revenue Breakdown by Tier", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Revenue (€)", fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'€{x/1000:.0f}K' if x < 1000000 else f'€{x/1000000:.1f}M'))
    
    return ax


def plot_cash_burn_rate(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot cash burn rate with runway analysis.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate burn rate (negative cashflow is burn)
    burn_rate = -df["net_cashflow"].clip(upper=0)
    
    # Create twin axis for cash position
    ax2 = ax.twinx()
    
    # Plot cash position as area
    ax.fill_between(df["month"], df["cash"], alpha=0.3, color='green', label="Cash Position")
    ax.plot(df["month"], df["cash"], color='green', linewidth=2)
    
    # Plot burn rate as bars
    bars = ax2.bar(df["month"], burn_rate, alpha=0.6, color='red', label="Burn Rate")
    
    # Add zero cash line if it occurs
    min_cash_idx = df["cash"].idxmin() if df["cash"].min() < 0 else None
    if min_cash_idx is not None:
        ax.axvline(x=min_cash_idx, color='red', linestyle='--', alpha=0.8, label="Cash Depleted")
    
    ax.set_title("Cash Position & Burn Rate Analysis", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Cash Position (€)", fontsize=12, color='green')
    ax2.set_ylabel("Burn Rate (€/month)", fontsize=12, color='red')
    
    # Format axes
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'€{x/1000:.0f}K' if x < 1000000 else f'€{x/1000000:.1f}M'))
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'€{x/1000:.0f}K' if x < 1000000 else f'€{x/1000000:.1f}M'))
    
    # Combine legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_conversion_funnel(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot conversion funnel as a waterfall chart.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 8))
    
    # Get latest month data
    latest = df.iloc[-1]
    
    # Funnel stages
    stages = ['Website Users', 'Leads', 'Free Users', 'Pro Users', 'Enterprise Users']
    values = [
        latest.get('website_users', latest.get('leads_total', 0) * 10),  # Estimate if not available
        latest['leads_total'],
        latest['free_active'],
        latest['pro_active'],
        latest['ent_active']
    ]
    
    # Calculate conversion rates
    conversion_rates = [values[i] / values[i-1] * 100 if values[i-1] > 0 else 0 for i in range(1, len(values))]
    
    # Create funnel bar chart
    y_pos = range(len(stages))
    bars = ax.barh(y_pos, values, alpha=0.8, 
                   color=['#3498db', '#9b59b6', '#2ecc71', '#f39c12', '#e74c3c'])
    
    # Add conversion rate labels
    for i, (bar, rate) in enumerate(zip(bars[1:], conversion_rates)):
        ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                f'{rate:.1f}%', va='center', fontweight='bold')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(stages)
    ax.set_xlabel("Count", fontsize=12)
    ax.set_title(f"Conversion Funnel - Month {latest['month']}", fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Format x-axis
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x < 1000000 else f'{x/1000000:.1f}M'))
    
    return ax


def plot_ltv_cac_analysis(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot LTV vs CAC analysis over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    
    # Estimate CAC from sales costs
    if 'sales_spend' in df.columns:
        new_pro = df['new_pro'] if 'new_pro' in df.columns else df['pro_active'].diff().fillna(df['pro_active'])
        new_ent = df['new_ent'] if 'new_ent' in df.columns else df['ent_active'].diff().fillna(df['ent_active'])
        total_new_customers = new_pro + new_ent
        cac = df['sales_spend'] / total_new_customers.replace(0, np.nan)
    else:
        # Estimate CAC as percentage of revenue
        cac = df['revenue_total'] * 0.2  # Assume 20% of revenue for sales
    
    # Estimate LTV based on customer lifetime and monthly revenue
    if 'churn_pro' in df.columns and 'churn_ent' in df.columns:
        avg_monthly_revenue = (df['revenue_total'] / (df['pro_active'] + df['ent_active'])).replace(0, np.nan)
        ltv_pro = avg_monthly_revenue / df['churn_pro'] if 'churn_pro' in df.columns else avg_monthly_revenue * 24
        ltv_ent = ltv_pro * 5  # Enterprise typically 5x Pro
        ltv = (ltv_pro * df['pro_active'] + ltv_ent * df['ent_active']) / (df['pro_active'] + df['ent_active'])
    else:
        ltv = cac * 3  # Default 3:1 LTV:CAC ratio
    
    # Plot LTV and CAC
    ax.plot(df["month"], ltv, marker='o', linewidth=2, label="LTV", color='#2ecc71')
    ax.plot(df["month"], cac, marker='s', linewidth=2, label="CAC", color='#e74c3c')
    
    # Add LTV:CAC ratio line
    ltv_cac_ratio = ltv / cac
    ax2 = ax.twinx()
    ax2.plot(df["month"], ltv_cac_ratio, marker='d', linewidth=2, alpha=0.7, 
             label="LTV:CAC Ratio", color='#9b59b6')
    ax2.axhline(y=3, color='gray', linestyle='--', alpha=0.5, label="Target (3:1)")
    
    ax.set_title("LTV vs CAC Analysis", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Value (€)", fontsize=12)
    ax2.set_ylabel("LTV:CAC Ratio", fontsize=12)
    
    # Format axes
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'€{x/1000:.0f}K' if x < 1000000 else f'€{x/1000000:.1f}M'))
    
    # Legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_unit_economics(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot detailed unit economics including ARPU, margins, etc.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate metrics
    total_users = df['free_active'] + df['pro_active'] + df['ent_active']
    arpu = df['revenue_total'] / total_users.replace(0, np.nan)
    
    # Estimate costs
    if 'costs_ex_tax' in df.columns:
        cost_per_user = df['costs_ex_tax'] / total_users.replace(0, np.nan)
        margin_per_user = arpu - cost_per_user
    else:
        # Estimate costs as 70% of revenue
        cost_per_user = arpu * 0.7
        margin_per_user = arpu * 0.3
    
    # Plot metrics
    ax.plot(df["month"], arpu, marker='o', linewidth=2, label="ARPU", color='#2ecc71')
    ax.plot(df["month"], cost_per_user, marker='s', linewidth=2, label="Cost per User", color='#e74c3c')
    ax.plot(df["month"], margin_per_user, marker='^', linewidth=2, label="Margin per User", color='#3498db')
    
    # Add margin percentage on secondary axis
    ax2 = ax.twinx()
    margin_pct = (margin_per_user / arpu * 100).fillna(0)
    ax2.plot(df["month"], margin_pct, marker='d', linewidth=2, alpha=0.7, 
             label="Margin %", color='#9b59b6')
    ax2.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
    
    ax.set_title("Unit Economics Analysis", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Per User (€)", fontsize=12)
    ax2.set_ylabel("Margin (%)", fontsize=12)
    
    # Format axes
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'€{x:.0f}'))
    
    # Legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_growth_metrics_heatmap(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot growth metrics as a heatmap for quick insights.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 8))
    
    # Select key metrics for heatmap
    metrics = {
        'Revenue Growth': df['revenue_total'].pct_change().fillna(0),
        'User Growth': (df['pro_active'] + df['ent_active']).pct_change().fillna(0),
        'Cash Growth': df['cash'].pct_change().fillna(0),
        'Market Cap Growth': df['market_cap'].pct_change().fillna(0),
        'Net Cashflow': df['net_cashflow'] / 1000,  # in K
        'Profit Margin': (df['net_cashflow'] / df['revenue_total']).fillna(0)
    }
    
    # Create heatmap data
    heatmap_data = pd.DataFrame(metrics)
    
    # Create heatmap
    sns.heatmap(heatmap_data.T, annot=True, fmt='.1%', cmap='RdYlGn', 
                center=0, ax=ax, cbar_kws={'label': 'Value'})
    
    ax.set_title("Growth Metrics Heatmap", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Metric", fontsize=12)
    
    return ax


def plot_customer_acquisition_channels(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot customer acquisition channels over time.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    
    # Estimate channel contributions if not directly available
    if 'ads_clicks' in df.columns and 'website_leads' in df.columns:
        # Use available data to estimate channel contributions
        organic_leads = df['leads_total'] - df.get('direct_leads', 0)
        ads_leads = df['ads_clicks'] * df.get('conv_web_to_lead', 0.03)
        
        # Create stacked area chart
        ax.stackplot(df["month"], organic_leads, ads_leads, df.get('direct_leads', 0),
                     labels=['Organic', 'Paid Ads', 'Direct Outreach'],
                     alpha=0.8, colors=['#2ecc71', '#3498db', '#e74c3c'])
    else:
        # Simple growth visualization
        ax.plot(df["month"], df["leads_total"], marker='o', linewidth=2, 
                label="Total Leads", color='#9b59b6')
    
    ax.set_title("Customer Acquisition Channels", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Leads", fontsize=12)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Format y-axis
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x/1000:.0f}K' if x >= 1000 else f'{x:.0f}'))
    
    return ax


def plot_financial_health_score(df: pd.DataFrame, ax: plt.Axes | None = None) -> plt.Axes:
    """Plot a comprehensive financial health score.
    
    Args:
        df: DataFrame with simulation results
        ax: Matplotlib axis to plot on. If None, creates new figure.
        
    Returns:
        The matplotlib axis with the plot
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 6))
    
    # Calculate financial health components (0-100 scale)
    # Cash runway score
    cash_months = df['cash'] / (-df['net_cashflow'].clip(upper=0).replace(0, 1))
    cash_score = np.clip(cash_months / 24 * 100, 0, 100)  # 24 months = perfect score
    
    # Growth score
    revenue_growth = df['revenue_total'].pct_change().fillna(0)
    growth_score = np.clip(revenue_growth * 100 + 50, 0, 100)
    
    # Profitability score
    profit_margin = df['net_cashflow'] / df['revenue_total'].fillna(0)
    profitability_score = np.clip(profit_margin * 100 + 50, 0, 100)
    
    # Combined health score
    health_score = (cash_score * 0.4 + growth_score * 0.3 + profitability_score * 0.3)
    
    # Plot components
    ax.fill_between(df["month"], 0, cash_score, alpha=0.3, label="Cash Runway", color='#2ecc71')
    ax.fill_between(df["month"], cash_score, cash_score + growth_score, 
                    alpha=0.3, label="Growth", color='#3498db')
    ax.fill_between(df["month"], cash_score + growth_score, 
                    cash_score + growth_score + profitability_score,
                    alpha=0.3, label="Profitability", color='#e74c3c')
    
    # Plot overall score
    ax.plot(df["month"], health_score, marker='o', linewidth=3, 
            label="Overall Health Score", color='#9b59b6')
    
    # Add zones
    ax.axhspan(0, 30, alpha=0.1, color='red', label='Danger Zone')
    ax.axhspan(30, 70, alpha=0.1, color='yellow', label='Warning Zone')
    ax.axhspan(70, 100, alpha=0.1, color='green', label='Healthy Zone')
    
    ax.set_title("Financial Health Score", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month", fontsize=12)
    ax.set_ylabel("Score (0-100)", fontsize=12)
    ax.set_ylim(0, 100)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    ax.grid(True, alpha=0.3)
    
    return ax


def plot_enhanced_dashboard(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Create an enhanced dashboard with improved visualizations.
    
    Args:
        df: DataFrame with simulation results
        save_path: If provided, save the plot to this path
    """
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # Define grid layout
    gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
    
    # 1. User Growth Stacked (top left, spanning 2 cols)
    ax1 = fig.add_subplot(gs[0, :2])
    plot_user_growth_stacked(df, ax=ax1)
    
    # 2. Revenue Breakdown (top right, spanning 2 cols)
    ax2 = fig.add_subplot(gs[0, 2:])
    plot_revenue_breakdown(df, ax=ax2)
    
    # 3. Cash Burn Rate (second row, spanning 2 cols)
    ax3 = fig.add_subplot(gs[1, :2])
    plot_cash_burn_rate(df, ax=ax3)
    
    # 4. LTV vs CAC (second row, right)
    ax4 = fig.add_subplot(gs[1, 2:])
    plot_ltv_cac_analysis(df, ax=ax4)
    
    # 5. Unit Economics (third row, left)
    ax5 = fig.add_subplot(gs[2, :2])
    plot_unit_economics(df, ax=ax5)
    
    # 6. Conversion Funnel (third row, right)
    ax6 = fig.add_subplot(gs[2, 2:])
    plot_conversion_funnel(df, ax=ax6)
    
    # 7. Customer Acquisition Channels (fourth row, left)
    ax7 = fig.add_subplot(gs[3, :2])
    plot_customer_acquisition_channels(df, ax=ax7)
    
    # 8. Financial Health Score (fourth row, right)
    ax8 = fig.add_subplot(gs[3, 2:])
    plot_financial_health_score(df, ax=ax8)
    
    # Add main title
    fig.suptitle("OTAI Financial Simulation - Enhanced Dashboard", fontsize=20, fontweight='bold', y=0.95)
    
    # Adjust layout
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=160, bbox_inches='tight')
    
    return fig


def plot_growth_insights(df: pd.DataFrame, save_path: str | None = None) -> None:
    """Create a growth-focused insights dashboard.
    
    Args:
        df: DataFrame with simulation results
        save_path: If provided, save the plot to this path
    """
    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Growth metrics heatmap
    plot_growth_metrics_heatmap(df, ax=axes[0, 0])
    
    # Market cap with growth phases
    ax = axes[0, 1]
    ax.plot(df["month"], df["market_cap"], marker='o', linewidth=2, color='black')
    ax.fill_between(df["month"], df["market_cap"], alpha=0.3, color='gold')
    
    # Add growth phases
    for i in range(0, len(df), 3):
        ax.axvspan(i, i+3, alpha=0.1, color='green' if i % 6 == 0 else 'blue')
    
    ax.set_title("Market Cap Growth Phases", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month")
    ax.set_ylabel("Market Cap (€)")
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'€{x/1000000:.1f}M'))
    
    # Revenue acceleration
    ax = axes[1, 0]
    revenue_growth = df['revenue_total'].pct_change().fillna(0)
    acceleration = revenue_growth.diff().fillna(0)
    
    ax.plot(df["month"], revenue_growth, marker='o', label="Revenue Growth Rate", alpha=0.7)
    ax.plot(df["month"], acceleration, marker='s', label="Growth Acceleration", alpha=0.7)
    ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax.set_title("Revenue Growth Dynamics", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month")
    ax.set_ylabel("Rate")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.1%}'))
    
    # Product value vs user acquisition
    ax = axes[1, 1]
    ax2 = ax.twinx()
    
    ax.plot(df["month"], df["product_value"], marker='o', color='red', label="Product Value")
    ax2.plot(df["month"], df["leads_total"], marker='s', color='blue', label="Leads")
    
    ax.set_title("Product Value vs Lead Generation", fontsize=14, fontweight='bold')
    ax.set_xlabel("Month")
    ax.set_ylabel("Product Value", color='red')
    ax2.set_ylabel("Leads", color='blue')
    ax.grid(True, alpha=0.3)
    
    # Legends
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.suptitle("Growth Insights Dashboard", fontsize=18, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=160, bbox_inches='tight')
    
    return fig
