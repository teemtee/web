import json

import tmt
from tmt import Test, Logger, Plan


def generate_test_json(test: Test, logger: Logger) -> str:
    """
    This function generates an JSON file with the input data for a test
    :param test: Test object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the JSON file...")
    full_url = test.web_link()
    data = {
        "name": test.name,
        "summary": test.summary,
        "description": test.description,
        "url": full_url,
        "ref": test.fmf_id.ref,
        "contact": test.contact
    }
    data = json.dumps(data)
    logger.print("JSON file generated successfully!", color="green")
    return data


def generate_plan_json(plan: Plan, logger: Logger) -> str:
    """
    This function generates an JSON file with the input data for a plan
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the JSON file...")
    full_url = plan.web_link()
    data = {
        "name": plan.name,
        "summary": plan.summary,
        "description": plan.description,
        "url": full_url,
        "ref": plan.fmf_id.ref
    }
    data = json.dumps(data)
    logger.print("JSON file generated successfully!", color="green")
    return data


def generate_testplan_json(test: tmt.Test, plan: tmt.Plan, logger: Logger) -> str:
    """
    This function generates an JSON file with the input data for a test and a plan
    :param test: Test object
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the JSON file...")
    full_url_test = test.web_link()
    full_url_plan = plan.web_link()
    data = {
        "test": {
            "name": test.name,
            "summary": test.summary,
            "description": test.description,
            "url": full_url_test,
            "ref": test.fmf_id.ref,
            "contact": test.contact
        },
        "plan": {
            "name": plan.name,
            "summary": plan.summary,
            "description": plan.description,
            "url": full_url_plan,
            "ref": plan.fmf_id.ref
        }
    }
    data = json.dumps(data)
    logger.print("JSON file generated successfully!", color="green")
    return data
