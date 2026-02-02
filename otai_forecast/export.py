from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def _maybe_asdict(x: Any) -> Any:
    return asdict(x) if is_dataclass(x) else x


def _assumptions_df(assumptions: Any | None) -> pd.DataFrame | None:
    if assumptions is None:
        return None
    a = _maybe_asdict(assumptions)
    if not isinstance(a, dict):
        return None
    return pd.DataFrame(
        [{"Parameter": k, "Value": v} for k, v in a.items()], columns=["Parameter", "Value"]
    )


def _decisions_df(monthly_decisions: Any | None) -> pd.DataFrame | None:
    if monthly_decisions is None:
        return None
    if not isinstance(monthly_decisions, list):
        return None
    rows: list[dict] = []
    for i, d in enumerate(monthly_decisions):
        dd = _maybe_asdict(d)
        if isinstance(dd, dict):
            rows.append({"month": i, **dd})
    return pd.DataFrame(rows) if rows else None


def export_simulation_output(
    rows: list[dict] | pd.DataFrame,
    out_path: str = "OTAI_Simulation_Output.xlsx",
    assumptions: Any | None = None,
    monthly_decisions: Any | None = None,
) -> str:
    df = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    df_a = _assumptions_df(assumptions)
    df_d = _decisions_df(monthly_decisions)

    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="simulation")
        if df_a is not None:
            df_a.to_excel(w, index=False, sheet_name="assumptions")
        if df_d is not None:
            df_d.to_excel(w, index=False, sheet_name="monthly_decisions")

    wb = load_workbook(out_path)
    ws = wb["simulation"]
    ws.freeze_panes = "A2"

    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            v = "" if cell.value is None else str(cell.value)
            if len(v) > max_len:
                max_len = len(v)
        ws.column_dimensions[col_letter].width = min(40, max(10, max_len + 2))

    wb.save(out_path)
    return out_path


def export_detailed(
    detailed_log: list[dict] | pd.DataFrame,
    out_path: str = "OTAI_Simulation_Detailed.xlsx",
    assumptions: Any | None = None,
    monthly_decisions: Any | None = None,
) -> str:
    df = (
        detailed_log
        if isinstance(detailed_log, pd.DataFrame)
        else pd.DataFrame(detailed_log)
    )
    df_a = _assumptions_df(assumptions)
    df_d = _decisions_df(monthly_decisions)

    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="monthly")
        if df_a is not None:
            df_a.to_excel(w, index=False, sheet_name="assumptions")
        if df_d is not None:
            df_d.to_excel(w, index=False, sheet_name="monthly_decisions")

    wb = load_workbook(out_path)
    ws = wb.active

    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            v = "" if cell.value is None else str(cell.value)
            if len(v) > max_len:
                max_len = len(v)
        ws.column_dimensions[col_letter].width = min(40, max(10, max_len + 2))

    wb.save(out_path)
    return out_path


