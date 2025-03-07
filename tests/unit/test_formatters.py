"""Unit tests for the formatters module."""

import json

from tmt_web.formatters import deserialize_data, serialize_data
from tmt_web.models import TestData, TestPlanData


def test_serialize_data_test_data():
    """Test serializing TestData."""
    test_data = TestData(
        name="/tests/core/smoke",
        summary="Just a basic smoke test",
        contact=["Petr Šplíchal <psplicha@redhat.com>"],
        framework="shell",
        fmf_id={
            "name": "/tests/core/smoke",
            "url": "https://github.com/teemtee/tmt/tree/main/tests/core/smoke/main.fmf",
            "path": None,
            "ref": "main",
        },
    )

    # Test serialization
    serialized = serialize_data(test_data)
    assert isinstance(serialized, str)

    # Verify it's valid JSON
    parsed = json.loads(serialized)
    assert parsed["name"] == "/tests/core/smoke"
    assert "fmf-id" in parsed  # Check for hyphenated field name in the output


def test_deserialize_data_test_plan_data():
    """Test deserializing to TestPlanData."""
    serialized = json.dumps(
        {
            "test": {
                "name": "/tests/core/smoke",
                "summary": "Just a basic smoke test",
                "framework": "shell",
            },
            "plan": {"name": "/plans/basic", "summary": "Basic plan"},
        }
    )

    # Should detect it's a TestPlanData
    result = deserialize_data(serialized)
    assert isinstance(result, TestPlanData)
    assert result.test.name == "/tests/core/smoke"
    assert result.plan.name == "/plans/basic"
