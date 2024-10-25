import os
import time

import pytest
from fastapi.testclient import TestClient

from tmt_web.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestApi:
    """
    This class tests the behaviour of the API directly
    """
    @pytest.fixture(autouse=True)
    def _setup(self):
        os.environ["USE_CELERY"] = "false"

    def test_basic_test_request_json(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&test-ref=main")
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data

    def test_basic_test_request_json_with_path(self, client):
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt.git"
            "&test-name=/test/shell/weird"
            "&test-path=/tests/execute/basic/data"
            "&test-ref=main")
        data = response.content.decode("utf-8")
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/execute/basic/data/test.fmf" in data

    def test_basic_test_request_html(self, client):
        response = client.get(
            "/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&test-ref=main&format=html")
        data = response.content.decode("utf-8")
        print(data)
        assert "500" not in data
        assert '<html lang="en">' in data

    def test_basic_test_request_yaml(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&format=yaml")
        data = response.content.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "url: https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data

    def test_basic_plan_request(self, client):
        response = client.get("/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan")
        data = response.content.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_basic_testplan_request(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&"
                              "plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan")
        data = response.content.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_invalid_test_arguments(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt")
        data = response.content.decode("utf-8")
        assert "Both test-url and test-name must be provided together" in data
        response = client.get("/?test-name=/tests/core/smoke")
        data = response.content.decode("utf-8")
        assert "Both test-url and test-name must be provided together" in data

    def test_invalid_plan_arguments(self, client):
        response = client.get("/?plan-url=https://github.com/teemtee/tmt")
        data = response.content.decode("utf-8")
        assert "Both plan-url and plan-name must be provided together" in data
        response = client.get("/?plan-name=/plans/features/basic")
        data = response.content.decode("utf-8")
        assert "Both plan-url and plan-name must be provided together" in data

    def test_invalid_testplan_arguments(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&plan-url=https://github.com/teemtee/tmt&"
                              "plan-name=/plans/features/basic")
        data = response.content.decode("utf-8")
        assert "Both test-url and test-name must be provided together" in data

    def test_invalid_argument_names(self, client):
        response = client.get("/?test_urlur=https://github.com/teemtee/tmt&test_nn=/tests/core/smoke")
        data = response.content.decode("utf-8")
        assert response.status_code == 500
        assert "At least one of test or plan parameters must be provided" in data


class TestCelery:
    """
    This class tests the API with the Celery instance
    """
    @pytest.fixture(autouse=True)
    def _setup(self):
        os.environ["USE_CELERY"] = "true"

    def test_basic_test_request(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke")
        json_data = response.json()
        while True:
            if json_data["status"] == "PENDING":
                response = client.get("/status?task-id=" + json_data["id"])
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
