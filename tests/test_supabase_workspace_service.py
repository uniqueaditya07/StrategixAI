"""Supabase custom workspace persistence tests for StrategixAI Phase 8."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.company_ingestion_service import (
    ManualCompanyInput,
    build_custom_company_workspace,
    build_updated_custom_company_workspace,
)
from analytics.supabase_workspace_service import (
    delete_user_custom_workspace,
    load_user_custom_workspaces,
    save_user_custom_workspace,
    update_user_custom_workspace,
    workspace_from_jsonb,
    workspace_to_jsonb,
)
from analytics.workspace_service import load_sample_company_workspaces
from models.company_schema import CompanyBusinessModel, CompanyIndustry, CompanyStage


USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


class FakeSupabaseClient:
    """In-memory fake for the Supabase table query chain used by the service."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def table(self, table_name: str) -> "FakeTableQuery":
        assert table_name == "custom_companies"
        return FakeTableQuery(self.rows)


class FakeTableQuery:
    """Tiny fluent query fake for select/upsert/update/delete."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.filters: dict[str, Any] = {}
        self.operation = "select"
        self.payload: dict[str, Any] | None = None

    def select(self, *_columns: str) -> "FakeTableQuery":
        self.operation = "select"
        return self

    def upsert(self, payload: dict[str, Any], **_kwargs: Any) -> "FakeTableQuery":
        self.operation = "upsert"
        self.payload = payload
        return self

    def update(self, payload: dict[str, Any]) -> "FakeTableQuery":
        self.operation = "update"
        self.payload = payload
        return self

    def delete(self) -> "FakeTableQuery":
        self.operation = "delete"
        return self

    def eq(self, column: str, value: Any) -> "FakeTableQuery":
        self.filters[column] = value
        return self

    def order(self, *_args: Any, **_kwargs: Any) -> "FakeTableQuery":
        return self

    def execute(self) -> dict[str, Any]:
        if self.operation == "upsert":
            assert self.payload is not None
            self.rows[:] = [
                row
                for row in self.rows
                if not (
                    row["user_id"] == self.payload["user_id"]
                    and row["company_id"] == self.payload["company_id"]
                )
            ]
            self.rows.append(self.payload)
            return {"data": [self.payload]}
        if self.operation == "update":
            assert self.payload is not None
            for index, row in enumerate(self.rows):
                if self._matches(row):
                    self.rows[index] = row | self.payload
            return {"data": [row for row in self.rows if self._matches(row)]}
        if self.operation == "delete":
            deleted = [row for row in self.rows if self._matches(row)]
            self.rows[:] = [row for row in self.rows if not self._matches(row)]
            return {"data": deleted}
        return {"data": [row for row in self.rows if self._matches(row)]}

    def _matches(self, row: dict[str, Any]) -> bool:
        return all(row.get(column) == value for column, value in self.filters.items())


def valid_manual_input(company_name: str) -> ManualCompanyInput:
    """Build a valid manual custom company input."""

    return ManualCompanyInput(
        company_name=company_name,
        industry=CompanyIndustry.SAAS,
        business_model=CompanyBusinessModel.SUBSCRIPTION,
        company_stage=CompanyStage.EARLY_STAGE,
        country="United States",
        currency="USD",
        description="Custom B2B SaaS workspace for Supabase persistence tests.",
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


def test_custom_workspace_rows_are_filtered_by_user_id() -> None:
    """Loading user custom workspaces should query only that user's rows."""

    client = FakeSupabaseClient()
    workspace_a = build_custom_company_workspace(valid_manual_input("User A Strategy Cloud"))
    workspace_b = build_custom_company_workspace(valid_manual_input("User B Strategy Cloud"))
    save_user_custom_workspace(USER_A, workspace_a, client=client)
    save_user_custom_workspace(USER_B, workspace_b, client=client)

    loaded_names = {
        workspace.company_name
        for workspace in load_user_custom_workspaces(USER_A, client=client)
    }

    assert loaded_names == {"User A Strategy Cloud"}


def test_user_a_cannot_load_user_b_custom_workspace() -> None:
    """A user's custom workspace list should not include another user's rows."""

    client = FakeSupabaseClient()
    save_user_custom_workspace(
        USER_B,
        build_custom_company_workspace(valid_manual_input("Private B Company")),
        client=client,
    )

    assert load_user_custom_workspaces(USER_A, client=client) == tuple()


def test_demo_companies_remain_available_globally() -> None:
    """Bundled sample companies should still load without a Supabase user."""

    company_names = {workspace.company_name for workspace in load_sample_company_workspaces()}

    assert "Northstar SaaS" in company_names
    assert len(company_names) == 5


def test_workspace_json_roundtrip() -> None:
    """CompanyWorkspace payloads should survive JSONB conversion."""

    workspace = build_custom_company_workspace(valid_manual_input("Roundtrip Cloud"))
    payload = workspace_to_jsonb(workspace)
    restored = workspace_from_jsonb(payload)

    assert restored.company_id == workspace.company_id
    assert restored.company_name == workspace.company_name
    assert restored.is_sample is False


def test_update_and_delete_are_scoped_to_user_id() -> None:
    """Update and delete calls should affect only the matching user's row."""

    client = FakeSupabaseClient()
    workspace_a = build_custom_company_workspace(valid_manual_input("Scoped Company"))
    workspace_b = build_custom_company_workspace(valid_manual_input("Scoped Company B"))
    save_user_custom_workspace(USER_A, workspace_a, client=client)
    save_user_custom_workspace(USER_B, workspace_b, client=client)

    updated = build_updated_custom_company_workspace(
        workspace_a,
        valid_manual_input("Scoped Company Prime"),
        (workspace_a, workspace_b),
    )
    update_user_custom_workspace(USER_A, updated, client=client)
    delete_user_custom_workspace(USER_A, updated.company_id, client=client)

    assert load_user_custom_workspaces(USER_A, client=client) == tuple()
    assert len(load_user_custom_workspaces(USER_B, client=client)) == 1


def main() -> None:
    """Run Supabase workspace tests without requiring pytest."""

    test_custom_workspace_rows_are_filtered_by_user_id()
    test_user_a_cannot_load_user_b_custom_workspace()
    test_demo_companies_remain_available_globally()
    test_workspace_json_roundtrip()
    test_update_and_delete_are_scoped_to_user_id()
    print("Supabase workspace service tests passed")


if __name__ == "__main__":
    main()
