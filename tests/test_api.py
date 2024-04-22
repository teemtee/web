import os
import time

import pytest
from src.api import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    return TestClient(app)


class TestApi:
    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ["USE_CELERY"] = "false"
        os.environ["TMP_DIR_PATH"] = "../.tmp/"

    def test_basic_test_request(self, client):
        # ?test_url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke")
        data = response.content.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data

    def test_basic_plan_request(self, client):
        # ?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan
        response = client.get("/?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan")
        data = response.content.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_basic_testplan_request(self, client):
        # ?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&
        # ?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke&"
                              "?plan-url=https://github.com/teemtee/tmt&plan-name=/plans/features/basic&type=plan")
        data = response.content.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_invalid_test_arguments(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt")
        data = response.content.decode("utf-8")
        assert "Invalid arguments!" in data
        response = client.get("/?test-name=/tests/core/smoke")
        data = response.content.decode("utf-8")
        assert "Invalid arguments!" in data

    def test_invalid_plan_arguments(self, client):
        response = client.get("/?plan-url=https://github.com/teemtee/tmt")
        data = response.content.decode("utf-8")
        assert "Invalid arguments!" in data
        response = client.get("/?plan-name=/plans/features/basic")
        data = response.content.decode("utf-8")
        assert "Invalid arguments!" in data

    def test_invalid_testplan_arguments(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&plan-url=https://github.com/teemtee/tmt&"
                              "plan-name=/plans/features/basic")
        data = response.content.decode("utf-8")
        assert "Invalid arguments!" in data

    def test_invalid_argument_names(self, client):
        response = client.get("/?test_urlur=https://github.com/teemtee/tmt&test_nn=/tests/core/smoke")
        assert response.status_code == 500


class TestCelery:
    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ["USE_CELERY"] = "true"

    def test_basic_test_request(self, client):
        response = client.get("/?test-url=https://github.com/teemtee/tmt&test-name=/tests/core/smoke")
        json_data = response.json()
        while True:
            if json_data["status"] == "PENDING":
                response = client.get("/status?task_id=" + json_data["id"])
                json_data = response.json()
                time.sleep(0.1)
            elif json_data["status"] == "SUCCESS":
                result = json_data["result"]
                assert "500" not in result
                assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in result
                break
            elif json_data["status"] == "FAILURE":
                assert False
            else:
                assert False
