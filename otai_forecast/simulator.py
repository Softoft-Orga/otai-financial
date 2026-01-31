from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .compute import (
    apply_churn,
    compute_finance,
    compute_leads,
    compute_new_ent,
    compute_new_free,
    compute_new_pro,
    compute_partners,
)
from .models import (
    Assumptions,
    Context,
    Policy,
    Roadmap,
    Row,
    State,
)


@dataclass
class BaseSimulator:
    """Base simulator with common functionality."""

    a: Assumptions
    roadmap: Roadmap
    policy: Policy

    def _create_initial_state(self) -> State:
        """Create the initial simulation state."""
        return State(
            t=0,
            cash=self.a.starting_cash_eur,
            free_active=0.0,
            pro_active=0.0,
            ent_active=0.0,
            partners=0.0,
        )

    def _create_initial_dev_progress(self) -> list[float]:
        """Create initial development progress tracking."""
        return [0.0] * len(self.roadmap.features)

    def _compute_monthly_metrics(
        self, state: State, ctx: Context, dev_progress: list[float]
    ) -> dict[str, Any]:
        """Compute all metrics for a month."""
        # Calculate maintenance days from active features only
        maintenance_days = self.roadmap.maintenance_days(dev_progress)

        # Spend additional dev days on new features
        additional_dev_available = ctx.inp.additional_dev_days

        # Update development progress
        updated_dev_progress = self.roadmap.update_progress(
            additional_dev_available, dev_progress
        )

        # Calculate feature development days completed this month
        feat_days_done = additional_dev_available

        # Compute leads
        leads = compute_leads(state, ctx)

        # Compute new customers
        new_free = compute_new_free(ctx, leads)
        new_pro = compute_new_pro(ctx, new_free)
        new_ent = compute_new_ent(ctx, new_pro)

        # Apply churn
        churned_free, free_after = apply_churn(state.free_active, ctx.a.churn_free)
        churned_pro, pro_after = apply_churn(state.pro_active, ctx.a.churn_pro)
        churned_ent, ent_after = apply_churn(state.ent_active, ctx.a.churn_ent)

        # Update active users
        new_free_active = free_after + new_free
        new_pro_active = pro_after + new_pro
        new_ent_active = ent_after + new_ent

        # Compute partners
        new_partners, partner_pro_deals, partner_ent_deals = compute_partners(
            state, ctx
        )
        total_partners = state.partners + new_partners

        # Add partner deals to active users
        new_pro_active += partner_pro_deals
        new_ent_active += partner_ent_deals

        # Compute finance
        finance = compute_finance(
            State(
                t=state.t,
                cash=state.cash,
                free_active=new_free_active,
                pro_active=new_pro_active,
                ent_active=new_ent_active,
                partners=total_partners,
            ),
            ctx,
            self.policy.p.pro_price,
            self.policy.p.ent_price,
            maintenance_days,
            feat_days_done,
        )

        return {
            "leads": leads,
            "new_free": new_free,
            "new_pro": new_pro,
            "new_ent": new_ent,
            "churned_free": churned_free,
            "churned_pro": churned_pro,
            "churned_ent": churned_ent,
            "free_active": new_free_active,
            "pro_active": new_pro_active,
            "ent_active": new_ent_active,
            "new_partners": new_partners,
            "partner_pro_deals": partner_pro_deals,
            "partner_ent_deals": partner_ent_deals,
            "partners": total_partners,
            "maintenance_days": maintenance_days,
            "feat_days_done": feat_days_done,
            "finance": finance,
            "dev_progress": updated_dev_progress,
        }


