import logging

import pytest
import tmt
from tmt.utils import GeneralError, yaml_to_dict

from tmt_web.generators import yaml_generator
from tmt_web.generators.json_generator import CombinedTestPlanModel, FmfIdModel


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
    """Test YAML generation for tests and plans."""

    def test_generate_test_yaml(self, test_obj, logger):
        """Test generating YAML for a test object."""
        data = yaml_generator.generate_test_yaml(test_obj, logger)
        parsed = yaml_to_dict(data)

        # Check content
        assert parsed["name"] == "/tests/data/sample_test"
        assert parsed["summary"] == "Concise summary describing what the test does"
        assert parsed["url"] == test_obj.web_link()

        # Check fmf-id structure
        assert isinstance(parsed["fmf-id"], dict)
        assert parsed["fmf-id"]["name"] == test_obj.fmf_id.name
        assert parsed["fmf-id"]["url"] == test_obj.fmf_id.url

        # Check YAML formatting
        assert "name: " in data
        assert "summary: " in data
        assert "fmf-id:" in data

    def test_generate_plan_yaml(self, plan_obj, logger):
        """Test generating YAML for a plan object."""
        data = yaml_generator.generate_plan_yaml(plan_obj, logger)
        parsed = yaml_to_dict(data)

        # Check content
        assert parsed["name"] == "/tests/data/sample_plan"
        assert parsed["url"] == plan_obj.web_link()

        # Check fmf-id structure
        assert isinstance(parsed["fmf-id"], dict)
        assert parsed["fmf-id"]["name"] == plan_obj.fmf_id.name
        assert parsed["fmf-id"]["url"] == plan_obj.fmf_id.url

    def test_generate_testplan_yaml(self, test_obj, plan_obj, logger):
        """Test generating YAML for combined test and plan."""
        data = yaml_generator.generate_testplan_yaml(test_obj, plan_obj, logger)
        parsed = yaml_to_dict(data)

        model = CombinedTestPlanModel.model_validate(parsed)

        # Check test object
        assert model.test.name == "/tests/data/sample_test"
        assert isinstance(model.test.fmf_id, FmfIdModel)

        # Check plan object
        assert model.plan.name == "/tests/data/sample_plan"
        assert isinstance(model.plan.fmf_id, FmfIdModel)

    def test_yaml_serialization_error(self, test_obj, logger, monkeypatch):
        """Test error handling when YAML serialization fails."""
        def mock_dict_to_yaml(*args, **kwargs):
            raise ValueError("YAML serialization failed")

        monkeypatch.setattr(yaml_generator, 'dict_to_yaml', mock_dict_to_yaml)

        with pytest.raises(GeneralError) as exc:
            yaml_generator.generate_test_yaml(test_obj, logger)
        assert "Failed to generate YAML output" in str(exc.value)
