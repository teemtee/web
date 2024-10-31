import logging
from unittest.mock import Mock

import pytest
import tmt
from jinja2 import TemplateNotFound
from tmt.utils import GeneralError

from tmt_web.generators import html_generator


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


@pytest.fixture
def test_obj(logger):
    return tmt.Tree(logger=logger).tests(names=["/tests/data/sample_test"])[0]


@pytest.fixture
def plan_obj(logger):
    return tmt.Tree(logger=logger).plans(names=["/tests/data/sample_plan"])[0]


class TestHtmlGenerator:
    """Test HTML generation for tests, plans, and status pages."""

    def test_generate_test_html(self, test_obj, logger):
        """Test generating HTML for a test object."""
        data = html_generator.generate_html_page(test_obj, logger)

        # Check basic structure
        assert '<!DOCTYPE html>' in data
        assert '<html lang="en">' in data
        assert f'<title>{test_obj.name}</title>' in data

        # Check content
        assert f'<h1>{test_obj.name}</h1>' in data
        assert f'<p>Name: {test_obj.name}</p>' in data
        assert test_obj.summary in data

    def test_generate_testplan_html(self, test_obj, plan_obj, logger):
        """Test generating HTML for combined test and plan view."""
        data = html_generator.generate_testplan_html_page(test_obj, plan_obj, logger)

        # Check basic structure
        assert '<!DOCTYPE html>' in data
        assert '<html lang="en">' in data
        assert 'Test and Plan Information' in data

        # Check test content
        assert 'Test Information' in data
        assert f'<p>Name: {test_obj.name}</p>' in data
        assert test_obj.summary in data

        # Check plan content
        assert 'Plan Information' in data
        assert f'<p>Name: {plan_obj.name}</p>' in data
        assert plan_obj.summary in data

    def test_generate_status_callback_pending(self, logger):
        """Test status callback page for pending task."""
        result = Mock(status="PENDING", result=None)
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(result, callback_url, logger)

        assert '<!DOCTYPE html>' in data
        assert '<h1>Processing...</h1>' in data
        assert callback_url in data
        assert 'Please wait...' in data
        assert 'setTimeout' in data  # Check for auto-refresh script
        assert 'window.location.href' in data  # Check for proper redirect

    def test_generate_status_callback_retrying(self, logger):
        """Test status callback page for retrying task."""
        result = Mock(status="RETRYING", result=None)
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(result, callback_url, logger)

        assert '<!DOCTYPE html>' in data
        assert '<h1>Retrying...</h1>' in data
        assert callback_url in data
        assert 'Task is being retried' in data
        assert 'window.location.href' in data  # Check for proper redirect

    def test_generate_status_callback_success(self, logger):
        """Test status callback page for successful task."""
        html_result = "<div>Test Result</div>"
        result = Mock(status="SUCCESS", result=html_result)
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(result, callback_url, logger)

        assert '<!DOCTYPE html>' in data
        assert html_result in data  # HTML should be included directly
        assert 'Status:' not in data  # Success case shows only the result

    def test_generate_status_callback_failure(self, logger):
        """Test status callback page for failed task."""
        error_msg = "Test failed: Something went wrong"
        result = Mock(status="FAILURE", result=error_msg)
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(result, callback_url, logger)

        assert '<!DOCTYPE html>' in data
        assert '<h1>Task Failed</h1>' in data
        assert 'Status: FAILURE' in data
        assert f'Error: {error_msg}' in data
        assert 'Refresh Status' in data

    def test_generate_status_callback_unknown(self, logger):
        """Test status callback page for unknown status."""
        result = Mock(status="UNKNOWN", result="Some result")
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(result, callback_url, logger)

        assert '<!DOCTYPE html>' in data
        assert '<h1>Task Status</h1>' in data
        assert 'Status: UNKNOWN' in data
        assert 'Result: Some result' in data
        assert 'Refresh Status' in data

    def test_missing_template(self, logger, monkeypatch):
        """Test handling of missing template."""
        def mock_get_template(*args):
            raise TemplateNotFound("missing.html.j2")

        monkeypatch.setattr(html_generator.env, 'get_template', mock_get_template)

        with pytest.raises(GeneralError) as exc:
            html_generator._render_template("missing.html.j2", logger)
        assert "Template 'missing.html.j2' not found" in str(exc.value)
        assert str(html_generator.TEMPLATE_DIR) in str(exc.value)

    def test_template_render_error(self, logger, monkeypatch):
        """Test handling of template rendering errors."""
        def mock_render(*args, **kwargs):
            raise Exception("Render failed")

        template = html_generator.env.get_template("testorplan.html.j2")
        monkeypatch.setattr(template, 'render', mock_render)
        monkeypatch.setattr(html_generator.env, 'get_template', lambda *args: template)

        with pytest.raises(GeneralError) as exc:
            html_generator._render_template("testorplan.html.j2", logger)
        assert "Failed to render template" in str(exc.value)
        assert "testorplan.html.j2" in str(exc.value)
