import logging
from unittest.mock import Mock

import pytest
import tmt
from tmt.utils import GeneralError, GitUrlError

from tmt_web.generators import html_generator, yaml_generator
from tmt_web.service import (
    format_output,
    get_tree,
    main,
    process_plan_request,
    process_test_request,
    process_testplan_request,
)
from tmt_web.service import (
    logger as service_logger,
)


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


def test_get_tree_git_error(mocker, logger):
    """Test get_tree with git error."""
    mocker.patch("tmt_web.utils.git_handler.get_git_repository", side_effect=GitUrlError("Invalid URL"))

    with pytest.raises(GitUrlError, match="Invalid repository URL"):
        get_tree("invalid-url", "test", None, None)


def test_get_tree_general_error(mocker):
    """Test get_tree with general error."""
    mocker.patch("tmt_web.utils.git_handler.get_git_repository", side_effect=RuntimeError("Failed"))

    with pytest.raises(GeneralError, match="Failed to clone repository"):
        get_tree("url", "test", None, "/some/path")


def test_get_tree_with_git_suffix(mocker):
    """Test get_tree with .git suffix path."""
    mock_path = mocker.Mock()
    mock_path.suffix = '.git'
    mock_path.with_suffix.return_value = mock_path
    mock_path.as_posix.return_value = '/path/to/repo'
    mocker.patch("tmt_web.utils.git_handler.get_git_repository", return_value=mock_path)
    mocker.patch("tmt.base.Tree")
    mocker.patch("tmt.plugins.explore")

    get_tree("url", "test", None, "/some/path")
    mock_path.with_suffix.assert_called_once_with('')


def test_format_output_unsupported_format(mocker, logger):
    """Test format_output with unsupported format."""
    test = Mock(spec=tmt.Test)

    with pytest.raises(GeneralError, match="Unsupported output format"):
        format_output(test, "invalid", logger)


def test_format_output_yaml_plan(mocker, logger):
    """Test format_output with yaml format and Plan object."""
    plan = Mock(spec=tmt.Plan)
    mocker.patch("tmt_web.generators.yaml_generator.generate_plan_yaml")
    format_output(plan, "yaml", logger)
    yaml_generator.generate_plan_yaml.assert_called_once_with(plan, logger=logger)  # type: ignore[attr-defined]


def test_process_test_request_not_found(mocker):
    """Test process_test_request when test not found."""
    mocker.patch("tmt_web.service.get_tree").return_value.tests.return_value = []

    with pytest.raises(GeneralError, match="Test 'test' not found"):
        process_test_request("url", "test")


def test_process_plan_request_not_found(mocker):
    """Test process_plan_request when plan not found."""
    mocker.patch("tmt_web.service.get_tree").return_value.plans.return_value = []

    with pytest.raises(GeneralError, match="Plan 'plan' not found"):
        process_plan_request("url", "plan")


def test_process_testplan_request_test_not_found(mocker):
    """Test process_testplan_request when test not found."""
    mocker.patch("tmt_web.service.get_tree").return_value.tests.return_value = []

    with pytest.raises(GeneralError, match="Test 'test' not found"):
        process_testplan_request(
            "url", "test", None, None,
            "url", "plan", None, None,
            "json",
        )


def test_process_testplan_request_plan_not_found(mocker):
    """Test process_testplan_request when plan not found."""
    tree_mock = mocker.patch("tmt_web.service.get_tree").return_value
    # First call for test succeeds
    tree_mock.tests.return_value = [mocker.Mock()]
    # Second call for plan fails
    tree_mock.plans.return_value = []

    with pytest.raises(GeneralError, match="Plan 'plan' not found"):
        process_testplan_request(
            "url", "test", None, None,
            "url", "plan", None, None,
            "json",
        )


def test_process_testplan_request_html(mocker):
    """Test process_testplan_request with html format."""
    tree_mock = mocker.patch("tmt_web.service.get_tree").return_value
    test_mock = Mock(spec=tmt.Test)
    plan_mock = Mock(spec=tmt.Plan)
    tree_mock.tests.return_value = [test_mock]
    tree_mock.plans.return_value = [plan_mock]
    mocker.patch("tmt_web.generators.html_generator.generate_testplan_html_page")

    process_testplan_request(
        "url", "test", None, None,
        "url", "plan", None, None,
        "html",
    )
    html_generator.generate_testplan_html_page.assert_called_once_with(test_mock, plan_mock, logger=service_logger)  # type: ignore[attr-defined]


def test_process_testplan_request_yaml(mocker):
    """Test process_testplan_request with yaml format."""
    tree_mock = mocker.patch("tmt_web.service.get_tree").return_value
    test_mock = Mock(spec=tmt.Test)
    plan_mock = Mock(spec=tmt.Plan)
    tree_mock.tests.return_value = [test_mock]
    tree_mock.plans.return_value = [plan_mock]
    mocker.patch("tmt_web.generators.yaml_generator.generate_testplan_yaml")

    process_testplan_request(
        "url", "test", None, None,
        "url", "plan", None, None,
        "yaml",
    )
    yaml_generator.generate_testplan_yaml.assert_called_once_with(test_mock, plan_mock, logger=service_logger)  # type: ignore[attr-defined]


def test_process_testplan_request_unsupported_format(mocker):
    """Test process_testplan_request with unsupported format."""
    tree_mock = mocker.patch("tmt_web.service.get_tree").return_value
    tree_mock.tests.return_value = [mocker.Mock()]
    tree_mock.plans.return_value = [mocker.Mock()]

    with pytest.raises(GeneralError, match="Unsupported output format"):
        process_testplan_request(
            "url", "test", None, None,
            "url", "plan", None, None,
            "invalid",
        )


def test_main_invalid_parameters():
    """Test main with invalid parameter combinations."""
    # Missing test URL
    with pytest.raises(GeneralError, match="Missing required test parameters"):
        main(None, "test", None, None, None, None, None, None, "json")

    # Missing plan URL
    with pytest.raises(GeneralError, match="Missing required plan parameters"):
        main(None, None, None, None, None, "plan", None, None, "json")

    # Missing test URL in combined request
    with pytest.raises(GeneralError, match="Missing required test/plan parameters"):
        main(None, "test", None, None, "url", "plan", None, None, "json")

    # Missing plan URL in combined request
    with pytest.raises(GeneralError, match="Missing required test/plan parameters"):
        main("url", "test", None, None, None, "plan", None, None, "json")

    # Invalid combination (neither test nor plan)
    with pytest.raises(GeneralError, match="Invalid combination of test and plan parameters"):
        main(None, None, None, None, None, None, None, None, "json")
