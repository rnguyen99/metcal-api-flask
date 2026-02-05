"""Pydantic schemas for request and response payloads."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class TokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", anystr_strip_whitespace=True)

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AssetBase(BaseModel):
    model_config = ConfigDict(extra="forbid", anystr_strip_whitespace=True, from_attributes=True)

    name: str = Field(min_length=1)
    category: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    value: Optional[float] = Field(default=None, ge=0)
    purchase_date: Optional[date] = None
    metadata: Optional[str] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", anystr_strip_whitespace=True)

    name: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    value: Optional[float] = Field(default=None, ge=0)
    purchase_date: Optional[date] = None
    metadata: Optional[str] = None

    @model_validator(mode="after")
    def ensure_payload(cls, values: "AssetUpdate") -> "AssetUpdate":  # type: ignore[name-defined]
        if not any(value is not None for value in values.model_dump().values()):
            raise ValueError("At least one field must be provided for update.")
        return values


class AssetResponse(AssetBase):
    id: int
    created_at: str
    updated_at: Optional[str] = None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    detail: str
    errors: Optional[list[dict]] = None
