import json
import logging

import pytest
import tmt
from tmt.utils import GeneralError

from tmt_web.generators import json_generator


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


@pytest.fixture
def test_obj(logger):
    return tmt.Tree(logger=logger).tests(names=["/tests/data/sample_test"])[0]


@pytest.fixture
def plan_obj(logger):
    return tmt.Tree(logger=logger).plans(names=["/tests/data/sample_plan"])[0]


class TestJsonGenerator:
    def test_generate_test_json(self, test_obj, logger):
        data = json_generator.generate_test_json(test_obj, logger)
        parsed = json.loads(data)

        # Check basic structure
        assert isinstance(parsed, dict)
        assert parsed["name"] == "/tests/data/sample_test"
        assert parsed["summary"] == "Concise summary describing what the test does"

        # Check types
        assert isinstance(parsed["contact"], list)
        assert isinstance(parsed["tag"], list)
        assert isinstance(parsed.get("summary"), str | type(None))
        assert isinstance(parsed.get("description"), str | type(None))

        # Check fmf-id structure
        fmf_id = parsed["fmf-id"]
        assert isinstance(fmf_id, dict)
        assert isinstance(fmf_id["name"], str)
        assert isinstance(fmf_id.get("url"), str | type(None))
        assert isinstance(fmf_id.get("path"), str | type(None))
        assert isinstance(fmf_id.get("ref"), str | type(None))

    def test_generate_plan_json(self, plan_obj, logger):
        data = json_generator.generate_plan_json(plan_obj, logger)
        parsed = json.loads(data)

        # Check basic structure
        assert isinstance(parsed, dict)
        assert parsed["name"] == "/tests/data/sample_plan"

        # Check types
        assert isinstance(parsed["contact"], list)
        assert isinstance(parsed["tag"], list)
        assert isinstance(parsed.get("summary"), str | type(None))
        assert isinstance(parsed.get("description"), str | type(None))

        # Check fmf-id structure
        fmf_id = parsed["fmf-id"]
        assert isinstance(fmf_id, dict)
        assert isinstance(fmf_id["name"], str)
        assert isinstance(fmf_id.get("url"), str | type(None))
        assert isinstance(fmf_id.get("path"), str | type(None))
        assert isinstance(fmf_id.get("ref"), str | type(None))

    def test_generate_testplan_json(self, test_obj, plan_obj, logger):
        data = json_generator.generate_testplan_json(test_obj, plan_obj, logger)
        parsed = json.loads(data)

        # Check structure
        assert isinstance(parsed, dict)
        assert "test" in parsed
        assert "plan" in parsed

        # Check test object
        test_data = parsed["test"]
        assert test_data["name"] == "/tests/data/sample_test"
        assert isinstance(test_data["fmf-id"], dict)

        # Check plan object
        plan_data = parsed["plan"]
        assert plan_data["name"] == "/tests/data/sample_plan"
        assert isinstance(plan_data["fmf-id"], dict)

    def test_json_serialization_error(self, test_obj, logger, monkeypatch):
        """Test error handling when JSON serialization fails"""
        class UnserializableObject:
            pass

        def mock_create_data(*args, **kwargs):
            return {"bad_field": UnserializableObject()}

        monkeypatch.setattr(json_generator, '_create_json_data', mock_create_data)

        with pytest.raises(GeneralError) as exc:
            json_generator.generate_test_json(test_obj, logger)
        assert "Failed to generate JSON output" in str(exc.value)

    def test_create_json_data_structure(self, test_obj, logger):
        data = json_generator._create_json_data(test_obj, logger)

        # Verify it matches our TypedDict structure
        assert isinstance(data, dict)
        assert "name" in data
        assert "contact" in data
        assert "tag" in data
        assert "fmf-id" in data

        # Verify fmf-id structure
        fmf_id = data["fmf-id"]
        assert "name" in fmf_id
        assert "url" in fmf_id
        assert "path" in fmf_id
        assert "ref" in fmf_id
