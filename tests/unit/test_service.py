"""Unit tests for the service layer."""

import json
import logging
from unittest.mock import Mock

import pytest
import tmt
from tmt.utils import GeneralError, GitUrlError

from tmt_web.formatters import deserialize_data, format_data
from tmt_web.models import PlanData, TestData, TestPlanData
from tmt_web.service import (
    get_tree,
    process_plan_request,
    process_request,
    process_test_request,
    process_testplan_request,
)
from tmt_web.utils.task_manager import task_manager


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


@pytest.fixture
def mock_test():
    """Create a mock test with required attributes."""
    test = Mock(spec=tmt.Test)
    test.name = "test"
    test.node = Mock()
    test.node.get.return_value = {
        "name": "test",
        "summary": "Test summary",
        "contact": "Test Contact <test@example.com>",
        "framework": "shell",
        "tier": "1",
    }
    test.web_link.return_value = "https://example.com/test"
    test.fmf_id = Mock()
    test.fmf_id.name = "test"
    test.fmf_id.url = "https://example.com/test"
    test.fmf_id.path = None
    test.fmf_id.ref = "main"
    return test


@pytest.fixture
def mock_plan():
    """Create a mock plan with required attributes."""
    plan = Mock(spec=tmt.Plan)
    plan.name = "plan"
    plan.node = Mock()
    plan.node.get.return_value = {
        "name": "plan",
        "summary": "Plan summary",
        "execute": {"how": "tmt"},
        "discover": {"how": "fmf"},
    }
    plan.web_link.return_value = "https://example.com/plan"
    plan.fmf_id = Mock()
    plan.fmf_id.name = "plan"
    plan.fmf_id.url = "https://example.com/plan"
    plan.fmf_id.path = None
    plan.fmf_id.ref = "main"
    return plan


def test_get_tree_git_error(mocker, logger):
    """Test get_tree with git error."""
    mocker.patch(
        "tmt_web.utils.git_handler.get_git_repository", side_effect=GitUrlError("Invalid URL")
    )

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
    mock_path.suffix = ".git"
    mock_path.with_suffix.return_value = mock_path
    mock_path.as_posix.return_value = "/path/to/repo"
    mocker.patch("tmt_web.utils.git_handler.get_git_repository", return_value=mock_path)
    mocker.patch("tmt.base.Tree")
    mocker.patch("tmt.plugins.explore")

    get_tree("url", "test", None, "/some/path")
    mock_path.with_suffix.assert_called_once_with("")


def test_format_data_unsupported_format(mocker, logger):
    """Test format_data with unsupported format."""
    test_data = TestData(name="test")

    with pytest.raises(ValueError, match="Unsupported output format"):
        format_data(test_data, "invalid", logger)


def test_format_data_yaml_plan(mocker, logger):
    """Test format_data with yaml format and Plan data."""
    plan_data = PlanData(
        name="plan",
        summary="Plan summary",
        execute=[{"how": "tmt"}],
    )
    result = format_data(plan_data, "yaml", logger)
    assert "name: plan" in result
    assert "summary: Plan summary" in result
    assert "execute:" in result
    assert "- how: tmt" in result


def test_format_data_html_test(mocker, logger):
    """Test format_data with html format and Test data."""
    test_data = TestData(name="test", summary="Test summary")
    mocker.patch(
        "tmt_web.generators.html_generator.generate_html_page", return_value="<html>test</html>"
    )
    result = format_data(test_data, "html", logger)
    assert result == "<html>test</html>"


def test_format_data_html_testplan(mocker, logger):
    """Test format_data with html format and TestPlan data."""
    test_data = TestData(name="test", summary="Test summary")
    plan_data = PlanData(name="plan", summary="Plan summary")
    testplan_data = TestPlanData(test=test_data, plan=plan_data)
    mocker.patch(
        "tmt_web.generators.html_generator.generate_testplan_html_page",
        return_value="<html>testplan</html>",
    )
    result = format_data(testplan_data, "html", logger)
    assert result == "<html>testplan</html>"


def test_deserialize_data_invalid_json(mocker):
    """Test deserialize_data with invalid JSON."""
    with pytest.raises(ValueError, match="Expecting value"):
        deserialize_data("invalid json")


def test_deserialize_data_unknown_format(mocker):
    """Test deserialize_data with unknown data format."""
    with pytest.raises(ValueError, match="Field required"):
        deserialize_data('{"unknown": "format"}')


def test_process_test_request_not_found(mocker):
    """Test process_test_request when test not found."""
    mocker.patch("tmt_web.service.get_tree").return_value.tests.return_value = []

    with pytest.raises(GeneralError, match="Test 'test' not found"):
        process_test_request("url", "test")


