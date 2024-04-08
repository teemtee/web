import pytest
from src.api import app
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    return TestClient(app)


class TestApi:
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