def export_nice(
    detailed_log: list[dict] | pd.DataFrame,
    out_path: str = "OTAI_Simulation_Nice.xlsx",
    assumptions: Any | None = None,
    monthly_decisions: Any | None = None,
) -> str:
    df = (
        detailed_log
        if isinstance(detailed_log, pd.DataFrame)
        else pd.DataFrame(detailed_log)
    )

    overview_cols = [
        "month",
        "cash",
        "debt",
        "revenue_total",
        "costs_ex_tax",
        "tax",
        "net_cashflow",
        "website_users",
        "domain_rating",
        "leads_total",
        "new_free",
        "new_pro",
        "new_ent",
        "free_active",
        "pro_active",
        "ent_active",
        "product_value",
    ]

    finance_cols = [
        "month",
        "revenue_pro",
        "revenue_ent",
        "revenue_total",
        "interest_payment",
        "costs_ex_tax",
        "profit_bt",
        "tax",
        "net_cashflow",
        "cash",
        "debt",
    ]

    acq_cols = [
        "month",
        "ads_spend",
        "seo_spend",
        "social_spend",
        "dev_spend",
        "operating_spend",
        "scraping_spend",
        "ads_clicks",
        "domain_rating",
        "seo_stock_users",
        "website_users",
        "website_leads",
        "outreach_leads",
        "scraping_leads",
        "direct_leads",
        "leads_total",
    ]

    funnel_cols = [
        "month",
        "new_free",
        "new_pro",
        "new_ent",
        "churned_free",
        "churned_pro",
        "churned_ent",
        "free_active",
        "pro_active",
        "ent_active",
    ]

    product_cols = [
        "month",
        "product_value",
        "pv_norm",
        "pro_price",
        "ent_price",
        "conv_web_to_lead_eff",
        "conv_lead_to_free_eff",
        "conv_free_to_pro_eff",
        "conv_pro_to_ent_eff",
        "churn_pro_eff",
    ]

    def pick(cols: list[str]) -> pd.DataFrame:
        return df[[c for c in cols if c in df.columns]].copy()

    df_overview = pick(overview_cols)
    df_finance = pick(finance_cols)
    df_acq = pick(acq_cols)
    df_funnel = pick(funnel_cols)
    df_product = pick(product_cols)

    df_a = _assumptions_df(assumptions)
    df_d = _decisions_df(monthly_decisions)

    def first_neg_month(series_month: pd.Series, series_cash: pd.Series):
        m = series_month[series_cash < 0]
        return int(m.iloc[0]) if len(m) else None

    kpis = [
        (
            "Months",
            int(df["month"].max() + 1) if "month" in df.columns and len(df) else None,
        ),
        (
            "Starting cash (€)",
            float(df["cash"].iloc[0]) if "cash" in df.columns and len(df) else None,
        ),
        (
            "Ending cash (€)",
            float(df["cash"].iloc[-1]) if "cash" in df.columns and len(df) else None,
        ),
        (
            "Ending debt (€)",
            float(df["debt"].iloc[-1]) if "debt" in df.columns and len(df) else None,
        ),
        (
            "Min cash (€)",
            float(df["cash"].min()) if "cash" in df.columns and len(df) else None,
        ),
        (
            "Month of min cash",
            int(df.loc[df["cash"].idxmin(), "month"])
            if "cash" in df.columns and len(df)
            else None,
        ),
        (
            "First month cash < 0",
            first_neg_month(df["month"], df["cash"])
            if "cash" in df.columns and len(df)
            else None,
        ),
        (
            "Total revenue (€)",
            float(df["revenue_total"].sum())
            if "revenue_total" in df.columns and len(df)
            else None,
        ),
        (
            "Avg revenue last 3 months (€)",
            float(df["revenue_total"].tail(3).mean())
            if "revenue_total" in df.columns and len(df) >= 3
            else None,
        ),
        (
            "Total costs ex tax (€)",
            float(df["costs_ex_tax"].sum())
            if "costs_ex_tax" in df.columns and len(df)
            else None,
        ),
        (
            "Total tax (€)",
            float(df["tax"].sum()) if "tax" in df.columns and len(df) else None,
        ),
        (
            "Total profit after tax (€)",
            float((df["profit_bt"] - df["tax"]).sum())
            if "profit_bt" in df.columns and "tax" in df.columns and len(df)
            else None,
        ),
        (
            "End Free active",
            float(df["free_active"].iloc[-1])
            if "free_active" in df.columns and len(df)
            else None,
        ),
        (
            "End Pro active",
            float(df["pro_active"].iloc[-1])
            if "pro_active" in df.columns and len(df)
            else None,
        ),
        (
            "End Enterprise active",
            float(df["ent_active"].iloc[-1])
            if "ent_active" in df.columns and len(df)
            else None,
        ),
        (
            "Total Ads spend (€)",
            float(df["ads_spend"].sum())
            if "ads_spend" in df.columns and len(df)
            else None,
        ),
        (
            "Total SEO spend (€)",
            float(df["seo_spend"].sum())
            if "seo_spend" in df.columns and len(df)
            else None,
        ),
        (
            "Total Social spend (€)",
            float(df["social_spend"].sum())
            if "social_spend" in df.columns and len(df)
            else None,
        ),
        (
            "Total Scraping spend (€)",
            float(df["scraping_spend"].sum())
            if "scraping_spend" in df.columns and len(df)
            else None,
        ),
    ]
    df_kpis = pd.DataFrame(kpis, columns=["Metric", "Value"])

    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        df_kpis.to_excel(w, index=False, sheet_name="Dashboard_KPIs")
        df_overview.to_excel(w, index=False, sheet_name="Dashboard_Overview")
        df_finance.to_excel(w, index=False, sheet_name="Finance")
        df_acq.to_excel(w, index=False, sheet_name="Acquisition")
        df_funnel.to_excel(w, index=False, sheet_name="Funnel")
        df_product.to_excel(w, index=False, sheet_name="Product")
        if df_a is not None:
            df_a.to_excel(w, index=False, sheet_name="Assumptions")
        if df_d is not None:
            df_d.to_excel(w, index=False, sheet_name="Monthly_Decisions")
        df.to_excel(w, index=False, sheet_name="Monthly_Full")

    wb = load_workbook(out_path)

    header_fill = PatternFill("solid", fgColor="1F2937")
    header_font = Font(color="FFFFFF", bold=True)
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    def autosize(ws):
        for i, col in enumerate(
            ws.iter_cols(
                min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column
            ),
            start=1,
        ):
            max_len = 0
            for cell in col:
                v = "" if cell.value is None else str(cell.value)
                if len(v) > max_len:
                    max_len = len(v)
            ws.column_dimensions[get_column_letter(i)].width = min(
                42, max(10, max_len + 2)
            )

    def style_sheet(ws):
        ws.freeze_panes = "A2"
        ws.row_dimensions[1].height = 24
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_align
        autosize(ws)

    for name in wb.sheetnames:
        style_sheet(wb[name])

    for name in [
        "Dashboard_Overview",
        "Finance",
        "Acquisition",
        "Funnel",
        "Product",
        "Monthly_Decisions",
        "Monthly_Full",
    ]:
        ws = wb[name]
        for col_name in [
            "cash",
            "debt",
            "revenue_total",
            "costs_ex_tax",
            "net_cashflow",
            "tax",
            "profit_bt",
            "revenue_pro",
            "revenue_ent",
            "ads_spend",
            "seo_spend",
            "social_spend",
            "dev_spend",
            "operating_spend",
            "scraping_spend",
            "sales_spend",
            "support_spend",
            "interest_payment",
        ]:
            idx = None
            for j in range(1, ws.max_column + 1):
                if ws.cell(row=1, column=j).value == col_name:
                    idx = j
                    break
            if idx:
                for r in range(2, ws.max_row + 1):
                    ws.cell(row=r, column=idx).number_format = '#,##0.00" €"'

    wb.save(out_path)
    return out_path
