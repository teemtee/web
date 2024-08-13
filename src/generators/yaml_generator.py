import tmt
from tmt import Logger


def generate_test_yaml(test: tmt.Test, logger: Logger) -> str:
    """
    This function generates an YAML file with the input data for a test
    :param test: Test object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the YAML file...")
    full_url = test.web_link()
    data = {
        "name": test.name,
        "summary": test.summary,
        "description": test.description,
        "url": full_url,
        "ref": test.fmf_id.ref,
        "contact": test.contact,
        "tag": test.tag,
        "tier": test.tier,
        "id": test.id,
        "fmf-id": {
            "url": test.fmf_id.url,
            "path": test.fmf_id.path.as_posix() if test.fmf_id.path is not None else None,
            "name": test.fmf_id.name,
            "ref": test.fmf_id.ref,
        }
    }
    data = tmt.utils.dict_to_yaml(data)
    logger.print("YAML file generated successfully!", color="green")
    return data


def generate_plan_yaml(plan: tmt.Plan, logger: Logger) -> str:
    """
    This function generates an YAML file with the input data for a plan
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the YAML file...")
    full_url = plan.web_link()
    data = {
        "name": plan.name,
        "summary": plan.summary,
        "description": plan.description,
        "url": full_url,
        "ref": plan.fmf_id.ref,
        "contact": plan.contact,
        "tag": plan.tag,
        "tier": plan.tier,
        "id": plan.id,
        "fmf-id": {
            "url": plan.fmf_id.url,
            "path": plan.fmf_id.path.as_posix() if plan.fmf_id.path is not None else None,
            "name": plan.fmf_id.name,
            "ref": plan.fmf_id.ref,
        }
    }
    data = tmt.utils.dict_to_yaml(data)
    logger.print("YAML file generated successfully!", color="green")
    return data


def generate_testplan_yaml(test: tmt.Test, plan: tmt.Plan, logger: Logger) -> str:
    """
    This function generates an YAML file with the input data for a test and a plan
    :param test: Test object
    :param plan: Plan object
    :param logger: tmt.Logger instance
    :return:
    """
    logger.print("Generating the YAML file...")
    full_url_test = test.web_link()
    full_url_plan = plan.web_link()
    data = {
        "test": {
            "name": test.name,
            "summary": test.summary,
            "description": test.description,
            "url": full_url_test,
            "ref": test.fmf_id.ref,
            "contact": test.contact,
            "tag": test.tag,
            "tier": test.tier,
            "id": test.id,
            "fmf-id": {
                "url": test.fmf_id.url,
                "path": test.fmf_id.path.as_posix() if test.fmf_id.path is not None else None,
                "name": test.fmf_id.name,
                "ref": test.fmf_id.ref,
            }
        },
        "plan": {
            "name": plan.name,
            "summary": plan.summary,
            "description": plan.description,
            "url": full_url_plan,
            "ref": plan.fmf_id.ref,
            "contact": plan.contact,
            "tag": plan.tag,
            "tier": plan.tier,
            "id": plan.id,
            "fmf-id": {
                "url": plan.fmf_id.url,
                "path": plan.fmf_id.path.as_posix() if plan.fmf_id.path is not None else None,
                "name": plan.fmf_id.name,
                "ref": plan.fmf_id.ref,
            }
        }
    }
    data = tmt.utils.dict_to_yaml(data)
    logger.print("YAML file generated successfully!", color="green")
    return data
