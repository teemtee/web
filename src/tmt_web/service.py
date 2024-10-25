import logging

import tmt
from celery.app import Celery  # type: ignore[attr-defined]
from tmt.utils import GeneralError, GitUrlError, Path  # type: ignore[attr-defined]

from tmt_web import settings
from tmt_web.generators import html_generator, json_generator, yaml_generator
from tmt_web.utils import git_handler

# Create main logger for the application
logger = tmt.Logger(logging.getLogger("tmt-web"))


app = Celery(__name__, broker=settings.REDIS_URL, backend=settings.REDIS_URL)


def get_tree(url: str, name: str, ref: str | None, tree_path: str | None) -> tmt.base.Tree:
    """
    This function clones the repository and returns the Tree object.

    :param ref: Object ref
    :param name: Object name
    :param url: Object url
    :param tree_path: Object path
    :return: returns a Tree object
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if git operations or tree lookup fails
    """
    logger.debug(f"Processing repository URL: {url}")
    logger.debug(f"Name: {name}")
    logger.debug(f"Ref: {ref}")

    try:
        path = git_handler.get_git_repository(url, logger, ref)
    except GitUrlError as err:
        raise GitUrlError(f"Invalid repository URL: {err}") from err
    except Exception as exc:
        raise GeneralError(f"Failed to clone repository: {exc}") from exc

    if tree_path is not None:
        tree_path += '/'
        # If path is set, construct a path to the tmt Tree
        if path.suffix == '.git':
            path = path.with_suffix('')
        path = Path(path.as_posix() + tree_path)

    logger.debug(f"Looking for tree in {path}")
    tree = tmt.base.Tree(path=path, logger=logger)
    logger.debug("Tree found")
    return tree


def process_test_request(
    test_url: str,
    test_name: str,
    test_ref: str | None = None,
    test_path: str | None = None,
    return_object: bool = True,
    out_format: str = "json"
) -> str | tmt.Test:
    """
    This function processes the request for a test and returns the data in specified output format
    or the Test object.

    :param test_url: Test url
    :param test_name: Test name
    :param test_ref: Test repo ref (optional)
    :param test_path: Test path (optional)
    :param return_object: Specify if the function should return the HTML file or the Test object
    :param out_format: Specifies output format
    :return: the data in specified output format or the Test object
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if test not found or format not supported
    """
    tree = get_tree(test_url, test_name, test_ref, test_path)
    logger.debug(f"Looking for test: {test_name}")

    # Find the desired Test object
    tests = tree.tests(names=[test_name])
    if not tests:
        logger.fail(f"Test '{test_name}' not found")
        raise GeneralError(f"Test '{test_name}' not found")

    wanted_test = tests[0]
    logger.debug("Test found")

    if not return_object:
        return wanted_test

    logger.debug(f"Generating {out_format} output")
    match out_format:
        case "html":
            return html_generator.generate_html_page(wanted_test, logger=logger)
        case "json":
            return json_generator.generate_test_json(wanted_test, logger=logger)
        case "yaml":
            return yaml_generator.generate_test_yaml(wanted_test, logger=logger)
        case _:
            logger.fail(f"Unsupported output format: {out_format}")
            raise GeneralError(f"Unsupported output format: {out_format}")


