"""Integration tests for the API."""

import time

import pytest
from fastapi.testclient import TestClient

from tmt_web import settings
from tmt_web.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestApi:
    """This class tests the behaviour of the API directly."""

    def test_root_empty_redirects_to_docs(self, client):
        """Test that empty root path redirects to docs."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"

    def test_basic_test_request_html(self, client):
        """Test basic test request with default format (html)."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&test-ref=main",
        )
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert '<html lang="en">' in data
        # Now just validate it's a status page with processing indicator
        assert "Processing..." in data
        assert "Status: PENDING" in data

    def test_basic_test_request_html_with_path(self, client):
        """Test basic test request with path and default format (html)."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt.git"
            "&test-name=/test/shell/weird"
            "&test-path=/tests/execute/basic/data"
            "&test-ref=main",
        )
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert '<html lang="en">' in data
        # Now just validate it's a status page with processing indicator
        assert "Processing..." in data
        assert "Status: PENDING" in data

    def test_basic_test_request_explicit_html(self, client):
        """Test basic test request with explicit html format."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&test-ref=main&format=html",
        )
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert '<html lang="en">' in data
        # Now just validate it's a status page with processing indicator
        assert "Processing..." in data
        assert "Status: PENDING" in data

    def test_basic_test_request_json(self, client):
        """Test basic test request with explicit json format."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=json",
        )
        assert response.status_code == 200
        # Parse the response as JSON to verify it's valid JSON
        json_data = response.json()
        # Check that we get a task status response with background task ID
        assert "id" in json_data
        assert json_data["status"] == "PENDING"
        assert "status_callback_url" in json_data

    def test_basic_test_request_yaml(self, client):
        """Test basic test request with yaml format."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=yaml",
        )
        assert response.status_code == 200
        # For YAML, the response is still JSON for the task status
        json_data = response.json()
        # Check that we get a task status response with background task ID
        assert "id" in json_data
        assert json_data["status"] == "PENDING"
        assert "status_callback_url" in json_data

    def test_basic_plan_request(self, client):
        """Test basic plan request with default format (html)."""
        response = client.get(
            "/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan",
        )
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert '<html lang="en">' in data
        # Now just validate it's a status page with processing indicator
        assert "Processing..." in data
        assert "Status: PENDING" in data

    def test_basic_testplan_request(self, client):
        """Test basic testplan request with default format (html)."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&"
            "plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan",
        )
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert '<html lang="en">' in data
        # Now just validate it's a status page with processing indicator
        assert "Processing..." in data
        assert "Status: PENDING" in data

    def test_invalid_testplan_arguments(self, client):
        """Test invalid combination of test and plan parameters."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&plan-url=https://github.com/teemtee/tmt&"
            "plan-name=/plans/features/basic",
        )
        assert response.status_code == 400
        data = response.content.decode("utf-8")
        assert "Both test-url and test-name must be provided together" in data

    def test_not_found_errors(self, client):
        """Test that missing tests/plans return 404."""
        # For simplicity, we'll check that the correct HTTP exception is raised
        # in the general_exception_handler which captures GeneralError
        from tmt.utils import GeneralError

        # Trigger the exception handler with a test not found error
        @app.get("/test-not-found-error-test")
        def test_not_found_error():
            raise GeneralError("Test '/nonexistent/test' not found")

        response = client.get("/test-not-found-error-test")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        # Trigger the exception handler with a plan not found error
        @app.get("/plan-not-found-error-test")
        def plan_not_found_error():
            raise GeneralError("Plan '/nonexistent/plan' not found")

        response = client.get("/plan-not-found-error-test")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_task_failure_generic_error(self, client, monkeypatch):
        """Test handling a task that failed with a generic error (not 'not found')."""
        # First create a real task to get a valid task ID
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=json",
        )
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Mock the task manager get_task_info to return a generic failure
        def mock_get_task_info(tid):
            return {
                "id": tid,
                "status": "FAILURE",
                "error": "Some generic error occurred",
                "result": None,
            }

        monkeypatch.setattr(
            "tmt_web.utils.task_manager.task_manager.get_task_info", mock_get_task_info
        )

        # Now try to get the result, should return 500 with the error
        response = client.get(f"/?task-id={task_id}&format=json")
        assert response.status_code == 500
        assert "Some generic error occurred" in response.json()["detail"]

    def test_task_pending_status(self, client, monkeypatch):
        """Test getting PENDING task status (covers the _to_task_out default path)."""
        # First create a real task to get a valid task ID
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=json",
        )
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Mock the task manager get_task_info to return PENDING status
        def mock_get_task_info(tid):
            return {
                "id": tid,
                "status": "PENDING",
                "result": None,
            }

        monkeypatch.setattr(
            "tmt_web.utils.task_manager.task_manager.get_task_info", mock_get_task_info
        )

        # Test with JSON format
        response = client.get(f"/status?task-id={task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert "/status?task-id=" in data["status_callback_url"]

        # Test with HTML format to cover line 392
        response = client.get(f"/?task-id={task_id}&format=html")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING"
        assert "/status/html?task-id=" in data["status_callback_url"]

    def test_status_endpoint_no_task_id(self, client):
        """Test /status endpoint with no task_id parameter."""
        response = client.get("/status")
        assert response.status_code == 422  # FastAPI validation error
        assert "Field required" in response.json()["detail"][0]["msg"]

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert data["status"] == "ok"
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["uptime_seconds"], float)

        # Check version info
        assert "api" in data["version"]
        assert "python" in data["version"]
        assert "tmt" in data["version"]

        # Check dependencies
        assert "valkey" in data["dependencies"]
        assert data["dependencies"]["valkey"] in ["ok", "failed"]

        # Check system info
        assert "platform" in data["system"]
        assert "hostname" in data["system"]
        assert "python_implementation" in data["system"]

    def test_health_check_valkey_error(self, client, monkeypatch):
        """Test health check when Valkey ping fails."""

        # Mock Valkey ping to fail
        def mock_ping(*args, **kwargs):
            raise Exception("Valkey connection failed")

        monkeypatch.setattr("tmt_web.utils.task_manager.task_manager.ping", mock_ping)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert data["dependencies"]["valkey"] == "failed"
        assert data["status"] == "ok"  # Overall status should still be ok


