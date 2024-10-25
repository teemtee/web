import logging

import pytest
import tmt
from tmt.utils import GeneralError

from tmt_web.generators import json_generator
from tmt_web.generators.json_generator import FmfIdModel, ObjectModel, TestAndPlanModel


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
    """Test JSON generation for tests and plans."""

    def test_generate_test_json(self, test_obj, logger):
        """Test generating JSON for a test object."""
        data = json_generator.generate_test_json(test_obj, logger)
        parsed = ObjectModel.model_validate_json(data)

        # Check content
        assert parsed.name == "/tests/data/sample_test"
        assert parsed.summary == "Concise summary describing what the test does"
        assert parsed.url == test_obj.web_link()

        # Check fmf-id structure
        assert isinstance(parsed.fmf_id, FmfIdModel)
        assert parsed.fmf_id.name == test_obj.fmf_id.name
        assert parsed.fmf_id.url == test_obj.fmf_id.url

    def test_generate_plan_json(self, plan_obj, logger):
        """Test generating JSON for a plan object."""
        data = json_generator.generate_plan_json(plan_obj, logger)
        parsed = ObjectModel.model_validate_json(data)

        # Check content
        assert parsed.name == "/tests/data/sample_plan"
        assert parsed.url == plan_obj.web_link()

        # Check fmf-id structure
        assert isinstance(parsed.fmf_id, FmfIdModel)
        assert parsed.fmf_id.name == plan_obj.fmf_id.name
        assert parsed.fmf_id.url == plan_obj.fmf_id.url

    def test_generate_testplan_json(self, test_obj, plan_obj, logger):
        """Test generating JSON for combined test and plan."""
        data = json_generator.generate_testplan_json(test_obj, plan_obj, logger)
        parsed = TestAndPlanModel.model_validate_json(data)

        # Check test object
        assert parsed.test.name == "/tests/data/sample_test"
        assert isinstance(parsed.test.fmf_id, FmfIdModel)

        # Check plan object
        assert parsed.plan.name == "/tests/data/sample_plan"
        assert isinstance(parsed.plan.fmf_id, FmfIdModel)

    def test_json_serialization_error(self, test_obj, logger, monkeypatch):
        """Test error handling when JSON serialization fails."""
        def mock_model_dump_json(*args, **kwargs):
            raise ValueError("JSON serialization failed")

        monkeypatch.setattr(ObjectModel, 'model_dump_json', mock_model_dump_json)

        with pytest.raises(GeneralError) as exc:
            json_generator.generate_test_json(test_obj, logger)
        assert "Failed to generate JSON output" in str(exc.value)

    def test_fmf_id_model_conversion(self, test_obj):
        """Test FmfIdModel conversion from tmt object."""
        fmf_id_data = FmfIdModel.from_fmf_id(test_obj.fmf_id)
        assert fmf_id_data.name == test_obj.fmf_id.name
        assert fmf_id_data.url == test_obj.fmf_id.url
        assert fmf_id_data.ref == test_obj.fmf_id.ref

        # Test path conversion
        if test_obj.fmf_id.path is not None:
            assert fmf_id_data.path == test_obj.fmf_id.path.as_posix()
        else:
            assert fmf_id_data.path is None

    def test_object_model_conversion(self, test_obj):
        """Test ObjectModel conversion from tmt object."""
        obj_data = ObjectModel.from_tmt_object(test_obj)
        assert obj_data.name == test_obj.name
        assert obj_data.summary == test_obj.summary
        assert obj_data.description == test_obj.description
        assert obj_data.url == test_obj.web_link()
        assert obj_data.ref == test_obj.fmf_id.ref
        assert obj_data.contact == test_obj.contact
        assert obj_data.tag == test_obj.tag
        assert obj_data.tier == test_obj.tier

    def test_field_aliases(self, test_obj, logger):
        """Test that field aliases work correctly."""
        data = json_generator.generate_test_json(test_obj, logger)
        # Check that the JSON uses fmf-id
        assert '"fmf-id":' in data
        # But the model uses fmf_id
        parsed = ObjectModel.model_validate_json(data)
        assert hasattr(parsed, "fmf_id")
