"""Workspace service tests for StrategixAI Phase 4."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.workspace_service import (
    build_company_dashboard_payload,
    build_company_executive_advisor_output,
    build_company_scenario_comparison,
    company_profile_to_assumptions,
    get_selected_company_workspace,
    load_available_company_workspaces,
    load_sample_company_workspaces,
)
from models.company_schema import CompanyProfile, CompanyWorkspace


EXPECTED_COMPANIES = {
    "Northstar SaaS",
    "MarketBridge Marketplace",
    "RetailX D2C",
    "FinEdge FinTech",
    "LearnLoop EdTech",
}


def test_all_sample_companies_load() -> None:
    """All local sample workspaces should load from JSON."""

    workspaces = load_sample_company_workspaces()
    company_names = {workspace.company_name for workspace in workspaces}

    assert len(workspaces) == 5
    assert company_names == EXPECTED_COMPANIES


def test_every_company_has_valid_profile_schema() -> None:
    """Every loaded workspace should carry a validated company profile."""

    for workspace in load_sample_company_workspaces():
        assert isinstance(workspace, CompanyWorkspace)
        assert isinstance(workspace.profile, CompanyProfile)
        assert workspace.company_id
        assert workspace.company_name
        assert company_profile_to_assumptions(workspace).business_name == workspace.company_name


def test_selected_company_workspace_returns_matching_company() -> None:
    """Workspace selection should return the requested company id."""

    workspace = get_selected_company_workspace("finedge-fintech")

    assert workspace is not None
    assert workspace.company_name == "FinEdge FinTech"


def test_every_company_can_produce_dashboard_payload() -> None:
    """Every workspace should produce chart-ready dashboard data."""

    for workspace in load_sample_company_workspaces():
        payload = build_company_dashboard_payload(
            workspace,
            scenario_name="Base Case",
            horizon_periods=24,
        )

        assert payload["scenario"]["company_id"] == workspace.company_id
        assert payload["scenario"]["company_name"] == workspace.company_name
        assert payload["summary_kpis"]["revenue"] > 0
        assert len(payload["revenue_trend"]) == 24
        assert len(payload["customer_trend"]) == 24
        assert len(payload["cash_trend"]) == 24


def test_every_company_can_run_scenario_comparison() -> None:
    """Every workspace should support the existing three-scenario comparison."""

    for workspace in load_sample_company_workspaces():
        comparison = build_company_scenario_comparison(
            workspace,
            horizon_periods=24,
        )

        assert comparison.baseline_scenario_id == f"{workspace.company_id}-base-base-case"
        assert len(comparison.scenarios) == 3
        assert {row.metrics.scenario_name for row in comparison.scenarios} == {
            "Base Case",
            "Growth Push",
            "Cost Optimization",
        }


def test_every_company_can_generate_executive_advisor_output() -> None:
    """Every workspace should produce deterministic executive advisor output."""

    for workspace in load_sample_company_workspaces():
        payload = build_company_dashboard_payload(
            workspace,
            scenario_name="Base Case",
            horizon_periods=24,
        )
        comparison = build_company_scenario_comparison(
            workspace,
            horizon_periods=24,
        )
        advisor = build_company_executive_advisor_output(workspace, payload, comparison)

        assert advisor.headline
        assert advisor.primary_recommendation
        assert advisor.advisor_response.model_name == "deterministic-executive-advisor-v1"


def test_workspace_fallback_preserves_demo_payload() -> None:
    """Missing workspace context should fall back to the existing demo behavior."""

    payload = build_company_dashboard_payload(
        None,
        scenario_name="Base Case",
        horizon_periods=24,
        fallback_business_model="SaaS Startup",
    )
    comparison = build_company_scenario_comparison(
        None,
        horizon_periods=24,
        fallback_business_model="SaaS Startup",
    )

    assert payload["scenario"]["business_model"] == "SaaS Startup"
    assert comparison.baseline_scenario_id == "saas-startup-base-case"


def main() -> None:
    """Run workspace tests without requiring pytest."""

    test_all_sample_companies_load()
    test_every_company_has_valid_profile_schema()
    test_selected_company_workspace_returns_matching_company()
    test_every_company_can_produce_dashboard_payload()
    test_every_company_can_run_scenario_comparison()
    test_every_company_can_generate_executive_advisor_output()
    test_workspace_fallback_preserves_demo_payload()
    print("Workspace service tests passed")


if __name__ == "__main__":
    main()
