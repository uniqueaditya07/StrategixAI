from __future__ import annotations

from analytics.workspace_service import get_selected_company_workspace, load_available_company_workspaces
from models.company_schema import CompanyWorkspace


class CopilotWorkspaceAccessError(Exception):
    """Raised when a verified user cannot access the requested workspace."""


def validate_copilot_workspace_access(uid: str, workspace_id: str) -> CompanyWorkspace:
    """Return the workspace only when it is available to the authenticated user."""

    if not uid:
        raise CopilotWorkspaceAccessError("Authenticated user is required.")

    # Transitional Phase 9 behavior: workspace files are currently local sample/custom
    # records without an owner field. The authenticated Streamlit app treats loaded
    # local workspaces as available after login, so Copilot allows only IDs present
    # in that same catalog until per-user workspace persistence is introduced.
    workspace = get_selected_company_workspace(
        workspace_id,
        load_available_company_workspaces(),
    )
    if workspace is None:
        raise CopilotWorkspaceAccessError("Workspace is not available to this user.")
    return workspace
