"""AI advisory schemas for StrategixAI.

These models define structured outputs for executive recommendations, strategic
risk analysis, and AI-generated narrative summaries. They contain contracts only;
prompting and model orchestration belong in the ai/ package.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.metrics_schema import KPISnapshot


Rate = Annotated[float, Field(ge=0.0, le=1.0)]
PositiveInt = Annotated[int, Field(gt=0)]


class AISchema(BaseModel):
    """Base schema with strict validation behavior for AI contracts."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class RecommendationPriority(StrEnum):
    """Executive priority level for a recommendation."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationCategory(StrEnum):
    """Strategic domain addressed by an AI recommendation."""

    PRICING = "pricing"
    GROWTH = "growth"
    RETENTION = "retention"
    COST_CONTROL = "cost_control"
    CASH_RUNWAY = "cash_runway"
    MARKET_POSITIONING = "market_positioning"
    OPERATIONS = "operations"
    FUNDRAISING = "fundraising"


class RiskSeverity(StrEnum):
    """Severity level for a strategic or financial risk."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(StrEnum):
    """Risk taxonomy used by advisory and reporting modules."""

    MARKET = "market"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    COMPETITIVE = "competitive"
    EXECUTION = "execution"
    MODEL_ASSUMPTION = "model_assumption"


class StrategicRecommendation(AISchema):
    """Actionable executive recommendation generated from scenario evidence."""

    title: str = Field(min_length=1, max_length=160)
    category: RecommendationCategory
    priority: RecommendationPriority
    recommendation: str = Field(min_length=1, max_length=1200)
    rationale: str = Field(min_length=1, max_length=1600)
    expected_impact: str = Field(min_length=1, max_length=800)
    implementation_effort: RecommendationPriority = Field(
        description="Relative effort required to execute the recommendation.",
    )
    confidence: Rate = Field(
        description="AI confidence in the recommendation based on available inputs.",
    )
    supporting_metrics: tuple[str, ...] = Field(default_factory=tuple)


class RiskItem(AISchema):
    """Structured risk observation with mitigation guidance."""

    title: str = Field(min_length=1, max_length=160)
    category: RiskCategory
    severity: RiskSeverity
    probability: Rate
    impact: Rate
    description: str = Field(min_length=1, max_length=1200)
    mitigation: str = Field(min_length=1, max_length=1200)
    leading_indicators: tuple[str, ...] = Field(default_factory=tuple)


class RiskAnalysis(AISchema):
    """Portfolio-level risk analysis for a scenario or strategy."""

    overall_risk_score: Rate = Field(
        description="Composite risk score where 1.0 is highest risk.",
    )
    risks: tuple[RiskItem, ...] = Field(default_factory=tuple)
    key_watchouts: tuple[str, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def validate_critical_risk_visibility(self) -> "RiskAnalysis":
        """Require executive watchouts when critical risks are present."""

        has_critical_risk = any(risk.severity == RiskSeverity.CRITICAL for risk in self.risks)
        if has_critical_risk and not self.key_watchouts:
            raise ValueError("critical risks require at least one key_watchout")
        return self


class ExecutiveSummary(AISchema):
    """Concise AI-generated executive narrative for a scenario result."""

    headline: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=2000)
    strategic_context: str = Field(min_length=1, max_length=1600)
    key_takeaways: tuple[str, ...] = Field(min_length=1, max_length=7)
    decision_prompt: str | None = Field(
        default=None,
        max_length=500,
        description="The most important decision leadership should make next.",
    )


class AIRecommendationRequest(AISchema):
    """Input contract for an AI advisor workflow."""

    scenario_id: str = Field(min_length=1, max_length=120)
    objective: str = Field(min_length=1, max_length=500)
    latest_kpis: KPISnapshot
    focus_areas: tuple[RecommendationCategory, ...] = Field(default_factory=tuple)
    max_recommendations: PositiveInt = Field(default=5, le=10)


class AIAdvisorResponse(AISchema):
    """Structured response returned by the future AI advisor module."""

    scenario_id: str = Field(min_length=1, max_length=120)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    executive_summary: ExecutiveSummary
    recommendations: tuple[StrategicRecommendation, ...] = Field(
        min_length=1,
        max_length=10,
    )
    risk_analysis: RiskAnalysis
    model_name: str | None = Field(default=None, max_length=120)
    confidence: Rate = Field(
        description="Overall confidence in the advisory response.",
    )
