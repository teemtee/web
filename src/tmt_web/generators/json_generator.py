import json
from collections.abc import Mapping
from typing import TypedDict

from tmt import Logger, Plan, Test
from tmt.utils import GeneralError


class FmfId(TypedDict):
    """Structure of fmf-id field in JSON output"""
    url: str | None
    path: str | None
    name: str
    ref: str | None


class ObjectData(TypedDict):
    """Common structure for both Test and Plan objects in JSON output"""
    name: str
    summary: str | None
    description: str | None
    url: str | None
    ref: str | None
    contact: list[str]
    tag: list[str]
    tier: str | None
    id: str
    fmf_id: FmfId


class TestAndPlanData(TypedDict):
    """Structure for combined Test and Plan output"""
    test: ObjectData
    plan: ObjectData


def _create_json_data(obj: Test | Plan, logger: Logger) -> Mapping[str, object]:
    """
    Helper function to create the JSON data from a test or plan object.

    :param obj: Test or Plan object to convert
    :param logger: Logger instance for logging
    :return: Dictionary with object data in a standardized format
    """
    logger.debug("Creating JSON data structure")
    full_url = obj.web_link()
    return {
        "name": obj.name,
        "summary": obj.summary,
        "description": obj.description,
        "url": full_url,
        "ref": obj.fmf_id.ref,
        "contact": obj.contact,
        "tag": obj.tag,
        "tier": obj.tier,
        "id": obj.id,
        "fmf-id": {
            "url": obj.fmf_id.url,
            "path": obj.fmf_id.path.as_posix() if obj.fmf_id.path is not None else None,
            "name": obj.fmf_id.name,
            "ref": obj.fmf_id.ref,
        }
    }


def _serialize_json(data: Mapping[str, object], logger: Logger) -> str:
    """
    Helper function to serialize data to JSON with error handling.

    :param data: Data to serialize
    :param logger: Logger instance for logging
    :return: JSON string
    :raises: GeneralError if JSON serialization fails
    """
    try:
        logger.debug("Serializing data to JSON")
        return json.dumps(data)
    except Exception as err:
        logger.fail("Failed to serialize data to JSON")
        raise GeneralError("Failed to generate JSON output") from err


def generate_test_json(test: Test, logger: Logger) -> str:
    """
    Generate JSON data for a test.

    :param test: Test object to convert
    :param logger: Logger instance for logging
    :return: JSON string with test data
    :raises: GeneralError if JSON generation fails
    """
    logger.debug("Generating JSON data for test")
    data = _create_json_data(test, logger)
    result = _serialize_json(data, logger)
    logger.debug("JSON data generated")
    return result


def generate_plan_json(plan: Plan, logger: Logger) -> str:
    """
    Generate JSON data for a plan.

    :param plan: Plan object to convert
    :param logger: Logger instance for logging
    :return: JSON string with plan data
    :raises: GeneralError if JSON generation fails
    """
    logger.debug("Generating JSON data for plan")
    data = _create_json_data(plan, logger)
    result = _serialize_json(data, logger)
    logger.debug("JSON data generated")
    return result


def generate_testplan_json(test: Test, plan: Plan, logger: Logger) -> str:
    """
    Generate JSON data for both test and plan.

    :param test: Test object to convert
    :param plan: Plan object to convert
    :param logger: Logger instance for logging
    :return: JSON string with test and plan data
    :raises: GeneralError if JSON generation fails
    """
    logger.debug("Generating JSON data for test and plan")
    data = {
        "test": _create_json_data(test, logger),
        "plan": _create_json_data(plan, logger),
    }
    result = _serialize_json(data, logger)
    logger.debug("JSON data generated")
    return result
