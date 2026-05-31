"""Company ingestion tests for StrategixAI Phase 5 V1."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.executive_advisor import ExecutiveAdvisorOutput
from analytics.company_ingestion_service import (
    CompanyIngestionError,
    ManualCompanyInput,
    build_updated_custom_company_workspace,
    build_custom_company_workspace,
    delete_custom_company_workspace,
    import_company_workspace_json,
    load_custom_company_workspaces,
    save_custom_company_workspace,
    update_custom_company_workspace,
)
from analytics.workspace_service import (
    SAMPLE_COMPANIES_DIR,
    build_company_dashboard_payload,
    build_company_executive_advisor_output,
    build_company_scenario_comparison,
    load_available_company_workspaces,
    load_sample_company_workspaces,
)
from models.company_schema import CompanyBusinessModel, CompanyIndustry, CompanyStage, WorkspaceType
from models.comparison_schema import ScenarioComparisonOutput


def valid_manual_input(company_name: str = "Acme Strategy Cloud") -> ManualCompanyInput:
    """Build a valid manual input fixture."""

    return ManualCompanyInput(
        company_name=company_name,
        industry=CompanyIndustry.SAAS,
        business_model=CompanyBusinessModel.SUBSCRIPTION,
        company_stage=CompanyStage.EARLY_STAGE,
        country="United States",
        currency="USD",
        description="Custom B2B SaaS workspace for ingestion tests.",
        starting_customers=120,
        monthly_price_arpu=129.0,
        monthly_churn_rate=0.025,
        cac=520.0,
        marketing_spend=16000.0,
        fixed_monthly_costs=62000.0,
        variable_cost_pct=0.2,
        starting_cash_balance=300000.0,
        forecast_horizon=24,
    )


def test_valid_custom_company_can_be_created() -> None:
    """Valid manual assumptions should produce a CompanyWorkspace."""

    workspace = build_custom_company_workspace(valid_manual_input())

    assert workspace.company_id == "acme-strategy-cloud"
    assert workspace.company_name == "Acme Strategy Cloud"
    assert workspace.is_sample is False
    assert workspace.metadata.workspace_type == WorkspaceType.CUSTOM
    assert workspace.metadata.workspace_name == "Acme Strategy Cloud"
    assert workspace.profile.assumptions.starting_customers == 120


def test_invalid_assumptions_are_rejected() -> None:
    """Invalid manual assumptions should fail before persistence."""

    try:
        ManualCompanyInput(
            **(valid_manual_input().model_dump() | {"starting_customers": 0})
        )
    except ValidationError:
        return
    raise AssertionError("Invalid starting customers should be rejected")


def test_empty_company_name_is_rejected() -> None:
    """Workspace names must not be empty."""

    try:
        ManualCompanyInput(**(valid_manual_input().model_dump() | {"company_name": ""}))
    except ValidationError:
        return
    raise AssertionError("Empty company name should be rejected")


def test_invalid_forecast_horizon_is_rejected() -> None:
    """Forecast horizons must stay inside the supported validation range."""

    try:
        ManualCompanyInput(**(valid_manual_input().model_dump() | {"forecast_horizon": 0}))
    except ValidationError:
        return
    raise AssertionError("Invalid forecast horizon should be rejected")


def test_duplicate_company_names_are_rejected() -> None:
    """Custom company names must be unique across existing workspaces."""

    existing = load_sample_company_workspaces()
    try:
        build_custom_company_workspace(
            valid_manual_input("Northstar SaaS"),
            existing,
        )
    except CompanyIngestionError:
        return
    raise AssertionError("Duplicate sample company name should be rejected")


def test_custom_company_json_can_be_saved(tmp_path: Path) -> None:
    """A custom workspace should save as a JSON file."""

    workspace = build_custom_company_workspace(valid_manual_input())
    saved_path = save_custom_company_workspace(workspace, custom_dir=tmp_path)

    assert saved_path.exists()
    assert saved_path.name == "acme-strategy-cloud.json"


def test_custom_company_json_can_be_loaded(tmp_path: Path) -> None:
    """Saved custom JSON should load back into a validated workspace."""

    workspace = build_custom_company_workspace(valid_manual_input())
    save_custom_company_workspace(workspace, custom_dir=tmp_path)

    loaded = load_custom_company_workspaces(tmp_path)

    assert len(loaded) == 1
    assert loaded[0].company_name == workspace.company_name


def test_custom_company_json_can_be_updated(tmp_path: Path) -> None:
    """Edited custom workspace values should persist to local JSON."""

    workspace = build_custom_company_workspace(valid_manual_input())
    save_custom_company_workspace(workspace, custom_dir=tmp_path)
    loaded = load_custom_company_workspaces(tmp_path)[0]
    updated_input = valid_manual_input("Acme Strategy Cloud Prime")
    updated_input.starting_customers = 240
    updated_input.monthly_price_arpu = 149.0

    updated = build_updated_custom_company_workspace(loaded, updated_input, (loaded,))
    update_custom_company_workspace(updated, custom_dir=tmp_path)
    reloaded = load_custom_company_workspaces(tmp_path)[0]

    assert reloaded.company_id == loaded.company_id
    assert reloaded.company_name == "Acme Strategy Cloud Prime"
    assert reloaded.profile.assumptions.starting_customers == 240
    assert reloaded.profile.assumptions.pricing.base_monthly_price == 149.0
    assert reloaded.metadata.updated_at >= reloaded.metadata.created_at


def test_duplicate_workspace_name_is_rejected_on_update() -> None:
    """Edited custom workspace names must remain unique across workspaces."""

    existing = load_sample_company_workspaces()
    workspace = build_custom_company_workspace(valid_manual_input())
    updated_input = valid_manual_input("Northstar SaaS")

    try:
        build_updated_custom_company_workspace(
            workspace,
            updated_input,
            existing + (workspace,),
        )
    except CompanyIngestionError:
        return
    raise AssertionError("Duplicate workspace name should be rejected on update")


def test_custom_company_json_can_be_deleted(tmp_path: Path) -> None:
    """Deleting a custom workspace should remove its persisted JSON file."""

    workspace = build_custom_company_workspace(valid_manual_input())
    save_custom_company_workspace(workspace, custom_dir=tmp_path)
    loaded = load_custom_company_workspaces(tmp_path)[0]

    deleted_path = delete_custom_company_workspace(loaded, custom_dir=tmp_path)

    assert not deleted_path.exists()
    assert load_custom_company_workspaces(tmp_path) == tuple()


def test_sample_company_delete_is_rejected() -> None:
    """Sample workspaces are protected from deletion."""

    sample = load_sample_company_workspaces()[0]
    try:
        delete_custom_company_workspace(sample)
    except CompanyIngestionError:
        return
    raise AssertionError("Sample workspace deletion should be rejected")


def test_imported_json_is_validated(tmp_path: Path) -> None:
    """Imported workspace JSON should validate and persist."""

    workspace = build_custom_company_workspace(valid_manual_input())
    imported, saved_path = import_company_workspace_json(
        workspace.model_dump_json(),
        custom_dir=tmp_path,
    )

    assert imported.company_id == workspace.company_id
    assert saved_path.exists()


def test_invalid_imported_json_is_rejected(tmp_path: Path) -> None:
    """Malformed or schema-invalid JSON imports should fail cleanly."""

    try:
        import_company_workspace_json(
            '{"profile": {"company_name": ""}}',
            custom_dir=tmp_path,
        )
    except CompanyIngestionError:
        return
    raise AssertionError("Invalid imported JSON should be rejected")


def test_custom_company_appears_in_workspace_loading(tmp_path: Path) -> None:
    """Workspace loading should include saved custom companies."""

    workspace = build_custom_company_workspace(valid_manual_input())
    save_custom_company_workspace(workspace, custom_dir=tmp_path)

    workspaces = load_available_company_workspaces(
        data_dir=SAMPLE_COMPANIES_DIR,
        custom_data_dir=tmp_path,
    )
    company_names = {loaded.company_name for loaded in workspaces}

    assert "Acme Strategy Cloud" in company_names
    assert "Northstar SaaS" in company_names


def test_custom_company_can_generate_dashboard_payload() -> None:
    """Custom workspaces should generate the standard dashboard payload."""

    workspace = build_custom_company_workspace(valid_manual_input())
    payload = build_company_dashboard_payload(
        workspace,
        scenario_name="Base Case",
        horizon_periods=24,
    )

    assert payload["scenario"]["company_id"] == workspace.company_id
    assert payload["summary_kpis"]["revenue"] > 0


def test_custom_company_can_generate_scenario_comparison() -> None:
    """Custom workspaces should support scenario comparison."""

    workspace = build_custom_company_workspace(valid_manual_input())
    comparison = build_company_scenario_comparison(workspace, horizon_periods=24)

    assert isinstance(comparison, ScenarioComparisonOutput)
    assert len(comparison.scenarios) == 3


def test_custom_company_can_generate_executive_advisor_output() -> None:
    """Custom workspaces should support executive advisor output."""

    workspace = build_custom_company_workspace(valid_manual_input())
    payload = build_company_dashboard_payload(
        workspace,
        scenario_name="Base Case",
        horizon_periods=24,
    )
    comparison = build_company_scenario_comparison(workspace, horizon_periods=24)
    advisor = build_company_executive_advisor_output(workspace, payload, comparison)

    assert isinstance(advisor, ExecutiveAdvisorOutput)
    assert advisor.headline


def main() -> None:
    """Run company ingestion tests without requiring pytest."""

    import tempfile

    test_valid_custom_company_can_be_created()
    test_invalid_assumptions_are_rejected()
    test_empty_company_name_is_rejected()
    test_invalid_forecast_horizon_is_rejected()
    test_duplicate_company_names_are_rejected()
    with tempfile.TemporaryDirectory() as path:
        test_custom_company_json_can_be_saved(Path(path))
    with tempfile.TemporaryDirectory() as path:
        test_custom_company_json_can_be_loaded(Path(path))
    with tempfile.TemporaryDirectory() as path:
        test_custom_company_json_can_be_updated(Path(path))
    test_duplicate_workspace_name_is_rejected_on_update()
    with tempfile.TemporaryDirectory() as path:
        test_custom_company_json_can_be_deleted(Path(path))
    test_sample_company_delete_is_rejected()
    with tempfile.TemporaryDirectory() as path:
        test_imported_json_is_validated(Path(path))
    with tempfile.TemporaryDirectory() as path:
        test_invalid_imported_json_is_rejected(Path(path))
    with tempfile.TemporaryDirectory() as path:
        test_custom_company_appears_in_workspace_loading(Path(path))
    test_custom_company_can_generate_dashboard_payload()
    test_custom_company_can_generate_scenario_comparison()
    test_custom_company_can_generate_executive_advisor_output()
    print("Company ingestion tests passed")


if __name__ == "__main__":
    main()