class TestBackgroundTasks:
    """This class tests the API with background tasks."""

    def test_basic_test_request_json(self, client):
        """Test basic test request with explicit json format."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=json",
        )
        assert response.status_code == 200
        json_data = response.json()
        while True:
            if json_data["status"] == "PENDING":
                response = client.get("/status?task-id=" + json_data["id"])
                assert response.status_code == 200
                json_data = response.json()
                time.sleep(0.1)
            elif json_data["status"] == "SUCCESS":
                # Get the final JSON result from the task
                response = client.get(f"/?task-id={json_data['id']}&format=json")
                assert response.status_code == 200
                result_data = response.json()
                assert (
                    result_data["fmf-id"]["url"]
                    == "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf"
                )
                break
            elif json_data["status"] == "FAILURE":
                pytest.fail("status = FAILURE: " + json_data["result"])
            else:
                pytest.fail("Unknown status: " + json_data["status"])

    def test_basic_test_request_default_html(self, client):
        """Test basic test request with default format (html)."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke",
        )
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "Processing..." in data
        assert "setTimeout" in data  # Check for auto-refresh script

        # Extract task ID from status callback URL
        task_id = data.split("task-id=")[1].split('"')[0]

        # Poll until complete
        while True:
            response = client.get(f"/status/html?task-id={task_id}", follow_redirects=False)
            if response.status_code == 303:  # Redirect to root endpoint
                assert response.headers["location"] == f"{settings.API_HOSTNAME}/?task-id={task_id}"
                # Follow redirect to get final result
                response = client.get(response.headers["location"])
                assert response.status_code == 200
                data = response.content.decode("utf-8")
                assert "Just a basic smoke test" in data
                break
            if response.status_code == 200:
                data = response.content.decode("utf-8")
                if "Processing..." in data:
                    time.sleep(0.1)
                    continue
                if "Task Failed" in data:
                    pytest.fail("Task failed: " + data)
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_basic_test_request_explicit_html(self, client):
        """Test basic test request with explicit html format."""
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=html",
        )
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "Processing..." in data
        assert "setTimeout" in data  # Check for auto-refresh script

        # Extract task ID from status callback URL
        task_id = data.split("task-id=")[1].split('"')[0]

        # Poll until complete
        while True:
            response = client.get(f"/status/html?task-id={task_id}", follow_redirects=False)
            if response.status_code == 303:  # Redirect to root endpoint
                assert response.headers["location"] == f"{settings.API_HOSTNAME}/?task-id={task_id}"
                # Follow redirect to get final result
                response = client.get(response.headers["location"])
                assert response.status_code == 200
                data = response.content.decode("utf-8")
                assert "Just a basic smoke test" in data
                break
            if response.status_code == 200:
                data = response.content.decode("utf-8")
                if "Processing..." in data:
                    time.sleep(0.1)
                    continue
                if "Task Failed" in data:
                    pytest.fail("Task failed: " + data)
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_basic_test_request_yaml(self, client):
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=yaml",
        )
        assert response.status_code == 200
        json_data = response.json()  # Status responses are always JSON
        while True:
            if json_data["status"] == "PENDING":
                response = client.get("/status?task-id=" + json_data["id"])
                assert response.status_code == 200
                json_data = response.json()
                time.sleep(0.1)
            elif json_data["status"] == "SUCCESS":
                # Get the final result in YAML format
                response = client.get(f"/?task-id={json_data['id']}&format=yaml")
                assert response.status_code == 200
                data = response.content.decode("utf-8")
                assert "500" not in data
                assert (
                    "url: https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf"
                    in data
                )
                break
            elif json_data["status"] == "FAILURE":
                pytest.fail("status = FAILURE: " + json_data["result"])
            else:
                pytest.fail("Unknown status: " + json_data["status"])

    def test_root_endpoint_with_task_id(self, client):
        """Test retrieving task results directly through root endpoint."""
        # First create a task with explicit JSON format
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=json",
        )
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Wait for task to complete
        while True:
            response = client.get(f"/status?task-id={task_id}")
            json_data = response.json()
            if json_data["status"] == "SUCCESS":
                break
            time.sleep(0.1)

        # Now test retrieving the result directly through root endpoint
        # Request the result with explicit JSON format
        response = client.get(f"/?task-id={task_id}&format=json")
        assert response.status_code == 200
        result_data = response.json()
        assert (
            result_data["fmf-id"]["url"]
            == "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf"
        )

    def test_root_endpoint_with_task_id_yaml(self, client):
        """Test retrieving task results in YAML format through root endpoint."""
        # First create a task
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=yaml",
        )
        assert response.status_code == 200
        task_data = response.json()  # Status responses are always JSON
        task_id = task_data["id"]

        # Wait for task to complete
        while True:
            response = client.get(f"/status?task-id={task_id}")
            json_data = response.json()
            if json_data["status"] == "SUCCESS":
                break
            time.sleep(0.1)

        # Now test retrieving the result directly through root endpoint
        response = client.get(f"/?task-id={task_id}&format=yaml")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "url: https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data

    def test_root_endpoint_with_task_id_html(self, client):
        """Test retrieving task results in HTML format through root endpoint."""
        # First create a task
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke",
        )
        assert response.status_code == 200
        task_id = response.content.decode("utf-8").split("task-id=")[1].split('"')[0]

        # Wait for task to complete and get redirected
        while True:
            response = client.get(f"/status/html?task-id={task_id}", follow_redirects=False)
            if response.status_code == 303:  # Redirect to root endpoint
                assert response.headers["location"] == f"{settings.API_HOSTNAME}/?task-id={task_id}"
                # Follow redirect to get final result
                response = client.get(response.headers["location"])
                assert response.status_code == 200
                data = response.content.decode("utf-8")
                assert "500" not in data
                assert '<html lang="en">' in data
                assert "Just a basic smoke test" in data
                break
            time.sleep(0.1)

    def test_root_endpoint_with_invalid_task_id(self, client, monkeypatch):
        """Test root endpoint with invalid task ID."""

        # Mock the task manager to handle invalid task IDs
        def mock_get_task_info(tid):
            return {"id": tid, "status": "FAILURE", "error": "Task not found", "result": None}

        monkeypatch.setattr(
            "tmt_web.utils.task_manager.task_manager.get_task_info", mock_get_task_info
        )

        response = client.get("/?task-id=invalid-task-id")
        assert response.status_code == 404  # Should return 404 not found
        data = response.json()
        assert "Task not found" in data["detail"]

    def test_status_html_endpoint_missing_task_id(self, client):
        response = client.get("/status/html")
        assert response.status_code == 422  # FastAPI validation error
        assert "Field required" in response.json()["detail"][0]["msg"]

    def test_status_endpoint_empty_task_id(self, client):
        """Test /status endpoint with empty task_id."""
        response = client.get("/status?task-id=")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "task-id is required"

    def test_status_html_endpoint_empty_task_id(self, client):
        """Test /status/html endpoint with empty task_id."""
        response = client.get("/status/html?task-id=")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "task-id is required"

    def test_status_html_endpoint_invalid_task_id(self, client):
        response = client.get("/status/html?task-id=invalid-task-id")
        assert response.status_code == 200  # Still returns 200 as it shows a status page
        data = response.content.decode("utf-8")
        assert "Task Status" in data
        assert "Status: FAILURE" in data  # Now returns FAILURE for invalid task IDs
        assert "Task Failed" in data  # Should show failure state
        assert "Error: Task not found" in data  # Now properly displays the error message

    def test_not_found_with_background_tasks(self, client):
        """Test that missing tests/plans return 404 with background tasks."""
        # Initial request creates a task - use explicit JSON format
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/nonexistent/test&format=json",
        )
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Poll the status endpoint until the task completes
        while True:
            response = client.get(f"/status?task-id={task_id}")
            if response.status_code == 404:
                # Task completed with not found error
                assert "not found" in response.json()["detail"].lower()
                break
            if response.status_code == 200:
                # Task still running
                status_data = response.json()
                if status_data["status"] == "FAILURE":
                    # Task failed, check if it's a not found error
                    if "not found" in status_data["result"].lower():
                        # This should now return 404 instead of 200
                        response = client.get(f"/status?task-id={task_id}")
                        assert response.status_code == 404
                        assert "not found" in response.json()["detail"].lower()
                        break
                    pytest.fail(f"Task failed with unexpected error: {status_data['result']}")
                elif status_data["status"] != "PENDING":
                    pytest.fail(f"Task completed with unexpected status: {status_data['status']}")
                time.sleep(0.1)
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_health_check_with_valkey(self, client):
        """Test health check endpoint with Valkey."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Dependencies should be ok when Valkey is running
        assert data["dependencies"]["valkey"] == "ok"

    def test_task_result_error_handling(self, client, monkeypatch):
        """Test error handling in _handle_task_result when deserialization fails."""
        # First create a real task to get a valid task ID
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=json",
        )
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Mock the task manager get_task_info to return a malformed result
        def mock_get_task_info(tid):
            return {
                "id": tid,
                "status": "SUCCESS",
                "result": '{"corrupt": "json with malformed structure',  # Malformed JSON
            }

        monkeypatch.setattr(
            "tmt_web.utils.task_manager.task_manager.get_task_info", mock_get_task_info
        )

        # Now try to get the result, which should trigger the error handling
        response = client.get(f"/?task-id={task_id}&format=json")
        assert response.status_code == 500
        assert "Error handling task result" in response.json()["detail"]

    def test_task_result_with_not_found_error(self, client, monkeypatch):
        """Test handling a task that failed with 'not found' error."""
        # First create a real task to get a valid task ID
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=json",
        )
        assert response.status_code == 200
        task_data = response.json()
        task_id = task_data["id"]

        # Mock the task manager get_task_info to return a not found error
        from tmt.utils import GeneralError

        error = GeneralError("Test '/nonexistent/test' not found")

        def mock_get_task_info(tid):
            return {
                "id": tid,
                "status": "FAILURE",
                "error": str(error),
                "result": None,
            }

        monkeypatch.setattr(
            "tmt_web.utils.task_manager.task_manager.get_task_info", mock_get_task_info
        )

        # Now try to get the result, which should trigger a 404 error
        response = client.get(f"/?task-id={task_id}&format=json")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_general_error_handler_500(self, client, monkeypatch):
        """Test the general error handler for unhandled errors (500 status code)."""
        from tmt.utils import GeneralError

        # Test generic error (should be 500)
        def raise_generic_error(*args, **kwargs):
            raise GeneralError("Some unhandled generic error")

        # Mock the _validate_parameters function to raise the error
        monkeypatch.setattr("tmt_web.api._validate_parameters", raise_generic_error)

        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke"
        )
        assert response.status_code == 500
        assert "Some unhandled generic error" in response.json()["detail"]

    def test_validate_parameters_conditions(self, client):
        """Test the actual validation conditions in _validate_parameters function."""
        # Test test_url provided without test_name
        response = client.get("/?test-url=https://github.com/teemtee/tmt")
        assert response.status_code == 400
        assert "Both test-url and test-name must be provided together" in response.json()["detail"]

        # Test test_name provided without test_url
        response = client.get("/?test-name=/tests/core/smoke")
        assert response.status_code == 400
        assert "Both test-url and test-name must be provided together" in response.json()["detail"]

        # Test plan_url provided without plan_name
        response = client.get("/?plan-url=https://github.com/teemtee/tmt")
        assert response.status_code == 400
        assert "Both plan-url and plan-name must be provided together" in response.json()["detail"]

        # Test plan_name provided without plan_url
        response = client.get("/?plan-name=/plans/features/basic")
        assert response.status_code == 400
        assert "Both plan-url and plan-name must be provided together" in response.json()["detail"]

        # Test no parameters provided (should redirect to docs)
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"

        # Test with invalid parameter names (none of the recognized parameters)
        response = client.get("/?invalid-param=value")
        assert response.status_code == 400
        assert (
            "At least one of test or plan parameters must be provided" in response.json()["detail"]
        )

    def test_invalid_parameter_combination(self, client, monkeypatch):
        """Test the error for invalid combination of test and plan parameters."""
        from tmt.utils import GeneralError

        # Since we're testing asynchronous behavior, we need to mock the API's _validate_parameters
        # function instead, which is called before service.main
        def simulate_invalid_combination(*args, **kwargs):
            raise GeneralError("Invalid combination of test and plan parameters")

        monkeypatch.setattr("tmt_web.api._validate_parameters", simulate_invalid_combination)

        response = client.get(
            "/?type=invalid&test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke"
        )
        assert response.status_code == 400
        assert "Invalid combination" in response.json()["detail"]
