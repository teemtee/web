import json
from typing import Any

import tmt.utils
from tmt import Plan, Test


def _create_json_data(obj: Test | Plan, logger: tmt.Logger) -> dict[str, Any]:
    """
    Helper function to create the JSON data from a test or plan object
    """
    logger.print("Generating the JSON file...")
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


def generate_test_json(test: tmt.Test, logger: tmt.Logger) -> str:
    """
    This function generates an JSON file with the input data for a test
    :param test: Test object
    :param logger: tmt.Logger instance
    :return:
    """
    data = _create_json_data(test, logger)
    return json.dumps(data)


def generate_plan_json(plan: tmt.Plan, logger: tmt.Logger) -> str:
    """
    This function generates an JSON file with the input data for a plan
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    data = _create_json_data(plan, logger)
    return json.dumps(data)


def generate_testplan_json(test: tmt.Test, plan: tmt.Plan, logger: tmt.Logger) -> str:
    """
    This function generates an JSON file with the input data for a test and a plan
    :param test: Test object
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the JSON file...")
    data = {
        "test": _create_json_data(test, logger),
        "plan": _create_json_data(plan, logger),
    }
    return json.dumps(data)
