import os
import time

import pytest
from fastapi.testclient import TestClient

from tmt_web.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestApi:
    """This class tests the behaviour of the API directly."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        os.environ["USE_CELERY"] = "false"

    def test_root_empty_redirects_to_docs(self, client):
        """Test that empty root path redirects to docs."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"

    def test_basic_test_request_json(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&test-ref=main")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data

    def test_basic_test_request_json_with_path(self, client):
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt.git"
            "&test-name=/test/shell/weird"
            "&test-path=/tests/execute/basic/data"
            "&test-ref=main")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/execute/basic/data/test.fmf" in data

    def test_basic_test_request_html(self, client):
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&test-ref=main&format=html")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert '<html lang="en">' in data
        assert "Just a basic smoke test" in data

    def test_basic_test_request_yaml(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=yaml")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "url: https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data

    def test_basic_plan_request(self, client):
        response = client.get("/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_basic_testplan_request(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&"
                              "plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_invalid_test_arguments(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt")
        assert response.status_code == 400
        data = response.content.decode("utf-8")
        assert "Both test-url and test-name must be provided together" in data

        response = client.get("/?test-name=/tests/core/smoke")
        assert response.status_code == 400
        data = response.content.decode("utf-8")
        assert "Both test-url and test-name must be provided together" in data

    def test_invalid_plan_arguments(self, client):
        response = client.get("/?plan-url=https://github.com/teemtee/tmt")
        assert response.status_code == 400
        data = response.content.decode("utf-8")
        assert "Both plan-url and plan-name must be provided together" in data

        response = client.get("/?plan-name=/plans/features/basic")
        assert response.status_code == 400
        data = response.content.decode("utf-8")
        assert "Both plan-url and plan-name must be provided together" in data

    def test_invalid_testplan_arguments(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&plan-url=https://github.com/teemtee/tmt&"
                              "plan-name=/plans/features/basic")
        assert response.status_code == 400
        data = response.content.decode("utf-8")
        assert "Both test-url and test-name must be provided together" in data

    def test_invalid_argument_names(self, client):
        response = client.get("/?test_urlur=https://github.com/teemtee/tmt&test_nn=/tests/core/smoke")
        assert response.status_code == 400
        data = response.content.decode("utf-8")
        assert "At least one of test or plan parameters must be provided" in data

    def test_not_found_errors(self, client):
        """Test that missing tests/plans return 404."""
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/nonexistent/test")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        response = client.get("/?plan-url=https://github.com/teemtee/tmt&plan-name=/nonexistent/plan")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

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
        assert "celery" in data["dependencies"]
        assert "redis" in data["dependencies"]
        # When Celery is disabled, dependencies should be marked as disabled
        assert data["dependencies"]["celery"] == "disabled"
        assert data["dependencies"]["redis"] == "disabled"

        # Check system info
        assert "platform" in data["system"]
        assert "hostname" in data["system"]
        assert "python_implementation" in data["system"]

    def test_health_check_redis_error(self, client, monkeypatch):
        """Test health check when Redis ping fails."""
        # Enable Celery for this test
        os.environ["USE_CELERY"] = "true"

        # Mock Redis ping to fail
        def mock_ping(*args, **kwargs):
            raise Exception("Redis connection failed")

        monkeypatch.setattr("tmt_web.service.main.app.control.ping", mock_ping)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert data["dependencies"]["celery"] == "failed"
        assert data["dependencies"]["redis"] == "failed"


class TestCelery:
    """This class tests the API with the Celery instance."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        os.environ["USE_CELERY"] = "true"

    def test_basic_test_request_json(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke")
        assert response.status_code == 200
        json_data = response.json()
        while True:
            if json_data["status"] == "PENDING":
                response = client.get("/status?task-id=" + json_data["id"])
                assert response.status_code == 200
                json_data = response.json()
                time.sleep(0.1)
            elif json_data["status"] == "SUCCESS":
                result = json_data["result"]
                assert "500" not in result
                assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in result
                break
            elif json_data["status"] == "FAILURE":
                pytest.fail("status = FAILURE: " + json_data["result"])
            else:
                pytest.fail("Unknown status: " + json_data["status"])

    def test_basic_test_request_html(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=html")
        assert response.status_code == 200
        data = response.content.decode("utf-8")
        assert "Processing..." in data
        assert "setTimeout" in data  # Check for auto-refresh script

        # Extract task ID from status callback URL
        task_id = data.split("task-id=")[1].split('"')[0]

        # Poll until complete
        while True:
            response = client.get(f"/status/html?task-id={task_id}")
            assert response.status_code == 200
            data = response.content.decode("utf-8")
            if "Processing..." in data:
                time.sleep(0.1)
                continue
            if "Task Failed" in data:
                pytest.fail("Task failed: " + data)
            else:
                assert "Just a basic smoke test" in data
                break

    def test_basic_test_request_yaml(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=yaml")
        assert response.status_code == 200
        json_data = response.json()
        while True:
            if json_data["status"] == "PENDING":
                response = client.get("/status?task-id=" + json_data["id"])
                assert response.status_code == 200
                json_data = response.json()
                time.sleep(0.1)
            elif json_data["status"] == "SUCCESS":
                result = json_data["result"]
                assert "500" not in result
                assert "url: https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in result
                break
            elif json_data["status"] == "FAILURE":
                pytest.fail("status = FAILURE: " + json_data["result"])
            else:
                pytest.fail("Unknown status: " + json_data["status"])

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
        assert "Status: PENDING" in data

    def test_not_found_with_celery(self, client):
        """Test that missing tests/plans return 404 with Celery."""
        # Initial request creates a task
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/nonexistent/test")
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

    def test_health_check_with_celery(self, client):
        """Test health check endpoint with Celery enabled."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Dependencies should be ok when Celery is enabled and running
        assert data["dependencies"]["celery"] == "ok"
        assert data["dependencies"]["redis"] == "ok"