def process_plan_request(
    plan_url: str,
    plan_name: str,
    plan_ref: str | None = None,
    plan_path: str | None = None,
    return_object: bool = True,
    out_format: str = "json"
) -> str | tmt.Plan:
    """
    This function processes the request for a plan and returns the data in specified output format
    or the Plan object.

    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref (optional)
    :param plan_path: Plan path (optional)
    :param return_object: Specify if the function should return the HTML file or the Plan object
    :param out_format: Specifies output format
    :return: the data in specified output format or the Plan object
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if plan not found or format not supported
    """
    tree = get_tree(plan_url, plan_name, plan_ref, plan_path)
    logger.debug(f"Looking for plan: {plan_name}")

    # Find the desired Plan object
    plans = tree.plans(names=[plan_name])
    if not plans:
        logger.fail(f"Plan '{plan_name}' not found")
        raise GeneralError(f"Plan '{plan_name}' not found")

    wanted_plan = plans[0]
    logger.debug("Plan found")

    if not return_object:
        return wanted_plan

    logger.debug(f"Generating {out_format} output")
    match out_format:
        case "html":
            return html_generator.generate_html_page(wanted_plan, logger=logger)
        case "json":
            return json_generator.generate_plan_json(wanted_plan, logger=logger)
        case "yaml":
            return yaml_generator.generate_plan_yaml(wanted_plan, logger=logger)
        case _:
            logger.fail(f"Unsupported output format: {out_format}")
            raise GeneralError(f"Unsupported output format: {out_format}")


def process_testplan_request(
    test_url: str,
    test_name: str,
    test_ref: str | None,
    test_path: str | None,
    plan_url: str,
    plan_name: str,
    plan_ref: str | None,
    plan_path: str | None,
    out_format: str
) -> str:
    """
    This function processes the request for a test and
    a plan and returns the data in a specified format.

    :param test_url: Test URL
    :param test_name: Test name
    :param test_ref: Test repo ref (optional)
    :param test_path: Test path (optional)
    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref (optional)
    :param plan_path: Plan path (optional)
    :param out_format: Specifies output format
    :return: page data in specified output format
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if test/plan not found or format not supported
    """
    test = process_test_request(test_url, test_name, test_ref, test_path, False, out_format)
    if not isinstance(test, tmt.Test):
        logger.fail("Invalid test object")
        raise GeneralError("Invalid test object")

    plan = process_plan_request(plan_url, plan_name, plan_ref, plan_path, False, out_format)
    if not isinstance(plan, tmt.Plan):
        logger.fail("Invalid plan object")
        raise GeneralError("Invalid plan object")

    logger.debug(f"Generating {out_format} output")
    match out_format:
        case "html":
            return html_generator.generate_testplan_html_page(test, plan, logger=logger)
        case "json":
            return json_generator.generate_testplan_json(test, plan, logger=logger)
        case "yaml":
            return yaml_generator.generate_testplan_yaml(test, plan, logger=logger)
        case _:
            logger.fail(f"Unsupported output format: {out_format}")
            raise GeneralError(f"Unsupported output format: {out_format}")


@app.task
def main(
    test_url: str | None,
    test_name: str | None,
    test_ref: str | None,
    test_path: str | None,
    plan_url: str | None,
    plan_name: str | None,
    plan_ref: str | None,
    plan_path: str | None,
    out_format: str
) -> str | tmt.Test | tmt.Plan:
    """
    Main entry point for processing requests.

    :raises: GeneralError for invalid argument combinations
    """
    logger.debug("Starting request processing")
    logger.debug("Validating input parameters")

    if test_name is not None and plan_name is None:
        if test_url is None:
            logger.fail("Missing required test parameters")
            raise GeneralError("Missing required test parameters")
        return process_test_request(test_url, test_name, test_ref, test_path, True, out_format)

    if plan_name is not None and test_name is None:
        if plan_url is None:
            logger.fail("Missing required plan parameters")
            raise GeneralError("Missing required plan parameters")
        return process_plan_request(plan_url, plan_name, plan_ref, plan_path, True, out_format)

    if plan_name is not None and test_name is not None:
        if test_url is None or plan_url is None:
            logger.fail("Missing required test/plan parameters")
            raise GeneralError("Missing required test/plan parameters")
        return process_testplan_request(
            test_url, test_name, test_ref, test_path,
            plan_url, plan_name, plan_ref, plan_path,
            out_format)

    logger.fail("Invalid combination of test and plan parameters")
    raise GeneralError("Invalid combination of test and plan parameters")