def test_process_test_request_returns_test_data(mocker, mock_test):
    """Test process_test_request returns TestData."""
    mocker.patch("tmt_web.service.get_tree").return_value.tests.return_value = [mock_test]

    result = process_test_request("url", "test")
    assert isinstance(result, TestData)
    assert result.name == "test"
    assert result.summary == "Test summary"
    assert result.contact == ["Test Contact <test@example.com>"]
    assert result.framework == "shell"
    assert result.tier == "1"


def test_process_plan_request_not_found(mocker):
    """Test process_plan_request when plan not found."""
    mocker.patch("tmt_web.service.get_tree").return_value.plans.return_value = []

    with pytest.raises(GeneralError, match="Plan 'plan' not found"):
        process_plan_request("url", "plan")


def test_process_plan_request_returns_plan_data(mocker, mock_plan):
    """Test process_plan_request returns PlanData."""
    mocker.patch("tmt_web.service.get_tree").return_value.plans.return_value = [mock_plan]

    result = process_plan_request("url", "plan")
    assert isinstance(result, PlanData)
    assert result.name == "plan"
    assert result.summary == "Plan summary"
    assert result.execute == [{"how": "tmt"}]
    assert result.discover == {"how": "fmf"}


def test_process_testplan_request_test_not_found(mocker):
    """Test process_testplan_request when test not found."""
    mocker.patch("tmt_web.service.get_tree").return_value.tests.return_value = []

    with pytest.raises(GeneralError, match="Test 'test' not found"):
        process_testplan_request(
            "url",
            "test",
            None,
            None,
            "url",
            "plan",
            None,
            None,
        )


def test_process_testplan_request_plan_not_found(mocker, mock_test):
    """Test process_testplan_request when plan not found."""
    tree_mock = mocker.patch("tmt_web.service.get_tree").return_value
    # First call for test succeeds
    tree_mock.tests.return_value = [mock_test]
    # Second call for plan fails
    tree_mock.plans.return_value = []

    with pytest.raises(GeneralError, match="Plan 'plan' not found"):
        process_testplan_request(
            "url",
            "test",
            None,
            None,
            "url",
            "plan",
            None,
            None,
        )


def test_process_testplan_request_returns_testplan_data(mocker, mock_test, mock_plan):
    """Test process_testplan_request returns TestPlanData."""
    tree_mock = mocker.patch("tmt_web.service.get_tree").return_value
    tree_mock.tests.return_value = [mock_test]
    tree_mock.plans.return_value = [mock_plan]

    result = process_testplan_request(
        "url",
        "test",
        None,
        None,
        "url",
        "plan",
        None,
        None,
    )
    assert isinstance(result, TestPlanData)
    assert result.test.name == "test"
    assert result.test.summary == "Test summary"
    assert result.plan.name == "plan"
    assert result.plan.summary == "Plan summary"


