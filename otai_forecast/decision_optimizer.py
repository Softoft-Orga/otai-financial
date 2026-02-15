from __future__ import annotations

import numpy as np
import optuna
import optuna.exceptions
import pandas as pd
import pydantic

from .models import Assumptions, MonthlyDecision
from .simulator import Simulator


def add_market_cap_columns(df: pd.DataFrame, a: Assumptions) -> pd.DataFrame:
    df = df.copy()
    df["revenue_ttm"] = df["revenue_total"].rolling(window=12, min_periods=1).sum()
    
    # Calculate revenue growth rate (6-month average for stability)
    revenue_growth = df["revenue_total"].pct_change().rolling(window=6, min_periods=1).mean()
    
    # Growth multiplier: higher growth increases the market cap multiple
    growth_multiplier = 1 + 2 * revenue_growth.clip(lower=-0.5, upper=1)  # Between 0.5x and 3x
    
    # Cash burn penalty: burning cash reduces the multiple
    cash_change = df["cash"].diff().fillna(0)
    burn_penalty = 1 - 0.2 * (cash_change < 0).astype(float) * (-cash_change / df["revenue_ttm"]).clip(upper=0.5)
    
    # Dynamic market cap multiple based on growth and profitability
    dynamic_multiple = a.market_cap_multiple * growth_multiplier * burn_penalty
    
    # Enterprise value: apply dynamic multiple to revenue
    enterprise_value = df["revenue_ttm"] * dynamic_multiple
    
    # Net cash position: cash minus 2x debt (debt is more punitive)
    net_cash = 0.1 * df["cash"] - 0.5 *df["debt"]
    
    # Final market cap: enterprise value plus net cash
    df["market_cap"] = enterprise_value + net_cash
    return df


def run_simulation_df(a: Assumptions, decisions: list[MonthlyDecision]) -> pd.DataFrame:
    df = pd.DataFrame(Simulator(a=a, decisions=decisions).run_rows())
    return add_market_cap_columns(df, a)


