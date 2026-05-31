"""Custom company ingestion service for StrategixAI Phase 5 V1.

This module validates manual company assumptions and imported JSON workspaces,
then persists them as local CompanyWorkspace JSON files. It deliberately keeps
creation, validation, and file IO outside the Streamlit app.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from models.business_schema import (
    BusinessAssumptions,
    BusinessStage,
    ChannelAssumption,
    ChurnAssumptions,
    CostStructure,
    MarketingChannel,
    MarketingStrategy,
    PricingModel,
    PricingStrategy,
    RevenueModel,
)
from models.company_schema import (
    CompanyBusinessModel,
    CompanyDataSource,
    CompanyIndustry,
    CompanyProfile,
    CompanyStage,
    CompanyWorkspace,
    WorkspaceMetadata,
    WorkspaceType,
)


CUSTOM_COMPANIES_DIR = Path(__file__).resolve().parents[1] / "data" / "custom_companies"


class CompanyIngestionError(ValueError):
    """Friendly validation or persistence error for custom company ingestion."""


class ManualCompanyInput(BaseModel):
    """Validated manual company creation input from Streamlit or tests."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    company_name: str = Field(min_length=1, max_length=160)
    industry: CompanyIndustry
    business_model: CompanyBusinessModel
    company_stage: CompanyStage
    country: str = Field(min_length=2, max_length=80)
    currency: str = Field(min_length=3, max_length=3)
    description: str = Field(min_length=1, max_length=800)
    starting_customers: int = Field(gt=0)
    monthly_price_arpu: float = Field(gt=0.0)
    monthly_churn_rate: float = Field(ge=0.0, le=1.0)
    cac: float = Field(gt=0.0)
    marketing_spend: float = Field(ge=0.0)
    fixed_monthly_costs: float = Field(ge=0.0)
    variable_cost_pct: float = Field(ge=0.0, le=1.0)
    starting_cash_balance: float = Field(ge=0.0)
    forecast_horizon: int = Field(gt=0, le=120)

    @model_validator(mode="after")
    def normalize_currency(self) -> "ManualCompanyInput":
        """Normalize currency once before building nested assumptions."""

        self.currency = self.currency.upper()
        return self


def build_custom_company_workspace(
    manual_input: ManualCompanyInput,
    existing_workspaces: tuple[CompanyWorkspace, ...] = tuple(),
) -> CompanyWorkspace:
    """Build a validated custom workspace from manual company assumptions."""

    company_id = generate_company_id(manual_input.company_name)
    _validate_unique_workspace(
        company_id=company_id,
        company_name=manual_input.company_name,
        existing_workspaces=existing_workspaces,
    )

    timestamp = datetime.utcnow()
    assumptions = _manual_input_to_assumptions(manual_input)
    profile = CompanyProfile(
        company_id=company_id,
        company_name=manual_input.company_name,
        industry=manual_input.industry,
        business_model=manual_input.business_model,
        company_stage=manual_input.company_stage,
        country=manual_input.country,
        currency=manual_input.currency,
        description=manual_input.description,
        default_forecast_horizon=manual_input.forecast_horizon,
        assumptions=assumptions,
        created_at=timestamp,
        updated_at=timestamp,
    )
    return CompanyWorkspace(
        profile=profile,
        metadata=WorkspaceMetadata(
            workspace_id=company_id,
            workspace_name=manual_input.company_name,
            workspace_type=WorkspaceType.CUSTOM,
            industry=manual_input.industry,
            business_model=manual_input.business_model,
            created_at=timestamp,
            updated_at=timestamp,
        ),
        data_source=CompanyDataSource.LOCAL_CUSTOM,
        source_path=None,
        is_sample=False,
    )


def build_updated_custom_company_workspace(
    workspace: CompanyWorkspace,
    manual_input: ManualCompanyInput,
    existing_workspaces: tuple[CompanyWorkspace, ...] = tuple(),
) -> CompanyWorkspace:
    """Build an edited custom workspace while preserving identity and creation metadata."""

    if workspace.is_sample or workspace.metadata.workspace_type != WorkspaceType.CUSTOM:
        raise CompanyIngestionError("Only custom workspaces can be edited.")

    _validate_unique_workspace(
        company_id=workspace.company_id,
        company_name=manual_input.company_name,
        existing_workspaces=existing_workspaces,
        current_company_id=workspace.company_id,
    )

    updated_at = datetime.utcnow()
    assumptions = _manual_input_to_assumptions(manual_input)
    profile = CompanyProfile(
        company_id=workspace.company_id,
        company_name=manual_input.company_name,
        industry=manual_input.industry,
        business_model=manual_input.business_model,
        company_stage=manual_input.company_stage,
        country=manual_input.country,
        currency=manual_input.currency,
        description=manual_input.description,
        default_forecast_horizon=manual_input.forecast_horizon,
        assumptions=assumptions,
        created_at=workspace.profile.created_at,
        updated_at=updated_at,
    )
    return CompanyWorkspace(
        profile=profile,
        metadata=WorkspaceMetadata(
            workspace_id=workspace.company_id,
            workspace_name=manual_input.company_name,
            workspace_type=WorkspaceType.CUSTOM,
            industry=manual_input.industry,
            business_model=manual_input.business_model,
            created_at=workspace.metadata.created_at,
            updated_at=updated_at,
        ),
        data_source=workspace.data_source,
        source_path=workspace.source_path,
        is_sample=False,
    )


