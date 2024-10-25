import logging

import pytest
import tmt
from tmt.utils import GeneralError, yaml_to_dict

from tmt_web.generators import yaml_generator


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


@pytest.fixture
def test_obj(logger):
    return tmt.Tree(logger=logger).tests(names=["/tests/data/sample_test"])[0]


@pytest.fixture
def plan_obj(logger):
    return tmt.Tree(logger=logger).plans(names=["/tests/data/sample_plan"])[0]


class TestYamlGenerator:
    def test_generate_test_yaml(self, test_obj, logger):
        data = yaml_generator.generate_test_yaml(test_obj, logger)
        parsed = yaml_to_dict(data)

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

    def test_generate_plan_yaml(self, plan_obj, logger):
        data = yaml_generator.generate_plan_yaml(plan_obj, logger)
        parsed = yaml_to_dict(data)

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

    def test_generate_testplan_yaml(self, test_obj, plan_obj, logger):
        data = yaml_generator.generate_testplan_yaml(test_obj, plan_obj, logger)
        parsed = yaml_to_dict(data)

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

    def test_yaml_serialization_error(self, test_obj, logger, monkeypatch):
        """Test error handling when YAML serialization fails"""
        def mock_dict_to_yaml(*args, **kwargs):
            raise Exception("YAML serialization failed")

        monkeypatch.setattr(yaml_generator, 'dict_to_yaml', mock_dict_to_yaml)

        with pytest.raises(GeneralError) as exc:
            yaml_generator.generate_test_yaml(test_obj, logger)
        assert "Failed to generate YAML output" in str(exc.value)

    def test_mapping_to_dict_cast(self, test_obj, logger, monkeypatch):
        """Test that we properly cast Mapping to dict for dict_to_yaml"""
        calls = []

        def mock_dict_to_yaml(data, **kwargs):
            calls.append(data)
            assert isinstance(data, dict)  # Verify we got a dict
            return "mocked yaml"

        monkeypatch.setattr(yaml_generator, 'dict_to_yaml', mock_dict_to_yaml)
        yaml_generator.generate_test_yaml(test_obj, logger)

        assert len(calls) == 1  # Verify dict_to_yaml was called
        assert isinstance(calls[0], dict)  # Verify we passed a dict