def _lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b."""
    t = max(0.0, min(1.0, t))
    return a + (b - a) * t


def _linear_interpolate_knots(knots: list[float], months: int) -> list[float]:
    """
    Linear interpolation between knots.

    Args:
        knots: List of values at knot positions
        months: Total number of months to interpolate

    Returns:
        List of interpolated values for each month
    """
    if len(knots) < 2:
        raise ValueError("At least 2 knots are required.")
    if months <= 1:
        return [knots[0]] * months

    knot_positions = np.linspace(0, months - 1, num=len(knots))
    month_positions = np.arange(months)
    return np.interp(month_positions, knot_positions, knots).tolist()


def scale_decisions_with_knots(
        base_decisions: list[MonthlyDecision],
        *,
        ads_knots: list[float],
        seo_knots: list[float],
        dev_knots: list[float],
        partner_knots: list[float],
        outreach_knots: list[float],
) -> list[MonthlyDecision]:
    """
    Scale decisions using knots per lever with linear interpolation.

    Args:
        base_decisions: Base monthly decisions to scale
        ads_knots: Scaling factors for ads budget at knot positions
        seo_knots: Scaling factors for SEO budget at knot positions
        dev_knots: Scaling factors for dev budget at knot positions
        partner_knots: Scaling factors for partner budget at knot positions
        outreach_knots: Scaling factors for outreach budget at knot positions

    Returns:
        Scaled monthly decisions
    """
    knot_counts = {
        len(ads_knots),
        len(seo_knots),
        len(dev_knots),
        len(partner_knots),
        len(outreach_knots),
    }
    if len(knot_counts) != 1:
        raise ValueError("All decision variables must use the same number of knots.")
    knot_count = next(iter(knot_counts))
    if knot_count < 2:
        raise ValueError("At least 2 knots are required.")

    months = len(base_decisions)

    # Interpolate scaling factors for each month
    ads_multipliers = _linear_interpolate_knots(ads_knots, months)
    seo_multipliers = _linear_interpolate_knots(seo_knots, months)
    dev_multipliers = _linear_interpolate_knots(dev_knots, months)
    partner_multipliers = _linear_interpolate_knots(partner_knots, months)
    outreach_multipliers = _linear_interpolate_knots(outreach_knots, months)

    out = []
    for i, base_decision in enumerate(base_decisions):
        out.append(
            MonthlyDecision(
                ads_budget=max(0.0, base_decision.ads_budget * ads_multipliers[i]),
                seo_budget=max(0.0, base_decision.seo_budget * seo_multipliers[i]),
                dev_budget=max(0.0, base_decision.dev_budget * dev_multipliers[i]),
                partner_budget=max(
                    0.0, base_decision.partner_budget * partner_multipliers[i]
                ),
                outreach_budget=max(
                    0.0, base_decision.outreach_budget * outreach_multipliers[i]
                ),
            )
        )

    return out


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
    """Legacy function using exponential scaling. Use scale_decisions_with_knots for new code."""
    out: list[MonthlyDecision] = []
    months = len(decisions)

    def _time_mult(start: float, end: float, t_index: int) -> float:
        if months <= 1:
            return start
        t = max(0.0, min(1.0, t_index / (months - 1)))
        if start <= 0.0 or end <= 0.0:
            return _lerp(start, end, t)
        return start * ((end / start) ** t)

    for i, d in enumerate(decisions):
        ads_mult = _time_mult(ads_start, ads_end, i)
        seo_mult = _time_mult(seo_start, seo_end, i)
        dev_mult = _time_mult(dev_start, dev_end, i)
        partner_mult = _time_mult(partner_start, partner_end, i)
        direct_outreach_mult = _time_mult(direct_outreach_start, direct_outreach_end, i)

        out.append(
            MonthlyDecision(
                ads_budget=max(0.0, d.ads_budget * ads_mult),
                seo_budget=max(0.0, d.seo_budget * seo_mult),
                dev_budget=max(0.0, d.dev_budget * dev_mult),
                partner_budget=max(0.0, d.partner_budget * partner_mult),
                outreach_budget=max(0.0, d.outreach_budget * direct_outreach_mult),
            )
        )

    return out


def choose_best_decisions_by_market_cap(
        a: Assumptions,
        base: list[MonthlyDecision],
        *,
        max_evals: int = 500,
        seed: int = 0,
        study_name: str | None = None,
        num_knots: int = 4,
        knot_low: float = 0.0,
        knot_high: float = 5.0,
        knot_lows: list[float] | None = None,
        knot_highs: list[float] | None = None,
        knot_config: dict[str, dict[str, list[float]]] | None = None,
) -> tuple[list[MonthlyDecision], pd.DataFrame]:
    """
    Optimize decisions using Optuna with TPE sampler.

    Uses a configurable number of knots per lever with linear interpolation.

    Args:
        a: Assumptions for the simulation
        base: Base monthly decisions to scale
        max_evals: Maximum number of trials (default: 500)
        seed: Random seed for reproducibility
        study_name: Optional name for the Optuna study
        num_knots: Number of knots per lever
        knot_low: Lower bound for knot values
        knot_high: Upper bound for knot values
        knot_lows: Optional per-knot lower bounds (length == num_knots)
        knot_highs: Optional per-knot upper bounds (length == num_knots)
        knot_config: Optional per-decision knot bounds. Dict mapping decision
            name ("ads", "seo", "dev", "partner", "outreach") to
            {"lows": [...], "highs": [...]}. Overrides knot_lows/knot_highs.
        
    Returns:
        Tuple of (best_decisions, best_dataframe)
    """
    if num_knots < 2:
        raise ValueError("num_knots must be at least 2.")
    if knot_config is None:
        if knot_low >= knot_high:
            raise ValueError("knot_low must be less than knot_high.")
        if (knot_lows is None) ^ (knot_highs is None):
            raise ValueError("knot_lows and knot_highs must be provided together.")
        if knot_lows is not None and knot_highs is not None:
            if len(knot_lows) != num_knots or len(knot_highs) != num_knots:
                raise ValueError("knot_lows and knot_highs must match num_knots length.")

    # Create study with TPE sampler and pruner
    sampler = optuna.samplers.TPESampler(seed=seed)

    if study_name is None:
        import random
        random_id = random.randint(0, 10 ** 9 - 1)
        study_name = f"otai_optimization_{a.months}m_{random_id}"

    study = optuna.create_study(
        study_name=study_name,
        sampler=sampler,
        direction="maximize"
    )

    def _suggest_knots(trial: optuna.Trial, prefix: str) -> list[float]:
        if knot_config is not None and prefix in knot_config:
            cfg = knot_config[prefix]
            return [
                trial.suggest_float(
                    f"{prefix}_knot_{i}",
                    cfg["lows"][i],
                    cfg["highs"][i],
                )
                for i in range(num_knots)
            ]
        if knot_lows is not None and knot_highs is not None:
            return [
                trial.suggest_float(
                    f"{prefix}_knot_{i}",
                    knot_lows[i],
                    knot_highs[i],
                )
                for i in range(num_knots)
            ]
        return [
            trial.suggest_float(f"{prefix}_knot_{i}", knot_low, knot_high)
            for i in range(num_knots)
        ]

    def objective(trial: optuna.Trial) -> float:
        knot_sets = {
            name: _suggest_knots(trial, name)
            for name in ("ads", "seo", "dev", "partner", "outreach")
        }

        # Scale decisions using knots
        decisions = scale_decisions_with_knots(
            base,
            ads_knots=knot_sets["ads"],
            seo_knots=knot_sets["seo"],
            dev_knots=knot_sets["dev"],
            partner_knots=knot_sets["partner"],
            outreach_knots=knot_sets["outreach"],
        )

        # Run simulation with error handling
        try:
            df = run_simulation_df(a, decisions)
        except (ValueError, pydantic.ValidationError):
            # Return a small value for any validation errors
            print("ERROR")
            return -1

        # Report intermediate values every month for pruning
        for month_idx in range(len(df)):
            # Report market cap at each month
            trial.report(float(df["market_cap"].iloc[month_idx]), step=month_idx)

        # Check if cash went too small (constraint violation)
        if df["cash"].min() < a.minimum_cash_balance:
            # Return a small value for constraint violations
            return df["cash"].min() - a.minimum_cash_balance

        # Check liquidity constraint using liquid assets proxy:
        # cash + product_value + one-month average revenue (TTM/12) / debt
        # Avoid division by zero by handling months with no debt
        liquidity_ratios = df.apply(
            lambda row: (
                row["cash"] + row["product_value"] + (row["revenue_ttm"] / 12)
            ) / (row["debt"] + 1),
            axis=1,
        )

        final_market_cap = float(df["market_cap"].iloc[-1])
        min_liquidity_ratio = liquidity_ratios.min()

        # Check if liquidity constraint is violated (ratio too low)
        if min_liquidity_ratio < a.minimum_liquidity_ratio:
            # Penalize based on how much the constraint is violated
            return final_market_cap - (a.minimum_liquidity_ratio - min_liquidity_ratio) * final_market_cap

        # Return final market cap as objective
        return final_market_cap

    # Optimize
    study.optimize(objective, n_trials=max_evals, n_jobs=14)

    # Get best trial
    best_trial = study.best_trial

    # Extract best knots
    def _extract_knots(prefix: str) -> list[float]:
        return [best_trial.params[f"{prefix}_knot_{i}"] for i in range(num_knots)]

    best_ads_knots = _extract_knots("ads")
    best_seo_knots = _extract_knots("seo")
    best_dev_knots = _extract_knots("dev")
    best_partner_knots = _extract_knots("partner")
    best_outreach_knots = _extract_knots("outreach")

    # Generate best decisions
    best_decisions = scale_decisions_with_knots(
        base,
        ads_knots=best_ads_knots,
        seo_knots=best_seo_knots,
        dev_knots=best_dev_knots,
        partner_knots=best_partner_knots,
        outreach_knots=best_outreach_knots,
    )

    # Run simulation one more time to get the dataframe
    try:
        best_df = run_simulation_df(a, best_decisions)
    except (ValueError, pydantic.ValidationError):
        # If even the best solution fails, fall back to base decisions
        try:
            best_df = run_simulation_df(a, base)
            best_decisions = base
        except (ValueError, pydantic.ValidationError):
            # If base decisions also fail, create minimal decisions
            minimal_decisions = [
                MonthlyDecision(
                    ads_budget=100.0,
                    seo_budget=100.0,
                    dev_budget=100.0,
                    partner_budget=50.0,
                    outreach_budget=100.0,
                )
                for _ in range(a.months)
            ]
            best_df = run_simulation_df(a, minimal_decisions)
            best_decisions = minimal_decisions

    # Store study in a global dict for potential analysis
    if not hasattr(choose_best_decisions_by_market_cap, "_studies"):
        choose_best_decisions_by_market_cap._studies = {}  # type: ignore[attr-defined]
    choose_best_decisions_by_market_cap._studies[study_name] = study  # type: ignore[attr-defined]

    return best_decisions, best_df
