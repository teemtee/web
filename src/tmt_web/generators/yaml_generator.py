from typing import Any

from tmt import Logger, Plan, Test
from tmt.utils import GeneralError, dict_to_yaml

from tmt_web.generators.json_generator import CombinedTestPlanModel, ObjectModel


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
        return dict_to_yaml(data)
    except Exception as err:
        logger.fail("Failed to serialize data to YAML")
        raise GeneralError("Failed to generate YAML output") from err


def generate_test_yaml(test: Test, logger: Logger) -> str:
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


def generate_plan_yaml(plan: Plan, logger: Logger) -> str:
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


def generate_testplan_yaml(test: Test, plan: Plan, logger: Logger) -> str:
    """
    Generate YAML data for both test and plan.

    :param test: Test object to convert
    :param plan: Plan object to convert
    :param logger: Logger instance for logging
    :return: YAML string with test and plan data
    :raises: GeneralError if YAML generation fails
    """
    logger.debug("Generating YAML data for test and plan")
    data = CombinedTestPlanModel.from_tmt_objects(test, plan).model_dump(by_alias=True)
    return _serialize_yaml(data, logger)
