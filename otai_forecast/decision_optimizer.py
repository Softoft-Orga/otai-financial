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
    scraping_start: float,
    scraping_end: float,
    outreach_start: float,
    outreach_end: float,
) -> list[MonthlyDecision]:
    out: list[MonthlyDecision] = []
    months = len(decisions)
    for i, d in enumerate(decisions):
        ads_mult = _time_mult(ads_start, ads_end, i, months)
        seo_mult = _time_mult(seo_start, seo_end, i, months)
        dev_mult = _time_mult(dev_start, dev_end, i, months)
        scraping_mult = _time_mult(scraping_start, scraping_end, i, months)
        outreach_mult = _time_mult(outreach_start, outreach_end, i, months)

        out.append(
            MonthlyDecision(
                ads_spend=max(0.0, d.ads_spend * ads_mult),
                seo_spend=max(0.0, d.seo_spend * seo_mult),
                social_spend=d.social_spend,
                dev_spend=max(0.0, d.dev_spend * dev_mult),
                scraping_spend=max(0.0, d.scraping_spend * scraping_mult),
                outreach_intensity=max(0.0, min(1.0, d.outreach_intensity * outreach_mult)),
                pro_price_override=d.pro_price_override,
                ent_price_override=d.ent_price_override,
            )
        )

    return out


def choose_best_decisions_by_market_cap(
    a: Assumptions,
    base: list[MonthlyDecision],
    *,
    max_evals: int = 25_000,
    seed: int = 0,
) -> tuple[list[MonthlyDecision], pd.DataFrame]:
    best_score = -1.0
    best_df: pd.DataFrame | None = None
    best_decisions = base

    rng = random.Random(seed)
    for _ in range(int(max_evals)):
        ads_start = rng.uniform(0.0, 3.0)
        ads_end = rng.uniform(0.0, 3.0)
        seo_start = rng.uniform(0.0, 3.0)
        seo_end = rng.uniform(0.0, 3.0)
        dev_start = rng.uniform(0.5, 1.5)
        dev_end = rng.uniform(0.5, 1.5)
        scraping_start = rng.uniform(0.0, 3.0)
        scraping_end = rng.uniform(0.0, 3.0)
        outreach_start = rng.uniform(0.75, 1.25)
        outreach_end = rng.uniform(0.75, 1.25)

        decisions = scale_decisions_time_ramp(
            base,
            ads_start=ads_start,
            ads_end=ads_end,
            seo_start=seo_start,
            seo_end=seo_end,
            dev_start=dev_start,
            dev_end=dev_end,
            scraping_start=scraping_start,
            scraping_end=scraping_end,
            outreach_start=outreach_start,
            outreach_end=outreach_end,
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