def save_custom_company_workspace(
    workspace: CompanyWorkspace,
    *,
    custom_dir: Path | None = None,
    existing_workspaces: tuple[CompanyWorkspace, ...] = tuple(),
) -> Path:
    """Persist a custom company workspace without overwriting existing files."""

    if workspace.is_sample:
        raise CompanyIngestionError("Sample workspaces cannot be saved as custom companies.")

    _validate_unique_workspace(
        company_id=workspace.company_id,
        company_name=workspace.company_name,
        existing_workspaces=existing_workspaces,
    )
    target_dir = custom_dir or CUSTOM_COMPANIES_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{workspace.company_id}.json"
    if target_path.exists():
        raise CompanyIngestionError("A custom company with this ID already exists.")

    saved_workspace = workspace.model_copy(
        update={"source_path": str(target_path)},
        deep=True,
    )
    target_path.write_text(
        saved_workspace.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return target_path


def update_custom_company_workspace(
    workspace: CompanyWorkspace,
    *,
    custom_dir: Path | None = None,
) -> Path:
    """Overwrite an existing custom workspace JSON file."""

    if workspace.is_sample or workspace.metadata.workspace_type != WorkspaceType.CUSTOM:
        raise CompanyIngestionError("Only custom workspaces can be updated.")

    target_dir = custom_dir or CUSTOM_COMPANIES_DIR
    target_path = Path(workspace.source_path) if workspace.source_path else target_dir / f"{workspace.company_id}.json"
    target_dir.mkdir(parents=True, exist_ok=True)
    if not target_path.exists():
        raise CompanyIngestionError("Custom workspace file could not be found.")
    if target_path.parent.resolve() != target_dir.resolve():
        raise CompanyIngestionError("Custom workspace path is outside the local workspace store.")

    saved_workspace = workspace.model_copy(
        update={"source_path": str(target_path)},
        deep=True,
    )
    target_path.write_text(
        saved_workspace.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return target_path


def delete_custom_company_workspace(
    workspace: CompanyWorkspace,
    *,
    custom_dir: Path | None = None,
) -> Path:
    """Delete a custom workspace JSON file from local storage."""

    if workspace.is_sample or workspace.metadata.workspace_type != WorkspaceType.CUSTOM:
        raise CompanyIngestionError("Demo and sample workspaces cannot be deleted.")

    target_dir = custom_dir or CUSTOM_COMPANIES_DIR
    target_path = Path(workspace.source_path) if workspace.source_path else target_dir / f"{workspace.company_id}.json"
    if target_path.parent.resolve() != target_dir.resolve():
        raise CompanyIngestionError("Custom workspace path is outside the local workspace store.")
    if not target_path.exists():
        raise CompanyIngestionError("Custom workspace file could not be found.")

    target_path.unlink()
    return target_path


def load_custom_company_workspaces(custom_dir: Path | None = None) -> tuple[CompanyWorkspace, ...]:
    """Load validated custom company workspaces from local JSON files."""

    source_dir = custom_dir or CUSTOM_COMPANIES_DIR
    if not source_dir.exists():
        return tuple()

    workspaces: list[CompanyWorkspace] = []
    for path in sorted(source_dir.glob("*.json")):
        workspace = CompanyWorkspace.model_validate_json(path.read_text(encoding="utf-8"))
        workspaces.append(workspace.model_copy(update={"source_path": str(path)}, deep=True))
    return tuple(workspaces)


def import_company_workspace_json(
    raw_json: str | bytes,
    *,
    custom_dir: Path | None = None,
    existing_workspaces: tuple[CompanyWorkspace, ...] = tuple(),
) -> tuple[CompanyWorkspace, Path]:
    """Validate and persist an uploaded CompanyWorkspace JSON document."""

    try:
        raw_text = raw_json.decode("utf-8") if isinstance(raw_json, bytes) else raw_json
        payload = json.loads(raw_text)
        workspace = CompanyWorkspace.model_validate(payload)
    except json.JSONDecodeError as exc:
        raise CompanyIngestionError("The uploaded file is not valid JSON.") from exc
    except ValidationError as exc:
        raise CompanyIngestionError(_format_validation_error(exc)) from exc

    workspace = workspace.model_copy(
        update={
            "data_source": CompanyDataSource.IMPORTED_FILE,
            "is_sample": False,
            "metadata": workspace.metadata.model_copy(
                update={"workspace_type": WorkspaceType.CUSTOM},
                deep=True,
            ),
            "source_path": None,
        },
        deep=True,
    )
    saved_path = save_custom_company_workspace(
        workspace,
        custom_dir=custom_dir,
        existing_workspaces=existing_workspaces,
    )
    return workspace, saved_path


def generate_company_id(company_name: str) -> str:
    """Generate a safe, stable slug from a company name."""

    slug = re.sub(r"[^a-z0-9]+", "-", company_name.strip().lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) < 3:
        raise CompanyIngestionError("Company name must produce at least a 3-character ID.")
    return slug[:80].rstrip("-")


def _validate_unique_workspace(
    *,
    company_id: str,
    company_name: str,
    existing_workspaces: tuple[CompanyWorkspace, ...],
    current_company_id: str | None = None,
) -> None:
    """Reject duplicate company names or IDs across known workspaces."""

    normalized_name = company_name.strip().casefold()
    for workspace in existing_workspaces:
        if current_company_id is not None and workspace.company_id == current_company_id:
            continue
        if workspace.company_id == company_id:
            raise CompanyIngestionError("A company with this ID already exists.")
        if workspace.company_name.strip().casefold() == normalized_name:
            raise CompanyIngestionError("Company name must be unique across workspaces.")


def _manual_input_to_assumptions(manual_input: ManualCompanyInput) -> BusinessAssumptions:
    """Convert validated manual input into reusable simulation assumptions."""

    return BusinessAssumptions(
        business_name=manual_input.company_name,
        stage=BusinessStage(manual_input.company_stage.value),
        revenue_model=_revenue_model_for_company(manual_input.business_model),
        starting_cash_balance=manual_input.starting_cash_balance,
        starting_customers=manual_input.starting_customers,
        target_monthly_growth_rate=0.08,
        pricing=PricingStrategy(
            model=PricingModel.FLAT_RATE,
            currency=manual_input.currency,
            base_monthly_price=manual_input.monthly_price_arpu,
            expected_expansion_rate=0.0,
        ),
        marketing=MarketingStrategy(
            channels=(
                ChannelAssumption(
                    channel=MarketingChannel.PAID_SEARCH,
                    monthly_budget=manual_input.marketing_spend,
                    cost_per_acquisition=manual_input.cac,
                    conversion_rate=0.05,
                    monthly_budget_growth_rate=0.0,
                ),
            ),
            organic_monthly_leads=0,
            organic_conversion_rate=0.0,
            referral_rate=0.0,
        ),
        churn=ChurnAssumptions(
            monthly_logo_churn_rate=manual_input.monthly_churn_rate,
            monthly_revenue_churn_rate=manual_input.monthly_churn_rate,
            reactivation_rate=0.0,
            churn_improvement_rate=0.0,
        ),
        costs=CostStructure(
            monthly_fixed_costs=manual_input.fixed_monthly_costs,
            variable_cost_per_customer=manual_input.monthly_price_arpu
            * manual_input.variable_cost_pct,
            gross_margin=1.0 - manual_input.variable_cost_pct,
            headcount_growth_rate=0.0,
        ),
    )


def _revenue_model_for_company(business_model: CompanyBusinessModel) -> RevenueModel:
    """Map company workspace models into existing simulation revenue models."""

    mapping = {
        CompanyBusinessModel.SUBSCRIPTION: RevenueModel.SUBSCRIPTION,
        CompanyBusinessModel.MARKETPLACE: RevenueModel.MARKETPLACE,
        CompanyBusinessModel.D2C_COMMERCE: RevenueModel.ONE_TIME_SALE,
        CompanyBusinessModel.FINTECH_PRODUCT: RevenueModel.SUBSCRIPTION,
        CompanyBusinessModel.EDTECH_PLATFORM: RevenueModel.SUBSCRIPTION,
        CompanyBusinessModel.HYBRID: RevenueModel.HYBRID,
    }
    return mapping[business_model]


def _format_validation_error(exc: ValidationError) -> str:
    """Convert Pydantic details into a compact user-facing message."""

    first_error = exc.errors()[0]
    location = " > ".join(str(part) for part in first_error.get("loc", ()))
    message = first_error.get("msg", "Validation failed")
    if location:
        return f"{location}: {message}"
    return message
