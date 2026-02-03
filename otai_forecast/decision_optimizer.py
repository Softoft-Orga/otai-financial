from __future__ import annotations

import random

import pandas as pd

from .models import Assumptions, MonthlyDecision
from .simulator import Simulator


def add_market_cap_columns(df: pd.DataFrame, a: Assumptions) -> pd.DataFrame:
    df = df.copy()
    df["revenue_ttm"] = df["revenue_total"].rolling(window=12, min_periods=1).sum()
    df["market_cap"] = df["revenue_ttm"] * a.market_cap_multiple
    return df


def run_simulation_df(a: Assumptions, decisions: list[MonthlyDecision]) -> pd.DataFrame:
    df = pd.DataFrame(Simulator(a=a, decisions=decisions).run_rows())
    return add_market_cap_columns(df, a)


def _lerp(a: float, b: float, t: float) -> float:
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def _time_mult(start: float, end: float, t_index: int, months: int) -> float:
    if months <= 1:
        return start
    t = max(0.0, min(1.0, t_index / (months - 1)))
    if start <= 0.0 or end <= 0.0:
        return _lerp(start, end, t)
    return start * ((end / start) ** t)


def scale_decisions_time_ramp(
    decisions: list[MonthlyDecision],
    *,
    ads_start: float,
    ads_end: float,
    seo_start: float,
    seo_end: float,
    dev_start: float,
    dev_end: float,
    partner_start: float,
    partner_end: float,
    direct_outreach_start: float,
    direct_outreach_end: float,
) -> list[MonthlyDecision]:
    out: list[MonthlyDecision] = []
    months = len(decisions)
    for i, d in enumerate(decisions):
        ads_mult = _time_mult(ads_start, ads_end, i, months)
        seo_mult = _time_mult(seo_start, seo_end, i, months)
        dev_mult = _time_mult(dev_start, dev_end, i, months)
        partner_mult = _time_mult(partner_start, partner_end, i, months)
        direct_outreach_mult = _time_mult(
            direct_outreach_start, direct_outreach_end, i, months
        )

        out.append(
            MonthlyDecision(
                ads_budget=max(0.0, d.ads_budget * ads_mult),
                seo_budget=max(0.0, d.seo_budget * seo_mult),
                dev_budget=max(0.0, d.dev_budget * dev_mult),
                partner_budget=max(0.0, d.partner_budget * partner_mult),
                outreach_budget=max(
                    0.0, d.outreach_budget * direct_outreach_mult
                ),
            )
        )

    return out


def choose_best_decisions_by_market_cap(
    a: Assumptions,
    base: list[MonthlyDecision],
    *,
    max_evals: int = 10_000,
    seed: int = 0,
) -> tuple[list[MonthlyDecision], pd.DataFrame]:
    best_score = -1.0
    best_df: pd.DataFrame | None = None
    best_decisions = base

    rng = random.Random(seed)
    for _ in range(int(max_evals)):
        ads_start = rng.uniform(0.0, 10)
        ads_end = rng.uniform(0.0, 10)
        seo_start = rng.uniform(0.0, 10)
        seo_end = rng.uniform(0.0, 10)
        dev_start = rng.uniform(0.0, 10)
        dev_end = rng.uniform(0.0, 10)
        partner_start = rng.uniform(0.0, 3.0)
        partner_end = rng.uniform(0.0, 3.0)
        direct_outreach_start = rng.uniform(0.0, 10)
        direct_outreach_end = rng.uniform(0.0, 10)

        decisions = scale_decisions_time_ramp(
            base,
            ads_start=ads_start,
            ads_end=ads_end,
            seo_start=seo_start,
            seo_end=seo_end,
            dev_start=dev_start,
            dev_end=dev_end,
            partner_start=partner_start,
            partner_end=partner_end,
            direct_outreach_start=direct_outreach_start,
            direct_outreach_end=direct_outreach_end,
        )

        df = run_simulation_df(a, decisions)
        if df["cash"].min() < 0:
            continue

        score = float(df["market_cap"].iloc[-1])
        if score > best_score:
            best_score = score
            best_df = df
            best_decisions = decisions

    if best_df is None:
        best_df = run_simulation_df(a, base)

    return best_decisions, best_df
