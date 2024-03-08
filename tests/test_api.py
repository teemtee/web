import pytest
from src.api import app


@pytest.fixture()
def client():
    return app.test_client()


class TestApi:
    def test_basic_test_request(self, client):
        # ?test_url=https://github.com/teemtee/tmt&test_name=/tests/core/smoke
        response = client.get("/", query_string={"test_url": "https://github.com/teemtee/tmt",
                                                 "test_name": "/tests/core/smoke"})
        data = response.data.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data

    def test_basic_plan_request(self, client):
        # ?plan_url=https://github.com/teemtee/tmt&plan_name=/plans/features/basic&type=plan
        response = client.get("/", query_string={"plan_url": "https://github.com/teemtee/tmt",
                                                 "plan_name": "/plans/features/basic"})
        data = response.data.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_basic_testplan_request(self, client):
        # ?test_url=https://github.com/teemtee/tmt&test_name=/tests/core/smoke&
        # ?plan_url=https://github.com/teemtee/tmt&plan_name=/plans/features/basic&type=plan
        response = client.get("/", query_string={"test_url": "https://github.com/teemtee/tmt",
                                                 "test_name": "/tests/core/smoke",
                                                 "plan_url": "https://github.com/teemtee/tmt",
                                                 "plan_name": "/plans/features/basic"})
        data = response.data.decode("utf-8")
        print(data)
        assert "500" not in data
        assert "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf" in data
        assert "https://github.com/teemtee/tmt/tree/main/plans/features/basic.fmf" in data

    def test_invalid_test_arguments(self, client):
        response = client.get("/", query_string={"test_url": "https://github.com/teemtee/tmt",
                                                 "test_name": None})
        data = response.data.decode("utf-8")
        assert "Invalid arguments!" in data
        response = client.get("/", query_string={"test_url": None,
                                                 "test_name": "/tests/core/smoke"})
        data = response.data.decode("utf-8")
        assert "Invalid arguments!" in data

    def test_invalid_plan_arguments(self, client):
        response = client.get("/", query_string={"plan_url": "https://github.com/teemtee/tmt",
                                                 "plan_name": None})
        data = response.data.decode("utf-8")
        assert "Invalid arguments!" in data
        response = client.get("/", query_string={"plan_url": None,
                                                 "plan_name": "/plans/features/basic"})
        data = response.data.decode("utf-8")
        assert "Invalid arguments!" in data

    def test_invalid_testplan_arguments(self, client):
        response = client.get("/", query_string={"test_url": "https://github.com/teemtee/tmt",
                                                 "test_name": None,
                                                 "plan_url": "https://github.com/teemtee/tmt",
                                                 "plan_name": "/plans/features/basic"})
        data = response.data.decode("utf-8")
        assert "Invalid arguments!" in data

    def test_invalid_argument_names(self, client):
        response = client.get("/", query_string={"test_urlurl": "https://github.com/teemtee/tmt",
                                                 "test_nn": "/tests/core/smoke"})
        assert response.status_code == 500