def test_process_testplan_request_with_all_attributes(mocker):
    """Test processing test and plan with all possible attributes."""
    # Create test with all possible attributes
    test = Mock(spec=tmt.Test)
    test.name = "complete-test"
    test.node = Mock()
    test.node.get.return_value = {
        "name": "complete-test",
        "summary": "Test with all attributes",
        "description": "Detailed test description",
        "contact": ["John Doe <john@example.com>", "Jane Doe <jane@example.com>"],
        "component": ["component1", "component2"],
        "enabled": True,
        "environment": {"KEY": "value"},
        "duration": "15m",
        "framework": "shell",
        "manual": False,
        "path": "/path/to/test",
        "tier": "1",
        "order": 50,
        "id": "test-123",
        "link": [{"name": "issue", "url": "https://example.com/issue/123"}],
        "tag": ["tag1", "tag2"],
    }
    test.web_link.return_value = "https://example.com/test"
    test.fmf_id = Mock()
    test.fmf_id.name = "complete-test"
    test.fmf_id.url = "https://example.com/test"
    test.fmf_id.path = "/path/to/test"
    test.fmf_id.ref = "main"

    # Create plan with all possible attributes
    plan = Mock(spec=tmt.Plan)
    plan.name = "complete-plan"
    plan.node = Mock()
    plan.node.get.return_value = {
        "name": "complete-plan",
        "summary": "Plan with all attributes",
        "description": "Detailed plan description",
        "prepare": [{"how": "shell", "script": "prepare.sh"}],
        "execute": [{"how": "tmt"}],
        "finish": [{"how": "shell", "script": "cleanup.sh"}],
        "discover": {"how": "fmf"},
        "provision": {"how": "local"},
        "report": {"how": "html"},
        "enabled": True,
        "path": "/path/to/plan",
        "order": 100,
        "id": "plan-456",
        "link": [{"name": "docs", "url": "https://example.com/docs"}],
        "tag": ["plan-tag1", "plan-tag2"],
    }
    plan.web_link.return_value = "https://example.com/plan"
    plan.fmf_id = Mock()
    plan.fmf_id.name = "complete-plan"
    plan.fmf_id.url = "https://example.com/plan"
    plan.fmf_id.path = "/path/to/plan"
    plan.fmf_id.ref = "main"

    # Mock tree to return our test and plan
    tree_mock = mocker.patch("tmt_web.service.get_tree").return_value
    tree_mock.tests.return_value = [test]
    tree_mock.plans.return_value = [plan]

    # Process the request
    result = process_testplan_request(
        "url",
        "complete-test",
        None,
        None,
        "url",
        "complete-plan",
        None,
        None,
    )

    # Verify all attributes are present and correct
    assert isinstance(result, TestPlanData)

    # Verify test attributes
    assert result.test.name == "complete-test"
    assert result.test.summary == "Test with all attributes"
    assert result.test.description == "Detailed test description"
    assert result.test.contact == ["John Doe <john@example.com>", "Jane Doe <jane@example.com>"]
    assert result.test.component == ["component1", "component2"]
    assert result.test.enabled is True
    assert result.test.environment == {"KEY": "value"}
    assert result.test.duration == "15m"
    assert result.test.framework == "shell"
    assert result.test.manual is False
    assert result.test.path == "/path/to/test"
    assert result.test.tier == "1"
    assert result.test.order == 50
    assert result.test.id == "test-123"
    assert result.test.link == [{"name": "issue", "url": "https://example.com/issue/123"}]
    assert result.test.tag == ["tag1", "tag2"]
    assert result.test.fmf_id.name == "complete-test"
    assert result.test.fmf_id.url == "https://example.com/test"
    assert result.test.fmf_id.path == "/path/to/test"
    assert result.test.fmf_id.ref == "main"

    # Verify plan attributes
    assert result.plan.name == "complete-plan"
    assert result.plan.summary == "Plan with all attributes"
    assert result.plan.description == "Detailed plan description"
    assert result.plan.prepare == [{"how": "shell", "script": "prepare.sh"}]
    assert result.plan.execute == [{"how": "tmt"}]
    assert result.plan.finish == [{"how": "shell", "script": "cleanup.sh"}]
    assert result.plan.discover == {"how": "fmf"}
    assert result.plan.provision == {"how": "local"}
    assert result.plan.report == {"how": "html"}
    assert result.plan.enabled is True
    assert result.plan.path == "/path/to/plan"
    assert result.plan.order == 100
    assert result.plan.id == "plan-456"
    assert result.plan.link == [{"name": "docs", "url": "https://example.com/docs"}]
    assert result.plan.tag == ["plan-tag1", "plan-tag2"]
    assert result.plan.fmf_id.name == "complete-plan"
    assert result.plan.fmf_id.url == "https://example.com/plan"
    assert result.plan.fmf_id.path == "/path/to/plan"
    assert result.plan.fmf_id.ref == "main"


def test_main_invalid_parameters():
    """Test directly the worker function that validates parameters."""
    from tmt_web.service import _process_request_worker

    # Missing test URL
    with pytest.raises(GeneralError, match="Missing required test parameters"):
        _process_request_worker(None, "test", None, None, None, None, None, None, "json")

    # Missing plan URL
    with pytest.raises(GeneralError, match="Missing required plan parameters"):
        _process_request_worker(None, None, None, None, None, "plan", None, None, "json")

    # Missing test URL in combined request
    with pytest.raises(GeneralError, match="Missing required test/plan parameters"):
        _process_request_worker(None, "test", None, None, "url", "plan", None, None, "json")

    # Missing plan URL in combined request
    with pytest.raises(GeneralError, match="Missing required test/plan parameters"):
        _process_request_worker("url", "test", None, None, None, "plan", None, None, "json")

    # Invalid combination (neither test nor plan)
    with pytest.raises(GeneralError, match="Invalid combination of test and plan parameters"):
        _process_request_worker(None, None, None, None, None, None, None, None, "json")


def test_main_direct_processing(mocker):
    """Test main direct processing."""
    # Create a mock test
    test_data = TestData(name="test", summary="Test summary")

    # Mock process_test_request to return our test data
    mocker.patch("tmt_web.service.process_test_request", return_value=test_data)

    # Mock format_data to verify it's called directly
    mocker.patch("tmt_web.service.format_data", return_value="formatted_data")

    # Mock serialize_data to ensure it's NOT called
    mocker.patch("tmt_web.service.serialize_data")

    # Create a mock BackgroundTasks object
    mock_bg_tasks = mocker.Mock()

    # Call main with test parameters
    result = process_request(
        mock_bg_tasks, "url", "test", None, None, None, None, None, None, "json"
    )

    # Verify the task_manager.execute_task was called
    # Note: We don't need to verify format_data/serialize_data directly
    # as that's now handled inside the task manager
    assert isinstance(result, str)  # Should return a task ID


