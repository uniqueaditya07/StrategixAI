"""Scenario comparison contracts for StrategixAI.

These schemas define structured outputs for comparing deterministic scenario
runs. They contain no simulation logic; comparison execution belongs in the
analytics layer and core simulation remains in engine/.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator


NonNegativeFloat = Annotated[float, Field(ge=0.0)]


class ComparisonSchema(BaseModel):
    """Base schema with strict validation for comparison contracts."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ComparisonScenarioType(StrEnum):
    """Supported deterministic comparison cases for the dashboard."""

    BASE_CASE = "base_case"
    GROWTH_PUSH = "growth_push"
    COST_OPTIMIZATION = "cost_optimization"


class ComparisonMetricDelta(ComparisonSchema):
    """Delta for one metric compared with the baseline scenario."""

    metric_name: str = Field(min_length=1, max_length=120)
    absolute_delta: float
    percentage_delta: float | None = None


class ScenarioComparisonMetrics(ComparisonSchema):
    """Comparable terminal metrics for one deterministic scenario."""

    scenario_id: str = Field(min_length=1, max_length=120)
    scenario_name: str = Field(min_length=1, max_length=160)
    scenario_type: ComparisonScenarioType
    revenue: NonNegativeFloat
    net_income: float
    customers: int = Field(ge=0)
    cash_balance: float
    breakeven_month: int | None = Field(default=None, ge=1)
    ltv_to_cac_ratio: NonNegativeFloat | None = None


class ScenarioComparisonRow(ComparisonSchema):
    """One scenario's metrics plus baseline-relative deltas."""

    metrics: ScenarioComparisonMetrics
    deltas_vs_baseline: tuple[ComparisonMetricDelta, ...] = Field(default_factory=tuple)


class ScenarioComparisonOutput(ComparisonSchema):
    """Structured output returned by the scenario comparison service."""

    baseline_scenario_id: str = Field(min_length=1, max_length=120)
    scenarios: tuple[ScenarioComparisonRow, ...] = Field(min_length=1)
    compared_metrics: tuple[str, ...] = Field(
        default=(
            "revenue",
            "net_income",
            "customers",
            "cash_balance",
            "breakeven_month",
            "ltv_to_cac_ratio",
        )
    )

    @model_validator(mode="after")
    def validate_baseline_present(self) -> "ScenarioComparisonOutput":
        """Require the declared baseline to exist in comparison rows."""

        scenario_ids = {row.metrics.scenario_id for row in self.scenarios}
        if self.baseline_scenario_id not in scenario_ids:
            raise ValueError("baseline_scenario_id must be present in scenarios")
        return self
