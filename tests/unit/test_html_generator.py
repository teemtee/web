"""Unit tests for HTML generator."""

import logging

import pytest
import tmt
from jinja2 import TemplateNotFound
from tmt.utils import GeneralError

from tmt_web.generators import html_generator
from tmt_web.models import FmfIdData, PlanData, TestData


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


@pytest.fixture
def test_data():
    """Create a test TestData object."""
    return TestData(
        name="sample-test",
        summary="Sample test summary",
        description="Sample test description",
        contact=["Test Contact <test@example.com>"],
        component=["component1"],
        enabled=True,
        environment={"KEY": "value"},
        duration="15m",
        framework="shell",
        manual=False,
        path="/path/to/test",
        tier="1",
        order=50,
        id="test-123",
        link=[{"name": "issue", "url": "https://example.com/issue/123"}],
        tag=["tag1", "tag2"],
        fmf_id=FmfIdData(
            name="test",
            url="https://example.com/test",
            path="/path/to/test",
            ref="main",
        ),
    )


@pytest.fixture
def plan_data():
    """Create a test PlanData object."""
    return PlanData(
        name="sample-plan",
        summary="Sample plan summary",
        description="Sample plan description",
        prepare=[{"how": "shell", "script": "prepare.sh"}],
        execute=[{"how": "tmt"}],
        finish=[{"how": "shell", "script": "cleanup.sh"}],
        discover={"how": "fmf"},
        provision={"how": "local"},
        report={"how": "html"},
        enabled=True,
        path="/path/to/plan",
        order=100,
        id="plan-456",
        link=[{"name": "docs", "url": "https://example.com/docs"}],
        tag=["plan-tag1", "plan-tag2"],
        fmf_id=FmfIdData(
            name="plan",
            url="https://example.com/plan",
            path="/path/to/plan",
            ref="main",
        ),
    )


