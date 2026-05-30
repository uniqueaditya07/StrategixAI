"""KPI and simulation output schemas for StrategixAI.

These schemas describe normalized outputs from future simulation and analytics
modules. They intentionally contain no simulation logic.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


NonNegativeFloat = Annotated[float, Field(ge=0.0)]
Rate = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]


class MetricsSchema(BaseModel):
    """Base schema with strict validation behavior for KPI contracts."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class MetricTrend(StrEnum):
    """Directional movement for a KPI compared with a prior period."""

    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"
    UNKNOWN = "unknown"


class MetricUnit(StrEnum):
    """Standard display units for metrics."""

    CURRENCY = "currency"
    COUNT = "count"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    MONTHS = "months"
    DAYS = "days"


class FinancialMetrics(MetricsSchema):
    """Financial KPIs produced by simulations or analytics pipelines."""

    monthly_recurring_revenue: NonNegativeFloat = 0.0
    annual_recurring_revenue: NonNegativeFloat = 0.0
    revenue: NonNegativeFloat = 0.0
    gross_profit: float = 0.0
    gross_margin: Rate = 0.0
    operating_expenses: NonNegativeFloat = 0.0
    net_income: float = 0.0
    cash_balance: float = 0.0
    burn_rate: NonNegativeFloat = 0.0
    runway_months: NonNegativeFloat | None = Field(
        default=None,
        description="Estimated cash runway in months; null when not meaningful.",
    )


class CustomerMetrics(MetricsSchema):
    """Customer base, retention, and revenue quality KPIs."""

    active_customers: NonNegativeInt = 0
    new_customers: NonNegativeInt = 0
    churned_customers: NonNegativeInt = 0
    reactivated_customers: NonNegativeInt = 0
    logo_churn_rate: Rate = 0.0
    revenue_churn_rate: Rate = 0.0
    net_revenue_retention: NonNegativeFloat = Field(
        default=1.0,
        description="Net revenue retention expressed as a multiplier.",
    )
    average_revenue_per_user: NonNegativeFloat = 0.0
    customer_lifetime_value: NonNegativeFloat = 0.0


class MarketingMetrics(MetricsSchema):
    """Acquisition efficiency and funnel KPIs."""

    marketing_spend: NonNegativeFloat = 0.0
    leads: NonNegativeInt = 0
    acquired_customers: NonNegativeInt = 0
    blended_cac: NonNegativeFloat = 0.0
    conversion_rate: Rate = 0.0
    payback_period_months: NonNegativeFloat | None = Field(
        default=None,
        description="CAC payback period in months; null when unavailable.",
    )
    ltv_to_cac_ratio: NonNegativeFloat | None = Field(
        default=None,
        description="LTV/CAC ratio; null when CAC is zero or unavailable.",
    )


class KPIMetric(MetricsSchema):
    """Generic KPI record for dashboards, analytics tables, and AI context."""

    name: str = Field(min_length=1, max_length=120)
    value: float
    unit: MetricUnit
    trend: MetricTrend = MetricTrend.UNKNOWN
    benchmark: float | None = Field(default=None)
    target: float | None = Field(default=None)
    insight: str | None = Field(default=None, max_length=500)


class KPISnapshot(MetricsSchema):
    """A consolidated KPI snapshot for a single simulation period."""

    period: PositiveInt = Field(description="One-based simulation period number.")
    financial: FinancialMetrics = Field(default_factory=FinancialMetrics)
    customer: CustomerMetrics = Field(default_factory=CustomerMetrics)
    marketing: MarketingMetrics = Field(default_factory=MarketingMetrics)
    custom_metrics: tuple[KPIMetric, ...] = Field(default_factory=tuple)


class SimulationPeriodOutput(MetricsSchema):
    """Simulation output for one forecast period."""

    period: PositiveInt
    label: str = Field(min_length=1, max_length=80)
    kpis: KPISnapshot
    notes: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Optional engine-generated explanations for the period.",
    )

    @model_validator(mode="after")
    def validate_period_alignment(self) -> "SimulationPeriodOutput":
        """Ensure period metadata is consistent across nested KPI data."""

        if self.kpis.period != self.period:
            raise ValueError("kpis.period must match period")
        return self


class SimulationSummary(MetricsSchema):
    """High-level summary of a completed simulation run."""

    starting_cash_balance: float = 0.0
    ending_cash_balance: float = 0.0
    ending_revenue: NonNegativeFloat = 0.0
    ending_customers: NonNegativeInt = 0
    cumulative_revenue: NonNegativeFloat = 0.0
    cumulative_net_income: float = 0.0
    breakeven_period: PositiveInt | None = None
    minimum_cash_balance: float | None = None


class SimulationOutput(MetricsSchema):
    """Complete output contract returned by a simulation engine."""

    scenario_id: str = Field(min_length=1, max_length=120)
    periods: tuple[SimulationPeriodOutput, ...] = Field(
        min_length=1,
        description="Ordered period-level outputs from a simulation run.",
    )
    summary: SimulationSummary

    @model_validator(mode="after")
    def validate_period_sequence(self) -> "SimulationOutput":
        """Require contiguous one-based period numbering."""

        expected_periods = tuple(range(1, len(self.periods) + 1))
        actual_periods = tuple(period.period for period in self.periods)
        if actual_periods != expected_periods:
            raise ValueError("simulation periods must be contiguous and start at 1")
        return self
