"""Data models for tmt-web."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FmfIdData(BaseModel):
    """Raw fmf-id data model."""

    name: str
    url: str | None = None
    path: str | None = None
    ref: str | None = None


class TestData(BaseModel):
    """Raw test data model."""

    name: str
    summary: str | None = None
    description: str | None = None
    contact: list[str] | None = None
    component: list[str] | None = None
    enabled: bool | None = None
    environment: dict[str, Any] | None = None
    duration: str | None = None
    framework: str | None = None
    manual: bool | None = None
    path: str | None = None
    tier: str | None = None
    order: int | None = None
    id: str | None = None
    link: list[dict[str, Any]] | None = None
    tag: list[str] | None = None
    fmf_id: FmfIdData | None = Field(None, alias="fmf-id")
    extra_data: dict[str, Any] | None = None

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both fmf_id and fmf-id
        alias_generator=None,  # Allow both fmf_id and fmf-id
    )


class PlanData(BaseModel):
    """Raw plan data model."""

    name: str
    summary: str | None = None
    description: str | None = None
    prepare: list[dict[str, Any]] | None = None
    execute: list[dict[str, Any]] | None = None
    finish: list[dict[str, Any]] | None = None
    discover: dict[str, Any] | None = None
    provision: dict[str, Any] | None = None
    report: dict[str, Any] | None = None
    enabled: bool | None = None
    path: str | None = None
    order: int | None = None
    id: str | None = None
    link: list[dict[str, Any]] | None = None
    tag: list[str] | None = None
    fmf_id: FmfIdData | None = Field(None, alias="fmf-id")
    extra_data: dict[str, Any] | None = None

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both fmf_id and fmf-id
        alias_generator=None,  # Allow both fmf_id and fmf-id
    )


class TestPlanData(BaseModel):
    """Combined test and plan data model."""

    test: TestData
    plan: PlanData
