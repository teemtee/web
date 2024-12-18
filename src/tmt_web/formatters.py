"""Formatters for converting data models to various output formats."""

import json

from tmt import Logger
from tmt.utils import dict_to_yaml

from tmt_web.generators import html_generator
from tmt_web.models import PlanData, TestData, TestPlanData


def _format_json(data: TestData | PlanData | TestPlanData) -> str:
    """Format data model as JSON string."""
    return data.model_dump_json(by_alias=True)


def _format_yaml(data: TestData | PlanData | TestPlanData) -> str:
    """Format data model as YAML string."""
    # First convert to dict with proper aliases
    data_dict = data.model_dump(by_alias=True)
    # Then use tmt's yaml formatter

    return dict_to_yaml(data_dict)


def _format_html(data: TestData | PlanData | TestPlanData, logger: Logger) -> str:
    """Format data model as HTML string."""
    if isinstance(data, TestPlanData):
        return html_generator.generate_testplan_html_page(data.test, data.plan, logger=logger)
    if isinstance(data, TestData):
        return html_generator.generate_html_page(data, logger=logger)
    return html_generator.generate_html_page(data, logger=logger)


def format_data(data: TestData | PlanData | TestPlanData, out_format: str, logger: Logger) -> str:
    """Format data model in the specified output format."""
    match out_format:
        case "html":
            return _format_html(data, logger)
        case "json":
            return _format_json(data)
        case "yaml":
            return _format_yaml(data)
        case _:
            logger.fail(f"Unsupported output format: {out_format}")
            raise ValueError(f"Unsupported output format: {out_format}")


def serialize_data(data: TestData | PlanData | TestPlanData) -> str:
    """Serialize data model to JSON string for storage."""
    return data.model_dump_json(by_alias=True)


def deserialize_data(data_str: str) -> TestData | PlanData | TestPlanData:
    """Deserialize JSON string back to appropriate data model."""
    data = json.loads(data_str)
    if "test" in data and "plan" in data:
        return TestPlanData.model_validate(data)
    if "framework" in data:  # Unique to TestData
        return TestData.model_validate(data)
    return PlanData.model_validate(data)
