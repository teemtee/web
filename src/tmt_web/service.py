import logging
import os

import tmt
from celery.app import Celery  # type: ignore[attr-defined]
from tmt.utils import Path  # type: ignore[attr-defined]

from tmt_web.generators import html_generator
from tmt_web.generators import json_generator, yaml_generator
from tmt_web.utils import git_handler

logger = tmt.Logger(logging.getLogger("tmt-logger"))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

app = Celery(__name__, broker=redis_url, backend=redis_url)


def get_tree(url: str, name: str, ref: str | None, tree_path: str) -> tmt.base.Tree:
    """
    This function clones the repository and returns the Tree object.

    :param ref: Object ref
    :param name: Object name
    :param url: Object url
    :param tree_path: Object path
    :return:
    """
    logger.print(f"Cloning the repository for url: {url}")
    logger.print("Parsing the url and name...")
    logger.print(f"URL: {url}")
    logger.print(f"Name: {name}")

    path = git_handler.get_git_repository(url, logger, ref)

    if tree_path is not None:
        tree_path += '/'
        # If path is set, construct a path to the tmt Tree
        if path.suffix == '.git':
            path = path.with_suffix('')
        path = Path(path.as_posix() + tree_path)

    logger.print("Looking for tree...")
    tree = tmt.base.Tree(path=path, logger=logger)
    logger.print("Tree found!", color="green")
    return tree


def process_test_request(test_url: str,
                         test_name: str,
                         test_ref: str,
                         test_path: str,
                         return_object: bool,
                         out_format: str) -> str | tmt.Test | None:
    """
    This function processes the request for a test and returns the HTML file or the Test object.

    :param test_url: Test url
    :param test_name: Test name
    :param test_ref: Test repo ref
    :param test_path: Test path
    :param return_object: Specify if the function should return the HTML file or the Test object
    :param out_format: Specifies output format
    :return:
    """

    tree = get_tree(test_url, test_name, test_ref, test_path)

    logger.print("Looking for the wanted test...")

    # Find the desired Test object
    wanted_test = tree.tests(names=[test_name])[0]
    if not wanted_test:
        logger.print("Test not found!", color="red")
        return None

    logger.print("Test found!", color="green")
    if not return_object:
        return wanted_test
    match out_format:
        case "html":
            return html_generator.generate_html_page(wanted_test, logger=logger)
        case "json":
            return json_generator.generate_test_json(wanted_test, logger=logger)
        case "yaml":
            return yaml_generator.generate_test_yaml(wanted_test, logger=logger)
    return None


def process_plan_request(plan_url: str,
                         plan_name: str,
                         plan_ref: str,
                         plan_path: str,
                         return_object: bool,
                         out_format: str) -> str | None | tmt.Plan:
    """
    This function processes the request for a plan and returns the HTML file or the Plan object.

    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref
    :param plan_path: Plan path
    :param return_object: Specify if the function should return the HTML file or the Plan object
    :param out_format: Specifies output format
    :return:
    """

    tree = get_tree(plan_url, plan_name, plan_ref, plan_path)

    logger.print("Looking for the wanted plan...")

    # Find the desired Plan object
    wanted_plan = tree.plans(names=[plan_name])[0]
    if not wanted_plan:
        logger.print("Plan not found!", color="red")
        return None
    logger.print("Plan found!", color="green")
    if not return_object:
        return wanted_plan
    match out_format:
        case "html":
            return html_generator.generate_html_page(wanted_plan, logger=logger)
        case "json":
            return json_generator.generate_plan_json(wanted_plan,  logger=logger)
        case "yaml":
            return yaml_generator.generate_plan_yaml(wanted_plan, logger=logger)
    return None


def process_testplan_request(test_url,
                             test_name,
                             test_ref,
                             test_path,
                             plan_url,
                             plan_name,
                             plan_ref,
                             plan_path,
                             out_format) -> str | None:
    """
    This function processes the request for a test and a plan and returns the HTML file.

    :param test_url: Test URL
    :param test_name: Test name
    :param test_ref: Test repo ref
    :param test_path: Test path
    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref
    :param plan_path: Plan path
    :param out_format: Specifies output format
    :return:
    """
    test = process_test_request(test_url, test_name, test_ref, test_path, False, out_format)
    if not isinstance(test, tmt.Test):
        logger.print("Invalid test object", color="red")
        return None
    plan = process_plan_request(plan_url, plan_name, plan_ref, plan_path, False, out_format)
    if not isinstance(plan, tmt.Plan):
        logger.print("Invalid plan object", color="red")
        return None
    match out_format:
        case "html":
            return html_generator.generate_testplan_html_page(test, plan, logger=logger)
        case "json":
            return json_generator.generate_testplan_json(test, plan, logger=logger)
        case "yaml":
            return yaml_generator.generate_testplan_yaml(test, plan, logger=logger)

    return None


@app.task
def main(test_url: str | None,
         test_name: str | None,
         test_ref: str | None,
         test_path: str | None,
         plan_url: str | None,
         plan_name: str | None,
         plan_ref: str | None,
         plan_path: str | None,
         out_format: str) -> str | tmt.Test | tmt.Plan | None:
    logger.print("Starting...", color="blue")
    # TODO
    if test_name is not None and plan_name is None:
        return process_test_request(test_url, test_name, test_ref, test_path, True, out_format)  # type: ignore [arg-type]
    if plan_name is not None and test_name is None:
        return process_plan_request(plan_url, plan_name, plan_ref, plan_path, True, out_format)  # type: ignore [arg-type]
    if plan_name is not None and test_name is not None:
        return process_testplan_request(test_url, test_name, test_ref, test_path,
                                        plan_url, plan_name, plan_ref, plan_path, out_format)
    return None


if __name__ == "__main__":
    print("This is not executable file!")