class TestHtmlGenerator:
    """Test HTML generation for tests, plans, and status pages."""

    def test_generate_test_html(self, test_data, logger):
        """Test generating HTML for a test object."""
        data = html_generator.generate_html_page(test_data, logger)

        # Check basic structure
        assert "<!DOCTYPE html>" in data
        assert '<html lang="en">' in data
        assert f"<title>{test_data.name}</title>" in data

        # Check content
        assert f"<h1>{test_data.name}</h1>" in data

        # Name should not be shown as metadata since it's now the heading
        assert f"<p><strong>Name:</strong> {test_data.name}</p>" not in data

        # Also make sure fmf_id.name is not displayed
        assert f"<p><strong>Name:</strong> {test_data.fmf_id.name}</p>" not in data
        assert test_data.summary in data

    def test_generate_testplan_html(self, test_data, plan_data, logger):
        """Test generating HTML for combined test and plan view."""
        data = html_generator.generate_testplan_html_page(test_data, plan_data, logger)

        # Check basic structure
        assert "<!DOCTYPE html>" in data
        assert '<html lang="en">' in data
        assert "Test and Plan Information" in data

        # Check test content
        assert f"<h1>{test_data.name}</h1>" in data
        assert f"<p><strong>Name:</strong> {test_data.name}</p>" not in data

        # Also make sure fmf_id.name is not displayed
        assert f"<p><strong>Name:</strong> {test_data.fmf_id.name}</p>" not in data
        assert test_data.summary in data

        # Check plan content
        assert f"<h1>{plan_data.name}</h1>" in data
        assert f"<p><strong>Name:</strong> {plan_data.name}</p>" not in data
        assert plan_data.summary in data

        # Also make sure fmf_id.name is not displayed
        assert f"<p><strong>Name:</strong> {plan_data.fmf_id.name}</p>" not in data

    def test_generate_status_callback_pending(self, logger):
        """Test status callback page for pending task."""
        task_id = "123-abc"
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(
            task_id, callback_url, logger, status="PENDING", result=None
        )

        assert "<!DOCTYPE html>" in data
        assert "<h1>Processing...</h1>" in data
        assert callback_url in data
        assert "Please wait..." in data
        assert "setTimeout" in data  # Check for auto-refresh script
        assert "window.location.href" in data  # Check for proper redirect

    def test_generate_status_callback_retrying(self, logger):
        """Test status callback page for retrying task."""
        task_id = "123-abc"
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(
            task_id, callback_url, logger, status="RETRYING", result=None
        )

        assert "<!DOCTYPE html>" in data
        assert "<h1>Retrying...</h1>" in data
        assert callback_url in data
        assert "Task is being retried" in data
        assert "window.location.href" in data  # Check for proper redirect

    def test_generate_status_callback_success(self, logger):
        """Test status callback page for successful task."""
        task_id = "123-abc"
        html_result = "<div>Test Result</div>"
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(
            task_id, callback_url, logger, status="SUCCESS", result=html_result
        )

        assert "<!DOCTYPE html>" in data
        assert html_result in data  # HTML should be included directly
        assert "Status:" not in data  # Success case shows only the result

    def test_generate_status_callback_failure(self, logger):
        """Test status callback page for failed task."""
        task_id = "123-abc"
        error_msg = "Test failed: Something went wrong"
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(
            task_id, callback_url, logger, status="FAILURE", result=error_msg
        )

        assert "<!DOCTYPE html>" in data
        assert "<h1>Task Failed</h1>" in data
        assert "Status: FAILURE" in data
        assert f"Error: {error_msg}" in data
        assert "Refresh Status" in data

    def test_generate_status_callback_unknown(self, logger):
        """Test status callback page for unknown status."""
        task_id = "123-abc"
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(
            task_id, callback_url, logger, status="UNKNOWN", result="Some result"
        )

        assert "<!DOCTYPE html>" in data
        assert "<h1>Task Status</h1>" in data
        assert "Status: UNKNOWN" in data
        assert "Result: Some result" in data
        assert "Refresh Status" in data

    def test_missing_template(self, logger, monkeypatch):
        """Test handling of missing template."""

        def mock_get_template(*args):
            raise TemplateNotFound("missing.html.j2")

        monkeypatch.setattr(html_generator.env, "get_template", mock_get_template)

        with pytest.raises(GeneralError) as exc:
            html_generator._render_template("missing.html.j2", logger)
        assert "Template 'missing.html.j2' not found" in str(exc.value)
        assert str(html_generator.TEMPLATE_DIR) in str(exc.value)

    def test_template_render_error(self, logger, monkeypatch):
        """Test handling of template rendering errors."""

        def mock_render(*args, **kwargs):
            raise Exception("Render failed")

        template = html_generator.env.get_template("testorplan.html.j2")
        monkeypatch.setattr(template, "render", mock_render)
        monkeypatch.setattr(html_generator.env, "get_template", lambda *args: template)

        with pytest.raises(GeneralError) as exc:
            html_generator._render_template("testorplan.html.j2", logger)
        assert "Failed to render template" in str(exc.value)
        assert "testorplan.html.j2" in str(exc.value)

    def test_multiline_description_rendering(self, logger):
        """Test that multiline descriptions are rendered correctly with line breaks preserved."""
        # Create test data with multiline description
        multiline_description = (
            "First line of description\n\nSecond line after empty line\nThird line\n\nFourth line"
        )
        test_data = TestData(
            name="multiline-test",
            summary="Test with multiline description",
            description=multiline_description,
            contact=["Test Contact <test@example.com>"],
            component=["component1"],
            enabled=True,
            environment={"KEY": "value"},
            duration="15m",
            framework="shell",
            manual=False,
            path="/path/to/test",
            tier="1",
            order=50,
            id="test-multiline",
            tag=["tag1"],
            fmf_id=FmfIdData(
                name="test",
                url="https://example.com/test",
                path="/path/to/test",
                ref="main",
            ),
        )

        data = html_generator.generate_html_page(test_data, logger)

        # Check that the description is wrapped in proper HTML structure
        assert '<div class="description">' in data
        assert '<pre class="description-text">' in data
        assert "</pre>" in data
        assert "</div>" in data

        # Check that the multiline content is preserved
        assert "First line of description" in data
        assert "Second line after empty line" in data
        assert "Third line" in data
        assert "Fourth line" in data
