"""Service layer for tmt-web using FastAPI background tasks and Valkey."""

import logging
from typing import Literal

import tmt
from fastapi import BackgroundTasks
from tmt import Logger
from tmt._compat.pathlib import Path
from tmt.utils import GeneralError, GitUrlError

from tmt_web.converters import create_testplan_data, plan_to_model, test_to_model
from tmt_web.formatters import format_data, serialize_data
from tmt_web.models import PlanData, TestData, TestPlanData
from tmt_web.utils import git_handler
from tmt_web.utils.task_manager import task_manager

# Create main logger for the application
logger = Logger(logging.getLogger("tmt-web"))


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
        tree_path += "/"
        # If path is set, construct a path to the tmt Tree
        if path.suffix == ".git":
            path = path.with_suffix("")
        path = Path(path.as_posix() + tree_path)

    logger.debug(f"Looking for tree in {path}")
    tmt.plugins.explore(logger=logger)
    tree = tmt.base.Tree(path=path, logger=logger)
    logger.debug("Tree found")
    return tree


def process_test_request(
    test_url: str,
    test_name: str,
    test_ref: str | None = None,
    test_path: str | None = None,
) -> TestData:
    """
    Process a test request and return test data.

    :param test_url: Test url
    :param test_name: Test name
    :param test_ref: Test repo ref (optional)
    :param test_path: Test path (optional)
    :return: Test data model
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if test not found
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

    return test_to_model(wanted_test)


def process_plan_request(
    plan_url: str,
    plan_name: str,
    plan_ref: str | None = None,
    plan_path: str | None = None,
) -> PlanData:
    """
    Process a plan request and return plan data.

    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref (optional)
    :param plan_path: Plan path (optional)
    :return: Plan data model
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if plan not found
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

    return plan_to_model(wanted_plan)


def process_testplan_request(
    test_url: str,
    test_name: str,
    test_ref: str | None,
    test_path: str | None,
    plan_url: str,
    plan_name: str,
    plan_ref: str | None,
    plan_path: str | None,
) -> TestPlanData:
    """
    Process a test and plan request and return combined data.

    :param test_url: Test URL
    :param test_name: Test name
    :param test_ref: Test repo ref (optional)
    :param test_path: Test path (optional)
    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref (optional)
    :param plan_path: Plan path (optional)
    :return: Combined test and plan data model
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if test/plan not found
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

    return create_testplan_data(test, plan)


def process_request(
    background_tasks: BackgroundTasks,
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

    Creates a background task for processing the request and returns a task ID.

    :param background_tasks: FastAPI BackgroundTasks object
    :param test_url: Test URL
    :param test_name: Test name
    :param test_ref: Test repo ref (optional)
    :param test_path: Test path (optional)
    :param plan_url: Plan URL
    :param plan_name: Plan name
    :param plan_ref: Plan repo ref (optional)
    :param plan_path: Plan path (optional)
    :param out_format: Output format
    :return: Task ID for tracking the task
    :raises: GeneralError for invalid argument combinations
    """
    logger.debug("Starting request processing")
    logger.debug("Validating input parameters")

    # Use task manager to create and execute the background task
    return task_manager.execute_task(
        background_tasks=background_tasks,
        func=_process_request_worker,
        test_url=test_url,
        test_name=test_name,
        test_ref=test_ref,
        test_path=test_path,
        plan_url=plan_url,
        plan_name=plan_name,
        plan_ref=plan_ref,
        plan_path=plan_path,
        out_format=out_format,
    )


def _process_request_worker(
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
    Worker function for processing requests in background.

    This function is meant to be executed by the task manager.
    Returns serialized data that can be formatted later according to the requested format.

    :raises: GeneralError for invalid argument combinations
    """
    data: TestData | PlanData | TestPlanData
    if test_name is not None and plan_name is None:
        if test_url is None:
            logger.fail("Missing required test parameters")
            raise GeneralError("Missing required test parameters")
        data = process_test_request(test_url, test_name, test_ref, test_path)
    elif plan_name is not None and test_name is None:
        if plan_url is None:
            logger.fail("Missing required plan parameters")
            raise GeneralError("Missing required plan parameters")
        data = process_plan_request(plan_url, plan_name, plan_ref, plan_path)
    elif plan_name is not None and test_name is not None:
        if test_url is None or plan_url is None:
            logger.fail("Missing required test/plan parameters")
            raise GeneralError("Missing required test/plan parameters")
        data = process_testplan_request(
            test_url,
            test_name,
            test_ref,
            test_path,
            plan_url,
            plan_name,
            plan_ref,
            plan_path,
        )
    else:
        logger.fail("Invalid combination of test and plan parameters")
        raise GeneralError("Invalid combination of test and plan parameters")

    # Format immediately if requested, otherwise store serialized data
    if out_format:
        return format_data(data, out_format, logger)

    # Otherwise store raw data for later formatting
    return serialize_data(data)
