"""Company workspace schemas for StrategixAI.

These models define the local tenant/workspace contract used by Phase 4.
They validate company identity, profile context, and the assumptions that feed
the existing deterministic simulation engine.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from models.business_schema import BusinessAssumptions


NonEmptyString = Annotated[str, Field(min_length=1)]


class CompanySchema(BaseModel):
    """Base schema with strict workspace validation behavior."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class CompanyStage(StrEnum):
    """Lifecycle stage used for company workspace context."""

    IDEA = "idea"
    PRE_REVENUE = "pre_revenue"
    EARLY_STAGE = "early_stage"
    GROWTH = "growth"
    SCALE_UP = "scale_up"
    MATURE = "mature"


class CompanyIndustry(StrEnum):
    """Business-readable industry group for workspace segmentation."""

    SAAS = "saas"
    MARKETPLACE = "marketplace"
    RETAIL = "retail"
    FINTECH = "fintech"
    EDTECH = "edtech"


class CompanyBusinessModel(StrEnum):
    """Primary commercial model for a company workspace."""

    SUBSCRIPTION = "subscription"
    MARKETPLACE = "marketplace"
    D2C_COMMERCE = "d2c_commerce"
    FINTECH_PRODUCT = "fintech_product"
    EDTECH_PLATFORM = "edtech_platform"
    HYBRID = "hybrid"


class CompanyDataSource(StrEnum):
    """Source type for workspace assumptions."""

    LOCAL_SAMPLE = "local_sample"
    LOCAL_CUSTOM = "local_custom"
    IMPORTED_FILE = "imported_file"
    DATABASE = "database"


class CompanyProfile(CompanySchema):
    """Company identity and operating assumptions for one workspace."""

    company_id: str = Field(min_length=3, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")
    company_name: str = Field(min_length=1, max_length=160)
    industry: CompanyIndustry
    business_model: CompanyBusinessModel
    company_stage: CompanyStage
    country: str = Field(min_length=2, max_length=80)
    currency: str = Field(min_length=3, max_length=3)
    description: str = Field(min_length=1, max_length=800)
    default_forecast_horizon: int = Field(default=24, gt=0, le=120)
    assumptions: BusinessAssumptions
    created_at: datetime
    updated_at: datetime

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize currency codes for display and downstream assumptions."""

        return value.upper()

    @model_validator(mode="after")
    def validate_profile_alignment(self) -> "CompanyProfile":
        """Ensure profile metadata stays aligned with simulation assumptions."""

        if self.assumptions.business_name != self.company_name:
            raise ValueError("assumptions.business_name must match company_name")
        if self.assumptions.pricing.currency != self.currency:
            raise ValueError("assumptions.pricing.currency must match company currency")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be earlier than created_at")
        return self


class CompanyWorkspace(CompanySchema):
    """A loadable company workspace with profile and source metadata."""

    profile: CompanyProfile
    data_source: CompanyDataSource = CompanyDataSource.LOCAL_SAMPLE
    source_path: str | None = Field(default=None, max_length=500)
    is_sample: bool = True

    @property
    def company_id(self) -> str:
        """Return the workspace company id."""

        return self.profile.company_id

    @property
    def company_name(self) -> str:
        """Return the workspace display name."""

        return self.profile.company_name
