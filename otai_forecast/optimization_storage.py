from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .models import Assumptions, MonthlyDecision, ScenarioAssumptions


def assumptions_hash(assumptions: Assumptions) -> str:
    payload = json.dumps(
        assumptions.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def optimization_path(base_dir: Path, assumption_hash: str) -> Path:
    return base_dir / f"optimization_{assumption_hash}.yaml"


def load_optimization(base_dir: Path, assumption_hash: str) -> dict | None:
    path = optimization_path(base_dir, assumption_hash)
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def save_optimization(
    assumptions: Assumptions,
    decisions: list[MonthlyDecision],
    df: pd.DataFrame,
    *,
    base_dir: Path,
    scenario_assumptions: Iterable[ScenarioAssumptions] | None = None,
) -> str:
    base_dir.mkdir(parents=True, exist_ok=True)
    assumption_hash = assumptions_hash(assumptions)
    if scenario_assumptions is None:
        scenario_assumptions = []
    payload = _build_payload(
        assumptions,
        decisions,
        df,
        assumption_hash=assumption_hash,
        scenario_assumptions=scenario_assumptions,
    )
    path = optimization_path(base_dir, assumption_hash)
    existing = load_optimization(base_dir, assumption_hash)
    if _existing_beats_payload(existing, payload):
        return assumption_hash
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return assumption_hash


def _build_payload(
    assumptions: Assumptions,
    decisions: list[MonthlyDecision],
    df: pd.DataFrame,
    *,
    assumption_hash: str,
    scenario_assumptions: Iterable[ScenarioAssumptions],
) -> dict[str, Any]:
    return {
        "saved_at": datetime.utcnow().isoformat(),
        "assumption_hash": assumption_hash,
        "assumptions": assumptions.model_dump(),
        "assumption_scenarios": [
            scenario.model_dump() for scenario in scenario_assumptions
        ],
        "decisions": [decision.model_dump() for decision in decisions],
        "summary": {
            "end_market_cap": float(df["market_cap"].iloc[-1]),
            "end_cash": float(df["cash"].iloc[-1]),
            "min_cash": float(df["cash"].min()),
        },
    }


def _existing_beats_payload(existing: dict | None, payload: dict[str, Any]) -> bool:
    existing_cap = _extract_market_cap(existing)
    candidate_cap = _extract_market_cap(payload)
    if existing_cap is None or candidate_cap is None:
        return False
    return existing_cap >= candidate_cap


def _extract_market_cap(payload: dict | None) -> float | None:
    if not isinstance(payload, dict):
        return None
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return None
    value = summary.get("end_market_cap")
    if isinstance(value, (int, float)):
        return float(value)
    return None
