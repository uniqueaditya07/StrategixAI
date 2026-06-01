"""Executive report schemas for StrategixAI.

These contracts describe exportable executive reports built from existing
dashboard, simulation, and strategic intelligence outputs.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportSchema(BaseModel):
    """Base schema with strict validation for report exports."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class ReportFormat(StrEnum):
    """Supported executive report export formats."""

    JSON = "json"
    PDF = "pdf"


class ReportMetadata(ReportSchema):
    """Metadata for exported executive reports."""

    report_id: str = Field(min_length=1, max_length=160)
    report_title: str = Field(min_length=1, max_length=180)
    generated_at: datetime
    scenario_id: str = Field(min_length=1, max_length=120)
    scenario_name: str = Field(min_length=1, max_length=160)
    horizon_periods: int = Field(gt=0)
    export_formats: tuple[ReportFormat, ...] = Field(default=(ReportFormat.JSON, ReportFormat.PDF))


class CompanyReportInfo(ReportSchema):
    """Company and scenario context included in the report."""

    company_name: str = Field(min_length=1, max_length=180)
    company_id: str | None = Field(default=None, max_length=120)
    business_model: str = Field(min_length=1, max_length=160)
    scenario_name: str = Field(min_length=1, max_length=160)
    horizon_periods: int = Field(gt=0)
    workspace_source: str | None = Field(default=None, max_length=120)


class KPIReportSnapshot(ReportSchema):
    """Latest-period KPI snapshot for executive reporting."""

    period: str
    revenue: float
    annual_recurring_revenue: float
    net_income: float
    cash_balance: float
    runway_months: float | None = None
    active_customers: int
    logo_churn_rate: float
    net_revenue_retention: float
    blended_cac: float
    ltv_to_cac_ratio: float | None = None


class ExecutiveReport(ReportSchema):
    """Complete exportable executive report."""

    metadata: ReportMetadata
    company: CompanyReportInfo
    kpi_snapshot: KPIReportSnapshot
    business_health_score: int = Field(ge=0, le=100)
    health_classification: str = Field(min_length=1, max_length=80)
    strategic_signals: tuple[dict[str, Any], ...]
    risk_radar: tuple[dict[str, Any], ...]
    recommended_actions: tuple[dict[str, Any], ...]
    executive_verdict: str = Field(min_length=1)
    scenario_winner_analysis: dict[str, Any] | None = None
    simulation_summary: dict[str, Any] = Field(default_factory=dict)
    scenario_comparison_summary: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    key_findings: tuple[str, ...] = Field(default_factory=tuple)
    top_risks: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    strategic_recommendation: dict[str, Any] | None = None
    revenue_trend: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    cash_trend: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
    customer_trend: tuple[dict[str, Any], ...] = Field(default_factory=tuple)
