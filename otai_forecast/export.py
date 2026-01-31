from __future__ import annotations

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def export_simulation_output(
    rows: list[dict] | pd.DataFrame, out_path: str = "OTAI_Simulation_Output.xlsx"
) -> str:
    df = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    df.to_excel(out_path, index=False, sheet_name="simulation")

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
) -> str:
    df = (
        detailed_log
        if isinstance(detailed_log, pd.DataFrame)
        else pd.DataFrame(detailed_log)
    )
    df.to_excel(out_path, index=False)

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
    detailed_log: list[dict] | pd.DataFrame, out_path: str = "OTAI_Simulation_Nice.xlsx"
) -> str:
    df = (
        detailed_log
        if isinstance(detailed_log, pd.DataFrame)
        else pd.DataFrame(detailed_log)
    )

    overview_cols = [
        "month",
        "cash",
        "revenue",
        "total_costs",
        "net_cashflow",
        "website_users",
        "leads_total",
        "new_free",
        "new_pro",
        "new_ent",
        "free_active",
        "pro_active",
        "ent_active",
        "connector_count",
        "partners_active",
    ]

    reach_cols = [
        "month",
        "reach_share",
        "eff_total_market",
        "penetration",
        "friction_mult",
    ]

    reach_weight_cols = [c for c in df.columns if c.endswith("_weight")]
    if not reach_weight_cols:
        reach_weight_cols = [c for c in df.columns if c.startswith("weight_")]
    reach_cols = reach_cols + reach_weight_cols

    finance_cols = [
        "month",
        "revenue",
        "cost_ads",
        "cost_seo",
        "cost_social",
        "cost_overhead",
        "cost_dev_maint",
        "cost_dev_feat",
        "cost_partners",
        "total_costs",
        "net_cashflow",
        "cash",
    ]

    acq_cols = [
        "month",
        "ads_spend",
        "seo_spend",
        "pro_price",
        "seo_stock_users",
        "website_users",
        "website_leads",
        "referral_leads",
        "base_leads_hq",
        "base_leads_lq",
        "leads_hq",
        "leads_lq",
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

    partners_cols = [
        "month",
        "connector_count",
        "new_partners",
        "partner_pro_deals",
        "partner_ent_deals",
        "partners_active",
    ]

    def pick(cols: list[str]) -> pd.DataFrame:
        return df[[c for c in cols if c in df.columns]].copy()

    df_overview = pick(overview_cols)
    df_reach = pick(reach_cols)
    df_finance = pick(finance_cols)
    df_acq = pick(acq_cols)
    df_funnel = pick(funnel_cols)
    df_partners = pick(partners_cols)

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
            float(df["revenue"].sum()) if "revenue" in df.columns and len(df) else None,
        ),
        (
            "Avg revenue last 3 months (€)",
            float(df["revenue"].tail(3).mean())
            if "revenue" in df.columns and len(df) >= 3
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
            float(df["cost_ads"].sum())
            if "cost_ads" in df.columns and len(df)
            else None,
        ),
        (
            "Total SEO spend (€)",
            float(df["cost_seo"].sum())
            if "cost_seo" in df.columns and len(df)
            else None,
        ),
        (
            "Total Social spend (€)",
            float(df["cost_social"].sum())
            if "cost_social" in df.columns and len(df)
            else None,
        ),
        (
            "End connectors",
            float(df["connector_count"].iloc[-1])
            if "connector_count" in df.columns and len(df)
            else None,
        ),
        (
            "End partners",
            float(df["partners_active"].iloc[-1])
            if "partners_active" in df.columns and len(df)
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
        df_partners.to_excel(w, index=False, sheet_name="Partners")
        df_reach.to_excel(w, index=False, sheet_name="Reach")
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
        "Partners",
        "Reach",
        "Monthly_Full",
    ]:
        ws = wb[name]
        for col_name in [
            "cash",
            "revenue",
            "total_costs",
            "net_cashflow",
            "cost_ads",
            "cost_seo",
            "cost_social",
            "cost_overhead",
            "cost_dev_maint",
            "cost_dev_feat",
            "cost_partners",
        ]:
            idx = None
            for j in range(1, ws.max_column + 1):
                if ws.cell(row=1, column=j).value == col_name:
                    idx = j
                    break
            if idx:
                for r in range(2, ws.max_row + 1):
                    ws.cell(row=r, column=idx).number_format = '#,##0.00" €"'

    for name in [
        "Dashboard_Overview",
        "Acquisition",
        "Funnel",
        "Partners",
        "Reach",
        "Monthly_Full",
    ]:
        ws = wb[name]
        for col_name in ["reach_share", "penetration", "friction_mult"]:
            idx = None
            for j in range(1, ws.max_column + 1):
                if ws.cell(row=1, column=j).value == col_name:
                    idx = j
                    break
            if idx:
                for r in range(2, ws.max_row + 1):
                    ws.cell(row=r, column=idx).number_format = "0.00%"

    wb.save(out_path)
    return out_path
