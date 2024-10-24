import tmt
from tmt import Logger

from tmt_web.generators.json_generator import _create_json_data


def print_success(logger: Logger) -> None:
    logger.print("YAML file generated successfully!", color="green")


def generate_test_yaml(test: tmt.Test, logger: Logger) -> str:
    """
    This function generates an YAML file with the input data for a test.

    :param test: Test object
    :param logger: tmt.Logger instance
    :return: YAML data for a given test
    """
    yaml_data = tmt.utils.dict_to_yaml(_create_json_data(test, logger))
    print_success(logger)
    return yaml_data


def generate_plan_yaml(plan: tmt.Plan, logger: Logger) -> str:
    """
    This function generates an YAML file with the input data for a plan.

    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return: YAML data for a given plan.
    """
    yaml_data = tmt.utils.dict_to_yaml(_create_json_data(plan, logger))
    print_success(logger)
    return yaml_data


def generate_testplan_yaml(test: tmt.Test, plan: tmt.Plan, logger: Logger) -> str:
    """
    This function generates an YAML file with the input data for a test and a plan.

    :param test: Test object
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return: YAML data for a given test and plan
    """
    data = {
        "test": _create_json_data(test, logger),
        "plan": _create_json_data(plan, logger),
    }
    yaml_data = tmt.utils.dict_to_yaml(data)
    print_success(logger)
    return yaml_data
