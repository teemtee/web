from typing import Any

import tmt
from tmt import Logger
from tmt.utils import GeneralError, dict_to_yaml

from tmt_web.generators.json_generator import ObjectModel, TestAndPlanModel


def _serialize_yaml(data: dict[str, Any], logger: Logger) -> str:
    """
    Helper function to serialize data to YAML with error handling.

    :param data: Data to serialize
    :param logger: Logger instance for logging
    :return: YAML string
    :raises: GeneralError if YAML serialization fails
    """
    try:
        logger.debug("Serializing data to YAML")
        yaml_data = dict_to_yaml(data)
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
    data = ObjectModel.from_tmt_object(test).model_dump(by_alias=True)
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
    data = ObjectModel.from_tmt_object(plan).model_dump(by_alias=True)
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
    data = TestAndPlanModel.from_tmt_objects(test, plan).model_dump(by_alias=True)
    return _serialize_yaml(data, logger)
