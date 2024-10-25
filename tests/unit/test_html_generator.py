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
    def test_generate_test_html(self, test_obj, logger):
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
        result = Mock(status="PENDING", result=None)
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(result, callback_url, logger)

        assert '<!DOCTYPE html>' in data
        assert '<h1>Processing...</h1>' in data
        assert callback_url in data
        assert 'Please try again in a few seconds' in data

    def test_generate_status_callback_success(self, logger):
        result = Mock(status="SUCCESS", result="Test completed")
        callback_url = "http://example.com/status"

        data = html_generator.generate_status_callback(result, callback_url, logger)

        assert '<!DOCTYPE html>' in data
        assert '<h1>Task Status</h1>' in data
        assert 'Status: SUCCESS' in data
        assert 'Result: Test completed' in data

    def test_missing_template(self, logger, monkeypatch):
        def mock_get_template(*args):
            raise TemplateNotFound("missing.html.j2")

        monkeypatch.setattr(html_generator.env, 'get_template', mock_get_template)

        with pytest.raises(GeneralError) as exc:
            html_generator._render_template("missing.html.j2", logger)
        assert "Template 'missing.html.j2' not found" in str(exc.value)

    def test_template_render_error(self, logger, monkeypatch):
        def mock_render(*args, **kwargs):
            raise Exception("Render failed")

        template = html_generator.env.get_template("testorplan.html.j2")
        monkeypatch.setattr(template, 'render', mock_render)
        monkeypatch.setattr(html_generator.env, 'get_template', lambda *args: template)

        with pytest.raises(GeneralError) as exc:
            html_generator._render_template("testorplan.html.j2", logger)
        assert "Failed to render template" in str(exc.value)
