"""Scenario schemas for StrategixAI simulation workflows.

Scenario models combine business assumptions, simulation configuration, and
result metadata without implementing engine behavior.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.business_schema import BusinessAssumptions
from models.metrics_schema import SimulationOutput


PositiveInt = Annotated[int, Field(gt=0)]
Rate = Annotated[float, Field(ge=0.0, le=1.0)]


class ScenarioSchema(BaseModel):
    """Base schema with strict validation behavior for scenario contracts."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ScenarioType(StrEnum):
    """Strategic posture represented by a scenario."""

    BASE_CASE = "base_case"
    UPSIDE = "upside"
    DOWNSIDE = "downside"
    AGGRESSIVE_GROWTH = "aggressive_growth"
    CONSERVATIVE = "conservative"
    CUSTOM = "custom"


class SimulationCadence(StrEnum):
    """Time granularity for simulation outputs."""

    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class ScenarioStatus(StrEnum):
    """Lifecycle status for a scenario run."""

    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MonteCarloConfig(ScenarioSchema):
    """Configuration for a future Monte Carlo simulation engine."""

    enabled: bool = False
    iterations: PositiveInt = Field(default=1000, le=100_000)
    confidence_level: Rate = Field(default=0.9)
    random_seed: int | None = Field(default=None)


class SensitivityVariable(ScenarioSchema):
    """A variable range for future sensitivity analysis."""

    name: str = Field(min_length=1, max_length=120)
    base_value: float
    low_value: float
    high_value: float
    description: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_range(self) -> "SensitivityVariable":
        """Ensure sensitivity range surrounds the base value."""

        if self.low_value > self.high_value:
            raise ValueError("low_value must be less than or equal to high_value")
        if not self.low_value <= self.base_value <= self.high_value:
            raise ValueError("base_value must be between low_value and high_value")
        return self


class SimulationConfig(ScenarioSchema):
    """Execution settings shared by deterministic and probabilistic simulations."""

    horizon_periods: PositiveInt = Field(
        default=24,
        le=120,
        description="Number of periods to simulate.",
    )
    cadence: SimulationCadence = SimulationCadence.MONTHLY
    include_tax_effects: bool = False
    include_working_capital: bool = False
    monte_carlo: MonteCarloConfig = Field(default_factory=MonteCarloConfig)
    sensitivity_variables: tuple[SensitivityVariable, ...] = Field(default_factory=tuple)


class BusinessScenario(ScenarioSchema):
    """A complete scenario definition ready for simulation."""

    scenario_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=160)
    scenario_type: ScenarioType = ScenarioType.BASE_CASE
    description: str | None = Field(default=None, max_length=1000)
    assumptions: BusinessAssumptions
    config: SimulationConfig = Field(default_factory=SimulationConfig)
    status: ScenarioStatus = ScenarioStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class ScenarioRunRequest(ScenarioSchema):
    """Request contract consumed by the future simulation engine."""

    scenario: BusinessScenario
    requested_by: str | None = Field(default=None, max_length=120)
    persist_results: bool = True
    return_period_details: bool = True


class ScenarioRunResult(ScenarioSchema):
    """Result envelope returned by simulation workflows."""

    scenario_id: str = Field(min_length=1, max_length=120)
    status: ScenarioStatus
    output: SimulationOutput | None = None
    error_message: str | None = Field(default=None, max_length=1000)
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_result_state(self) -> "ScenarioRunResult":
        """Keep completed and failed result states internally consistent."""

        if self.status == ScenarioStatus.COMPLETED and self.output is None:
            raise ValueError("completed scenario results must include output")
        if self.status == ScenarioStatus.FAILED and not self.error_message:
            raise ValueError("failed scenario results must include error_message")
        return self


class ScenarioComparisonRequest(ScenarioSchema):
    """Request contract for comparing multiple strategic scenarios."""

    baseline_scenario_id: str = Field(min_length=1, max_length=120)
    comparison_scenario_ids: tuple[str, ...] = Field(min_length=1, max_length=10)
    metrics: tuple[str, ...] = Field(
        default=("revenue", "cash_balance", "active_customers", "burn_rate"),
        description="Metric names to compare across scenarios.",
    )

    @model_validator(mode="after")
    def validate_baseline_not_repeated(self) -> "ScenarioComparisonRequest":
        """Prevent comparing a scenario against itself as a peer."""

        if self.baseline_scenario_id in self.comparison_scenario_ids:
            raise ValueError("baseline_scenario_id cannot appear in comparison_scenario_ids")
        return self