@dataclass
class Simulator(BaseSimulator):
    """Simple simulator that returns summary rows."""

    def step(
        self, state: State, dev_progress: list[float]
    ) -> tuple[State, Row, list[float]]:
        """Execute one simulation step."""
        inp = self.policy.inputs(state.t)
        ctx = Context(t=state.t, a=self.a, inp=inp)

        # Apply effects from active features
        active_features = self.roadmap.active(dev_progress)
        for feature in active_features:
            if feature.effect is not None:
                ctx = feature.effect(ctx)

        metrics = self._compute_monthly_metrics(state, ctx, dev_progress)

        # Update state
        state.free_active = metrics["free_active"]
        state.pro_active = metrics["pro_active"]
        state.ent_active = metrics["ent_active"]
        state.partners = metrics["partners"]

        # Handle credit draw
        credit_draw = 0.0
        if state.cash < ctx.a.credit_cash_threshold:
            credit_draw = ctx.a.credit_draw_amount
            state.debt += credit_draw

        state.cash += metrics["finance"].net_cashflow

        # Create output row
        row = Row(
            t=state.t,
            cash=state.cash,
            debt=state.debt,
            leads=metrics["leads"],
            free_active=state.free_active,
            pro_active=state.pro_active,
            ent_active=state.ent_active,
            partners=state.partners,
            revenue_total=metrics["finance"].revenue_total,
            net_cashflow=metrics["finance"].net_cashflow,
            profit_before_tax=metrics["finance"].profit_before_tax,
            profit_after_tax=metrics["finance"].profit_after_tax,
            mrr=metrics["finance"].mrr,
            arr=metrics["finance"].arr,
            market_cap=metrics["finance"].market_cap,
            interest_payment=metrics["finance"].interest_payment,
        )

        state.t += 1
        return state, row, metrics["dev_progress"]

    def run(self) -> list[Row]:
        """Run the full simulation."""
        state = self._create_initial_state()
        dev_progress = self._create_initial_dev_progress()
        rows: list[Row] = []

        for _ in range(self.a.months):
            state, row, dev_progress = self.step(state, dev_progress)
            rows.append(row)

        return rows


@dataclass
class DetailedSimulator(BaseSimulator):
    """Detailed simulator that returns all intermediate values."""

    def run(self) -> list[dict]:
        """Run the full simulation with detailed output."""
        state = self._create_initial_state()
        dev_progress = self._create_initial_dev_progress()
        data_log: list[dict] = []

        for _ in range(self.a.months):
            inp = self.policy.inputs(state.t)
            ctx = Context(t=state.t, a=self.a, inp=inp)

            # Apply effects from active features
            active_features = self.roadmap.active(dev_progress)
            for feature in active_features:
                if feature.effect is not None:
                    ctx = feature.effect(ctx)

            metrics = self._compute_monthly_metrics(state, ctx, dev_progress)

            # Update state
            state.free_active = metrics["free_active"]
            state.pro_active = metrics["pro_active"]
            state.ent_active = metrics["ent_active"]
            state.partners = metrics["partners"]
            state.cash += metrics["finance"].net_cashflow

            # Create detailed row
            row = {
                "month": state.t,
                "cash": state.cash,
                "ads_spend": ctx.inp.ads_spend,
                "social_spend": ctx.inp.social_spend,
                "leads": metrics["leads"],
                "new_free": metrics["new_free"],
                "new_pro": metrics["new_pro"],
                "new_ent": metrics["new_ent"],
                "churned_free": metrics["churned_free"],
                "churned_pro": metrics["churned_pro"],
                "churned_ent": metrics["churned_ent"],
                "new_partners": metrics["new_partners"],
                "partner_pro_deals": metrics["partner_pro_deals"],
                "partner_ent_deals": metrics["partner_ent_deals"],
                "partners_active": state.partners,
                "free_active": state.free_active,
                "pro_active": state.pro_active,
                "ent_active": state.ent_active,
                "revenue": metrics["finance"].revenue_total,
                "cost_ads": ctx.inp.ads_spend,
                "cost_social": ctx.inp.social_spend,
                "cost_ops": ctx.a.ops_fixed_eur_per_month,
                "cost_dev_maint": metrics["maintenance_days"] * ctx.a.dev_day_cost_eur,
                "cost_dev_feat": metrics["feat_days_done"] * ctx.a.dev_day_cost_eur,
                "cost_partners": ctx.a.partner_commission_rate
                * metrics["finance"].revenue_total,
                "total_costs": (
                    ctx.inp.ads_spend
                    + ctx.inp.social_spend
                    + ctx.a.ops_fixed_eur_per_month
                    + metrics["maintenance_days"] * ctx.a.dev_day_cost_eur
                    + metrics["feat_days_done"] * ctx.a.dev_day_cost_eur
                    + ctx.a.partner_commission_rate * metrics["finance"].revenue_total
                ),
                "net_cashflow": metrics["finance"].net_cashflow,
            }
            data_log.append(row)

            state.t += 1
            dev_progress = metrics["dev_progress"]

        return data_log


def rows_to_dicts(rows: list[Row]) -> list[dict]:
    return [asdict(r) for r in rows]
