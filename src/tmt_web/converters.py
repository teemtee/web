"""Converters for tmt objects to data models."""

from typing import Any

from tmt import Plan, Test

from tmt_web.models import FmfIdData, PlanData, TestData, TestPlanData


def _convert_field_value(field: str, value: Any) -> Any:
    """Convert field value to the correct type."""
    if field == "contact":
        # Convert string to list if needed
        if isinstance(value, str):
            return [value]
        return value
    if field == "tier":
        # Convert tier to string
        return str(value) if value is not None else None
    if field == "execute":
        # Convert single dict to list
        if isinstance(value, dict):
            return [value]
        return value
    if field == "discover":
        # Convert list to dict if needed
        if isinstance(value, list) and value:
            return value[0]
        return value
    return value


def _convert_fmf_id(obj: Test | Plan) -> FmfIdData | None:
    """Convert tmt fmf_id to FmfIdData."""
    if not hasattr(obj, "fmf_id"):
        return None

    return FmfIdData(
        name=obj.fmf_id.name,
        url=obj.web_link(),
        path=str(obj.fmf_id.path) if obj.fmf_id.path is not None else None,
        ref=obj.fmf_id.ref,
    )


def test_to_model(test: Test) -> TestData:
    """Convert a tmt.Test object to TestData model."""
    # Get all raw data
    raw_data = test.node.get()

    # Extract known fields
    known_fields = {
        "name",
        "summary",
        "description",
        "contact",
        "component",
        "enabled",
        "environment",
        "duration",
        "framework",
        "manual",
        "path",
        "tier",
        "order",
        "id",
        "link",
        "tag",
    }

    # Build model data with only explicitly set fields
    model_data: dict[str, Any] = {"name": test.name}
    for field in known_fields - {"name"}:
        if field in raw_data:
            model_data[field] = _convert_field_value(field, raw_data[field])

    # Add fmf_id if available
    fmf_id = _convert_fmf_id(test)
    if fmf_id:
        model_data["fmf_id"] = fmf_id

    # Store any additional fields in extra_data
    extra_data = {k: v for k, v in raw_data.items() if k not in known_fields}
    if extra_data:
        model_data["extra_data"] = extra_data

    return TestData(**model_data)


def plan_to_model(plan: Plan) -> PlanData:
    """Convert a tmt.Plan object to PlanData model."""
    # Get all raw data
    raw_data = plan.node.get()

    # Extract known fields
    known_fields = {
        "name",
        "summary",
        "description",
        "prepare",
        "execute",
        "finish",
        "discover",
        "provision",
        "report",
        "enabled",
        "path",
        "order",
        "id",
        "link",
        "tag",
    }

    # Build model data with only explicitly set fields
    model_data: dict[str, Any] = {"name": plan.name}
    for field in known_fields - {"name"}:
        if field in raw_data:
            model_data[field] = _convert_field_value(field, raw_data[field])

    # Add fmf_id if available
    fmf_id = _convert_fmf_id(plan)
    if fmf_id:
        model_data["fmf_id"] = fmf_id

    # Store any additional fields in extra_data
    extra_data = {k: v for k, v in raw_data.items() if k not in known_fields}
    if extra_data:
        model_data["extra_data"] = extra_data

    return PlanData(**model_data)


def create_testplan_data(test: Test, plan: Plan) -> TestPlanData:
    """Create a TestPlanData model from Test and Plan objects."""
    return TestPlanData(
        test=test_to_model(test),
        plan=plan_to_model(plan),
    )
