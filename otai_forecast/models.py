from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

Month = int
EffectFn = Callable[["Context"], "Context"]


@dataclass(frozen=True)
class Assumptions:
    months: int

    dev_day_cost_eur: float = field()
    starting_cash_eur: float = field()

    ops_fixed_eur_per_month: float = field()

    # Marketing parameters
    ads_cost_per_lead_base: float = field()
    monthly_ads_expense: float = field()
    brand_popularity: float = field()

    # Conversion rates
    conv_lead_to_free: float = field()
    conv_free_to_pro: float = field()
    conv_pro_to_ent: float = field()

    churn_free: float = field()
    churn_pro: float = field()
    churn_ent: float = field()

    referral_leads_per_active_free: float = field()

    partner_commission_rate: float = field()
    pro_deals_per_partner_per_month: float = field()
    ent_deals_per_partner_per_month: float = field()
    new_partners_base_per_month: float = field()

    valuation_multiple_arr: float = field()
    credit_interest_rate_annual: float = field()
    credit_draw_amount: float = field()
    credit_cash_threshold: float = field()

    def __post_init__(self):
        if self.credit_interest_rate_annual < 0:
            raise ValueError("Credit interest rate must be non-negative")
        if self.credit_draw_amount < 0:
            raise ValueError("Credit draw amount must be non-negative")


@dataclass(frozen=True)
class PolicyParams:
    ads_start: float = field()
    ads_growth: float = field()
    ads_cap: float = field()

    social_baseline: float = field()

    additional_dev_days: float = (
        field()
    )  # Additional dev days per month for new features

    pro_price: float = field()
    ent_price: float = field()

    def __post_init__(self):
        if self.ads_cap < self.ads_start:
            raise ValueError("Ads cap must be >= ads start")


@dataclass(frozen=True)
class MonthlyInputs:
    ads_spend: float = field()
    social_spend: float = field()
    additional_dev_days: float = field()  # Additional dev days for new features


@dataclass
class Policy:
    p: PolicyParams

    def inputs(self, t: Month) -> MonthlyInputs:
        ads = min(self.p.ads_cap, self.p.ads_start * ((1 + self.p.ads_growth) ** t))
        return MonthlyInputs(
            ads_spend=ads,
            social_spend=self.p.social_baseline,
            additional_dev_days=self.p.additional_dev_days,
        )


@dataclass(frozen=True)
class Feature:
    name: str
    dev_days: float = field()
    maintenance_days_per_month: float = field()
    effect: EffectFn

    def is_active(self, dev_days_completed: float) -> bool:
        return dev_days_completed >= self.dev_days


@dataclass
class Roadmap:
    features: list[Feature] = field(default_factory=list)
    current_feature_idx: int = 0
    dev_days_spent_on_current: float = 0.0

    def active(self, dev_days_completed_per_feature: list[float]) -> list[Feature]:
        """Return list of features that are active based on development progress."""
        active = []
        for i, (feature, days_completed) in enumerate(
            zip(self.features, dev_days_completed_per_feature, strict=False)
        ):
            if feature.is_active(days_completed):
                active.append(feature)
        return active

    def maintenance_days(self, dev_days_completed_per_feature: list[float]) -> float:
        """Calculate total maintenance days for active features."""
        return sum(
            f.maintenance_days_per_month
            for f, days_completed in zip(
                self.features, dev_days_completed_per_feature, strict=False
            )
            if f.is_active(days_completed)
        )

    def get_next_feature(self) -> Feature | None:
        """Get the next feature to be developed."""
        if self.current_feature_idx < len(self.features):
            return self.features[self.current_feature_idx]
        return None

    def update_progress(
        self, additional_dev_days: float, dev_days_completed_per_feature: list[float]
    ) -> list[float]:
        """Update development progress based on additional dev days spent."""
        updated = dev_days_completed_per_feature.copy()

        # Add development days to current feature
        if self.current_feature_idx < len(self.features):
            updated[self.current_feature_idx] += additional_dev_days

            # Check if current feature is complete
            if (
                updated[self.current_feature_idx]
                >= self.features[self.current_feature_idx].dev_days
            ):
                # Move to next feature
                self.current_feature_idx += 1
                self.dev_days_spent_on_current = 0.0
            else:
                self.dev_days_spent_on_current = updated[self.current_feature_idx]

        return updated

    def add_feature(self, feature: Feature) -> None:
        self.features.append(feature)


@dataclass(frozen=True)
class Context:
    t: Month
    a: Assumptions
    inp: MonthlyInputs


@dataclass
class State:
    t: Month = field()
    cash: float = field()
    free_active: float = field()
    pro_active: float = field()
    ent_active: float = field()
    partners: float = field()
    debt: float = 0.0

    def reached_orgs(self) -> float:
        return self.free_active + self.pro_active + self.ent_active

    def copy_with_updates(self, **kwargs) -> State:
        from dataclasses import replace

        return replace(self, **kwargs)


@dataclass(frozen=True)
class Finance:
    revenue_total: float
    net_cashflow: float
    profit_before_tax: float
    profit_after_tax: float
    mrr: float
    arr: float
    market_cap: float
    debt: float
    interest_payment: float


@dataclass(frozen=True)
class Row:
    t: Month
    cash: float
    debt: float
    leads: float
    free_active: float
    pro_active: float
    ent_active: float
    partners: float
    revenue_total: float
    net_cashflow: float
    profit_before_tax: float
    profit_after_tax: float
    mrr: float
    arr: float
    market_cap: float
    interest_payment: float
