"""Supabase Postgres persistence for user-owned custom company workspaces."""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from analytics.company_ingestion_service import CompanyIngestionError
from analytics.supabase_service import get_authenticated_supabase_client
from models.company_schema import CompanyDataSource, CompanyWorkspace, WorkspaceType


CUSTOM_COMPANIES_TABLE = "custom_companies"


def load_user_custom_workspaces(
    user_id: str,
    *,
    client: Any | None = None,
) -> tuple[CompanyWorkspace, ...]:
    """Load custom workspaces owned by one authenticated Supabase user."""

    supabase = client or get_authenticated_supabase_client()
    response = (
        supabase.table(CUSTOM_COMPANIES_TABLE)
        .select("company_id, workspace_json")
        .eq("user_id", user_id)
        .order("company_name")
        .execute()
    )
    workspaces: list[CompanyWorkspace] = []
    for row in _response_rows(response):
        workspace = workspace_from_jsonb(row["workspace_json"])
        workspaces.append(workspace)
    return tuple(workspaces)


def save_user_custom_workspace(
    user_id: str,
    workspace: CompanyWorkspace,
    *,
    client: Any | None = None,
) -> None:
    """Insert or upsert a user-owned custom workspace row."""

    _validate_custom_workspace(workspace)
    supabase = client or get_authenticated_supabase_client()
    supabase.table(CUSTOM_COMPANIES_TABLE).upsert(
        _workspace_row(user_id, workspace),
        on_conflict="user_id,company_id",
    ).execute()


def update_user_custom_workspace(
    user_id: str,
    workspace: CompanyWorkspace,
    *,
    client: Any | None = None,
) -> None:
    """Update one custom workspace row for the authenticated user."""

    _validate_custom_workspace(workspace)
    supabase = client or get_authenticated_supabase_client()
    row = _workspace_row(user_id, workspace)
    supabase.table(CUSTOM_COMPANIES_TABLE).update(row).eq("user_id", user_id).eq(
        "company_id",
        workspace.company_id,
    ).execute()


def delete_user_custom_workspace(
    user_id: str,
    company_id: str,
    *,
    client: Any | None = None,
) -> None:
    """Delete one custom workspace row for the authenticated user."""

    supabase = client or get_authenticated_supabase_client()
    supabase.table(CUSTOM_COMPANIES_TABLE).delete().eq("user_id", user_id).eq(
        "company_id",
        company_id,
    ).execute()


def import_user_company_workspace_json(
    user_id: str,
    uploaded_json: bytes,
    *,
    existing_workspaces: tuple[CompanyWorkspace, ...] = tuple(),
    client: Any | None = None,
) -> CompanyWorkspace:
    """Validate uploaded workspace JSON and save it to Supabase for one user."""

    try:
        payload = json.loads(uploaded_json.decode("utf-8"))
        workspace = CompanyWorkspace.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CompanyIngestionError("The uploaded file is not valid JSON.") from exc
    except ValidationError as exc:
        raise CompanyIngestionError("The uploaded workspace does not match the expected schema.") from exc
    _reject_duplicate_workspace(workspace, existing_workspaces)
    workspace = workspace.model_copy(
        update={
            "data_source": CompanyDataSource.IMPORTED_FILE,
            "is_sample": False,
            "metadata": workspace.metadata.model_copy(
                update={"workspace_type": WorkspaceType.CUSTOM},
                deep=True,
            )
            if workspace.metadata is not None
            else None,
            "source_path": None,
        },
        deep=True,
    )
    save_user_custom_workspace(user_id, workspace, client=client)
    return workspace


def workspace_to_jsonb(workspace: CompanyWorkspace) -> dict[str, Any]:
    """Return a JSONB-ready payload for a workspace."""

    return json.loads(workspace.model_dump_json())


def workspace_from_jsonb(payload: dict[str, Any] | str) -> CompanyWorkspace:
    """Rebuild a CompanyWorkspace from a Supabase JSONB payload."""

    try:
        raw_payload = json.loads(payload) if isinstance(payload, str) else payload
        workspace = CompanyWorkspace.model_validate(raw_payload)
    except (TypeError, json.JSONDecodeError, ValidationError) as exc:
        raise CompanyIngestionError("Stored custom workspace JSON is invalid.") from exc

    return workspace.model_copy(
        update={
            "data_source": CompanyDataSource.DATABASE,
            "is_sample": False,
            "metadata": workspace.metadata.model_copy(
                update={"workspace_type": WorkspaceType.CUSTOM},
                deep=True,
            )
            if workspace.metadata is not None
            else None,
            "source_path": None,
        },
        deep=True,
    )


def _workspace_row(user_id: str, workspace: CompanyWorkspace) -> dict[str, Any]:
    """Build a Supabase row for a user-owned workspace."""

    return {
        "user_id": user_id,
        "company_id": workspace.company_id,
        "company_name": workspace.company_name,
        "workspace_json": workspace_to_jsonb(workspace),
    }


def _validate_custom_workspace(workspace: CompanyWorkspace) -> None:
    """Ensure only custom workspaces are stored in user-owned Supabase rows."""

    if workspace.is_sample or workspace.metadata.workspace_type != WorkspaceType.CUSTOM:
        raise CompanyIngestionError("Only custom workspaces can be stored for users.")


def _reject_duplicate_workspace(
    workspace: CompanyWorkspace,
    existing_workspaces: tuple[CompanyWorkspace, ...],
) -> None:
    """Reject duplicate imported workspace identity within visible workspaces."""

    normalized_name = workspace.company_name.strip().casefold()
    for existing_workspace in existing_workspaces:
        if existing_workspace.company_id == workspace.company_id:
            raise CompanyIngestionError("A company with this ID already exists.")
        if existing_workspace.company_name.strip().casefold() == normalized_name:
            raise CompanyIngestionError("Company name must be unique across workspaces.")


def _response_rows(response: Any) -> list[dict[str, Any]]:
    """Read rows from a Supabase response or a test fake."""

    data = response.get("data") if isinstance(response, dict) else getattr(response, "data", None)
    if data is None:
        return []
    return list(data)
