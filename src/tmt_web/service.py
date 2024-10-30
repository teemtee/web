import logging
from typing import Literal, TypeVar

import tmt
from celery.app import Celery  # type: ignore[attr-defined]
from tmt import Logger
from tmt._compat.pathlib import Path
from tmt.utils import GeneralError, GitUrlError

from tmt_web import settings
from tmt_web.generators import html_generator, json_generator, yaml_generator
from tmt_web.utils import git_handler

# Create main logger for the application
logger = Logger(logging.getLogger("tmt-web"))

app = Celery(__name__, broker=settings.REDIS_URL, backend=settings.REDIS_URL)

# Type variable for Test/Plan objects
T = TypeVar('T', tmt.Test, tmt.Plan)


def get_tree(url: str, name: str, ref: str | None, tree_path: str | None) -> tmt.base.Tree:
    """
    Clone the repository and return the Tree object.

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


def format_output(obj: tmt.Test | tmt.Plan, out_format: str, logger: Logger) -> str:
    """
    Format a Test or Plan object in the specified output format.

    :param obj: Test or Plan object to format
    :param out_format: Output format (html, json, or yaml)
    :param logger: Logger instance
    :return: Formatted output string
    :raises: GeneralError if format not supported
    """
    logger.debug(f"Generating {out_format} output")
    match out_format:
        case "html":
            return html_generator.generate_html_page(obj, logger=logger)
        case "json":
            if isinstance(obj, tmt.Test):
                return json_generator.generate_test_json(obj, logger=logger)
            return json_generator.generate_plan_json(obj, logger=logger)
        case "yaml":
            if isinstance(obj, tmt.Test):
                return yaml_generator.generate_test_yaml(obj, logger=logger)
            return yaml_generator.generate_plan_yaml(obj, logger=logger)
        case _:
            logger.fail(f"Unsupported output format: {out_format}")
            raise GeneralError(f"Unsupported output format: {out_format}")


def process_test_request(
    test_url: str,
    test_name: str,
    test_ref: str | None = None,
    test_path: str | None = None,
    out_format: str = "json",
) -> str:
    """
    Process a test request and return formatted output.

    :param test_url: Test url
    :param test_name: Test name
    :param test_ref: Test repo ref (optional)
    :param test_path: Test path (optional)
    :param out_format: Output format
    :return: Formatted output string
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

    return format_output(wanted_test, out_format, logger)


def process_plan_request(
    plan_url: str,
    plan_name: str,
    plan_ref: str | None = None,
    plan_path: str | None = None,
    out_format: str = "json",
) -> str:
    """
    Process a plan request and return formatted output.

    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref (optional)
    :param plan_path: Plan path (optional)
    :param out_format: Output format
    :return: Formatted output string
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

    return format_output(wanted_plan, out_format, logger)


def process_testplan_request(
    test_url: str,
    test_name: str,
    test_ref: str | None,
    test_path: str | None,
    plan_url: str,
    plan_name: str,
    plan_ref: str | None,
    plan_path: str | None,
    out_format: str,
) -> str:
    """
    Process a test and plan request and return formatted output.

    :param test_url: Test URL
    :param test_name: Test name
    :param test_ref: Test repo ref (optional)
    :param test_path: Test path (optional)
    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref (optional)
    :param plan_path: Plan path (optional)
    :param out_format: Output format
    :return: Formatted output string
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if test/plan not found or format not supported
    """
    # Get test and plan objects
    tree = get_tree(test_url, test_name, test_ref, test_path)
    tests = tree.tests(names=[test_name])
    if not tests:
        logger.fail(f"Test '{test_name}' not found")
        raise GeneralError(f"Test '{test_name}' not found")
    test = tests[0]

    tree = get_tree(plan_url, plan_name, plan_ref, plan_path)
    plans = tree.plans(names=[plan_name])
    if not plans:
        logger.fail(f"Plan '{plan_name}' not found")
        raise GeneralError(f"Plan '{plan_name}' not found")
    plan = plans[0]

    # Generate combined output
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
    out_format: Literal["html", "json", "yaml"],
) -> str:
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
        return process_test_request(test_url, test_name, test_ref, test_path, out_format)

    if plan_name is not None and test_name is None:
        if plan_url is None:
            logger.fail("Missing required plan parameters")
            raise GeneralError("Missing required plan parameters")
        return process_plan_request(plan_url, plan_name, plan_ref, plan_path, out_format)

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
