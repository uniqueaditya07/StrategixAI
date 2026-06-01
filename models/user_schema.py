"""User session schemas for StrategixAI authentication."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


NonEmptyString = Annotated[str, Field(min_length=1)]


class UserSchema(BaseModel):
    """Base schema with strict user validation behavior."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class PublicUser(UserSchema):
    """Session-safe authenticated Supabase user payload."""

    user_id: str = Field(min_length=1)
    name: str = ""
    email: str = Field(min_length=3, max_length=254)
    created_at: datetime | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        """Normalize and validate a basic email address."""

        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("Enter a valid email address.")
        local_part, domain = normalized.rsplit("@", 1)
        if not local_part or "." not in domain:
            raise ValueError("Enter a valid email address.")
        return normalized


class AuthSession(UserSchema):
    """Supabase auth session data held only in Streamlit session_state."""

    user: PublicUser
    access_token: str = Field(min_length=1)
    refresh_token: str = Field(min_length=1)
