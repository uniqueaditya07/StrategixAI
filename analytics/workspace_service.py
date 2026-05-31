"""Workspace orchestration service for StrategixAI Phase 4.

This service adapts local company workspaces into the existing simulation,
dashboard, comparison, and executive-advisor services. It does not duplicate
core simulation behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ai.executive_advisor import ExecutiveAdvisorOutput, generate_executive_advisor
from analytics.company_ingestion_service import (
    CUSTOM_COMPANIES_DIR,
    load_custom_company_workspaces,
)
from analytics.comparison_service import run_scenario_comparison
from analytics.dashboard_service import (
    DashboardPayload,
    SCENARIO_OPTIONS,
    apply_scenario_variant,
    build_cashflow_dataframe,
    build_customer_dataframe,
    build_dashboard_payload,
    build_revenue_dataframe,
    get_latest_kpis,
)
from engine.simulation_engine import run_simulation
from models.business_schema import BusinessAssumptions
from models.company_schema import CompanyWorkspace
from models.comparison_schema import ScenarioComparisonOutput
from models.scenario_schema import (
    BusinessScenario,
    ScenarioRunRequest,
    ScenarioRunResult,
    ScenarioStatus,
    ScenarioType,
    SimulationConfig,
)


SAMPLE_COMPANIES_DIR = Path(__file__).resolve().parents[1] / "data" / "sample_companies"


def load_available_company_workspaces(
    data_dir: Path | None = None,
    custom_data_dir: Path | None = None,
) -> tuple[CompanyWorkspace, ...]:
    """Load and validate sample and custom local company workspace JSON files."""

    source_dir = data_dir or SAMPLE_COMPANIES_DIR
    custom_source_dir = custom_data_dir or CUSTOM_COMPANIES_DIR
    workspaces: list[CompanyWorkspace] = []

    if not source_dir.exists():
        sample_workspaces: tuple[CompanyWorkspace, ...] = tuple()
    else:
        sample_workspaces = _load_company_workspaces_from_dir(source_dir)

    workspaces.extend(sample_workspaces)
    if data_dir is None or custom_data_dir is not None:
        workspaces.extend(load_custom_company_workspaces(custom_source_dir))

    return tuple(workspaces)


def load_sample_company_workspaces(data_dir: Path | None = None) -> tuple[CompanyWorkspace, ...]:
    """Load only bundled sample company workspaces."""

    source_dir = data_dir or SAMPLE_COMPANIES_DIR
    if not source_dir.exists():
        return tuple()
    return _load_company_workspaces_from_dir(source_dir)


def _load_company_workspaces_from_dir(source_dir: Path) -> tuple[CompanyWorkspace, ...]:
    """Load CompanyWorkspace JSON files from one directory."""

    workspaces: list[CompanyWorkspace] = []
    for path in sorted(source_dir.glob("*.json")):
        workspace = CompanyWorkspace.model_validate_json(path.read_text(encoding="utf-8"))
        workspace = workspace.model_copy(update={"source_path": str(path)}, deep=True)
        workspaces.append(workspace)

    return tuple(workspaces)


def get_selected_company_workspace(
    company_id: str | None,
    workspaces: tuple[CompanyWorkspace, ...] | None = None,
) -> CompanyWorkspace | None:
    """Return a selected workspace by id, or the first workspace when omitted."""

    available_workspaces = workspaces or load_available_company_workspaces()
    if not available_workspaces:
        return None
    if company_id is None:
        return available_workspaces[0]

    for workspace in available_workspaces:
        if workspace.company_id == company_id:
            return workspace
    return None


def company_profile_to_assumptions(workspace: CompanyWorkspace) -> BusinessAssumptions:
    """Convert a company profile into existing simulation assumptions."""

    return workspace.profile.assumptions.model_copy(deep=True)


def build_company_base_scenario(
    workspace: CompanyWorkspace,
    *,
    horizon_periods: int = 24,
) -> BusinessScenario:
    """Build a base simulation scenario for a company workspace."""

    profile = workspace.profile
    return BusinessScenario(
        scenario_id=f"{profile.company_id}-base",
        name=f"{profile.company_name} Base Plan",
        scenario_type=ScenarioType.BASE_CASE,
        description=profile.description,
        assumptions=company_profile_to_assumptions(workspace),
        config=SimulationConfig(horizon_periods=horizon_periods),
    )


def build_company_dashboard_payload(
    workspace: CompanyWorkspace | None,
    *,
    scenario_name: str = "Base Case",
    horizon_periods: int = 24,
    fallback_business_model: str = "SaaS Startup",
) -> DashboardPayload:
    """Build dashboard payload for a selected company, with demo fallback."""

    if workspace is None:
        return build_dashboard_payload(
            business_model=fallback_business_model,
            scenario_name=scenario_name,
            horizon_periods=horizon_periods,
        )

    if scenario_name not in SCENARIO_OPTIONS:
        raise ValueError(f"Unsupported scenario: {scenario_name}")

    base_scenario = build_company_base_scenario(workspace, horizon_periods=horizon_periods)
    scenario = apply_scenario_variant(base_scenario, scenario_name)
    result = run_simulation(ScenarioRunRequest(scenario=scenario, persist_results=False))
    output = _require_output(result)
    summary = output.summary
    profile = workspace.profile

    return {
        "scenario": {
            "scenario_id": result.scenario_id,
            "status": result.status.value,
            "business_model": _display_business_model(workspace),
            "scenario_name": scenario_name,
            "horizon_periods": horizon_periods,
            "company_id": profile.company_id,
            "company_name": profile.company_name,
            "workspace_source": workspace.data_source.value,
        },
        "summary_kpis": get_latest_kpis(result),
        "revenue_trend": build_revenue_dataframe(result),
        "customer_trend": build_customer_dataframe(result),
        "cash_trend": build_cashflow_dataframe(result),
        "simulation_summary": {
            "starting_cash_balance": summary.starting_cash_balance,
            "ending_cash_balance": summary.ending_cash_balance,
            "ending_revenue": summary.ending_revenue,
            "ending_customers": summary.ending_customers,
            "cumulative_revenue": summary.cumulative_revenue,
            "cumulative_net_income": summary.cumulative_net_income,
            "minimum_cash_balance": summary.minimum_cash_balance,
        },
        "breakeven_period": summary.breakeven_period,
    }


def build_company_scenario_comparison(
    workspace: CompanyWorkspace | None,
    *,
    horizon_periods: int = 24,
    fallback_business_model: str = "SaaS Startup",
) -> ScenarioComparisonOutput:
    """Build scenario comparison for a company workspace."""

    if workspace is None:
        return run_scenario_comparison(
            business_model=fallback_business_model,
            horizon_periods=horizon_periods,
        )

    return run_scenario_comparison(
        base_scenario=build_company_base_scenario(workspace, horizon_periods=horizon_periods),
        horizon_periods=horizon_periods,
    )


def build_company_executive_advisor_output(
    workspace: CompanyWorkspace | None,
    dashboard_payload: dict[str, Any],
    comparison: ScenarioComparisonOutput,
) -> ExecutiveAdvisorOutput:
    """Build deterministic executive advisor output for a company workspace."""

    del workspace
    return generate_executive_advisor(dashboard_payload, comparison)


def _display_business_model(workspace: CompanyWorkspace) -> str:
    """Return business-readable company model text for existing dashboard payloads."""

    return workspace.profile.business_model.value.replace("_", " ").title()


def _require_output(result: ScenarioRunResult):
    """Return simulation output or raise a clear workspace error."""

    if result.status != ScenarioStatus.COMPLETED or result.output is None:
        message = result.error_message or "Simulation did not return output."
        raise ValueError(f"Cannot build workspace dashboard payload: {message}")
    return result.output