def test_main_with_background_tasks(mocker):
    """Test main with background tasks."""
    # Create a mock test
    test_data = TestData(name="test", summary="Test summary")

    # Mock process_test_request to return our test data
    mocker.patch("tmt_web.service.process_test_request", return_value=test_data)

    # Mock the task_manager.execute_task
    mock_task_execute = mocker.patch(
        "tmt_web.service.task_manager.execute_task", return_value="task-123"
    )

    # Create a mock BackgroundTasks object
    mock_bg_tasks = mocker.Mock()

    # Call main with test parameters
    result = process_request(
        mock_bg_tasks, "url", "test", None, None, None, None, None, None, "json"
    )

    # Verify task_manager.execute_task was called with the right parameters
    mock_task_execute.assert_called_once()
    assert result == "task-123"


def test_process_request_worker_no_output_format(mocker):
    """Test _process_request_worker when no output format is specified."""
    # Create mock data
    test_data = TestData(name="test", summary="Test summary")

    # Mock process_test_request
    mocker.patch("tmt_web.service.process_test_request", return_value=test_data)

    # Mock serialize_data
    mock_serialize = mocker.patch("tmt_web.service.serialize_data", return_value="serialized_data")

    # Call worker with None as format
    from tmt_web.service import _process_request_worker

    result = _process_request_worker("url", "test", None, None, None, None, None, None, None)

    # Verify serialize_data was called instead of format_data
    mock_serialize.assert_called_once_with(test_data)
    assert result == "serialized_data"


def test_task_manager_update_nonexistent_task(mocker):
    """Test updating a non-existent task in the task manager."""
    # Mock Valkey client get method to return None (task doesn't exist)
    mocker.patch.object(task_manager.client, "get", return_value=None)

    # Mock the set method to check it's not called
    mock_set = mocker.patch.object(task_manager.client, "set")

    # Mock logger to verify warning is called
    mock_logger = mocker.patch.object(task_manager, "logger")

    # Try to update a non-existent task
    task_manager.update_task("nonexistent-task-id", "SUCCESS", result="test result")

    # Verify warning was logged
    mock_logger.warning.assert_called_once_with(
        "Trying to update non-existent task nonexistent-task-id"
    )

    # Verify client.set was not called (early return)
    mock_set.assert_not_called()


def test_task_manager_get_corrupted_task(mocker):
    """Test getting a task with corrupted JSON data."""
    # Mock Valkey client get method to return invalid JSON
    mocker.patch.object(task_manager.client, "get", return_value=b"not valid json")

    # Mock logger to verify error is logged
    mock_logger = mocker.patch.object(task_manager, "logger")

    # Get a task with corrupted data
    result = task_manager.get_task_info("corrupted-task-id")

    # Verify error was logged
    mock_logger.fail.assert_called_once_with("Corrupted task data for corrupted-task-id")

    # Verify returned data has expected error state
    assert result["id"] == "corrupted-task-id"
    assert result["status"] == "FAILURE"
    assert result["error"] == "Corrupted task data"
    assert result["result"] is None


def test_task_manager_update_decode_error(mocker):
    """Test updating a task with corrupted JSON data."""
    # Mock Valkey client get method to return invalid JSON
    mocker.patch.object(task_manager.client, "get", return_value=b"not valid json")

    # Mock logger to verify error is logged
    mock_logger = mocker.patch.object(task_manager, "logger")

    # Update a task with corrupted data
    task_manager.update_task("corrupted-task-id", "SUCCESS", result="test result")

    # Verify error was logged
    mock_logger.fail.assert_called_once_with("Failed to decode task data for corrupted-task-id")


def test_task_manager_update_encode_error(mocker):
    """Test updating a task with data that can't be encoded to JSON."""

    # Create a mock object that can't be JSON serialized
    class UnserializableObject:
        pass

    unserializable = UnserializableObject()

    # Mock Valkey client get method to return valid task data
    valid_task_data = json.dumps(
        {"id": "task-id", "status": "PENDING", "created_at": "2023-01-01T00:00:00+00:00"}
    ).encode()
    mocker.patch.object(task_manager.client, "get", return_value=valid_task_data)

    # Mock logger to verify error is logged
    mock_logger = mocker.patch.object(task_manager, "logger")

    # Update a task with unserializable data
    task_manager.update_task("task-id", "SUCCESS", result=unserializable)

    # Verify error was logged
    assert mock_logger.fail.call_count == 1
    assert "Failed to encode task data for task-id" in mock_logger.fail.call_args[0][0]
