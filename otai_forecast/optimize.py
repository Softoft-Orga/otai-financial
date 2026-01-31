from __future__ import annotations

import random
from dataclasses import dataclass

import pandas as pd

from otai_forecast.config import (
    DEFAULT_DEV_PARAMS,
    DEFAULT_OPTIMIZATION_RANGES,
    DEFAULT_PRICES,
)
from otai_forecast.models import (
    Assumptions,
    Policy,
    PolicyParams,
    Roadmap,
)
from otai_forecast.simulator import Simulator


@dataclass
class OptimizationResult:
    """Result of an optimization run."""

    best_params: PolicyParams
    best_score: float
    all_results: list[tuple[PolicyParams, float]]


class PolicyOptimizer:
    """Simple optimizer for policy parameters using random search."""

    def __init__(
        self,
        assumptions: Assumptions,
        roadmap: Roadmap,
        param_ranges: dict[str, tuple[float, float]] | None = None,
    ):
        """
        Initialize the optimizer.

        Args:
            assumptions: Fixed assumptions for the simulation
            roadmap: Fixed roadmap for the simulation
            param_ranges: Optional dict of parameter ranges to optimize
        """
        self.assumptions = assumptions
        self.roadmap = roadmap

        # Use provided parameter ranges or default to centralized config
        self.param_ranges = param_ranges or DEFAULT_OPTIMIZATION_RANGES

    def random_params(self) -> PolicyParams:
        """Generate random policy parameters within the defined ranges."""
        params = {}
        for param_name, (min_val, max_val) in self.param_ranges.items():
            params[param_name] = random.uniform(min_val, max_val)

        # Fixed pricing (not optimized)
        params.update(DEFAULT_PRICES)
        params.update(DEFAULT_DEV_PARAMS)

        # Ensure caps are >= starts
        if params["ads_cap"] < params["ads_start"]:
            params["ads_cap"] = params["ads_start"]

        return PolicyParams(**params)

    def evaluate_params(self, params: PolicyParams) -> float:
        """
        Evaluate a set of parameters and return the score.
        Maximize final market cap while ensuring cash never goes negative.
        """
        policy = Policy(p=params)
        sim = Simulator(a=self.assumptions, roadmap=self.roadmap, policy=policy)
        rows = sim.run()
        df = pd.DataFrame([r.__dict__ for r in rows])

        final_market_cap = df["market_cap"].iloc[-1]
        min_cash = df["cash"].min()

        # If cash goes negative, return a very bad score
        if min_cash < 0:
            return -999999999

        return final_market_cap

    def optimize(
        self, n_iterations: int = 100, verbose: bool = False
    ) -> OptimizationResult:
        """
        Optimize using random search.

        Args:
            n_iterations: Number of random parameter sets to try
            verbose: Whether to print progress

        Returns:
            OptimizationResult with best parameters and scores
        """
        best_score = float("-inf")
        best_params = None
        all_results = []

        for i in range(n_iterations):
            params = self.random_params()
            score = self.evaluate_params(params)
            all_results.append((params, score))

            if score > best_score:
                best_score = score
                best_params = params

            if verbose and (i + 1) % 10 == 0:
                print(
                    f"Iteration {i + 1}/{n_iterations}, Best Score: €{best_score:,.2f}"
                )

        return OptimizationResult(
            best_params=best_params,
            best_score=best_score,
            all_results=all_results,
        )
