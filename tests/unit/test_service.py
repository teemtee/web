import logging

import pytest
import tmt
from tmt.utils import GeneralError, GitUrlError

from tmt_web.service import format_output, get_tree, main, process_test_request


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
    mocker.patch("tmt_web.utils.git_handler.get_git_repository", side_effect=Exception("Failed"))

    with pytest.raises(GeneralError, match="Failed to clone repository"):
        get_tree("url", "test", None, None)


def test_format_output_unsupported_format(mocker, logger):
    """Test format_output with unsupported format."""
    test = mocker.Mock()

    with pytest.raises(GeneralError, match="Unsupported output format"):
        format_output(test, "invalid", logger)


def test_process_test_request_not_found(mocker):
    """Test process_test_request when test not found."""
    mocker.patch("tmt_web.service.get_tree").return_value.tests.return_value = []

    with pytest.raises(GeneralError, match="Test 'test' not found"):
        process_test_request("url", "test")


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
