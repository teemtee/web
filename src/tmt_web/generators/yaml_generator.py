from collections.abc import Mapping
from typing import Any, cast

import tmt
from tmt import Logger
from tmt.utils import GeneralError, dict_to_yaml

from tmt_web.generators.json_generator import _create_json_data


def _serialize_yaml(data: Mapping[str, Any], logger: Logger) -> str:
    """
    Helper function to serialize data to YAML with error handling.

    :param data: Data to serialize
    :param logger: Logger instance for logging
    :return: YAML string
    :raises: GeneralError if YAML serialization fails
    """
    try:
        logger.debug("Serializing data to YAML")
        # Cast Mapping to dict since dict_to_yaml expects a dict.
        # This is safe because we know the data comes from _create_json_data
        # which always returns a dict, even though its return type is the more
        # generic Mapping for better type variance.
        yaml_data = dict_to_yaml(cast(dict[str, Any], data))
        logger.debug("YAML data generated")
        return yaml_data
    except Exception as err:
        logger.fail("Failed to serialize data to YAML")
        raise GeneralError("Failed to generate YAML output") from err


def generate_test_yaml(test: tmt.Test, logger: Logger) -> str:
    """
    Generate YAML data for a test.

    :param test: Test object to convert
    :param logger: Logger instance for logging
    :return: YAML string with test data
    :raises: GeneralError if YAML generation fails
    """
    logger.debug("Generating YAML data for test")
    data = _create_json_data(test, logger)
    return _serialize_yaml(data, logger)


def generate_plan_yaml(plan: tmt.Plan, logger: Logger) -> str:
    """
    Generate YAML data for a plan.

    :param plan: Plan object to convert
    :param logger: Logger instance for logging
    :return: YAML string with plan data
    :raises: GeneralError if YAML generation fails
    """
    logger.debug("Generating YAML data for plan")
    data = _create_json_data(plan, logger)
    return _serialize_yaml(data, logger)


def generate_testplan_yaml(test: tmt.Test, plan: tmt.Plan, logger: Logger) -> str:
    """
    Generate YAML data for both test and plan.

    :param test: Test object to convert
    :param plan: Plan object to convert
    :param logger: Logger instance for logging
    :return: YAML string with test and plan data
    :raises: GeneralError if YAML generation fails
    """
    logger.debug("Generating YAML data for test and plan")
    data = {
        "test": _create_json_data(test, logger),
        "plan": _create_json_data(plan, logger),
    }
    return _serialize_yaml(data, logger)
