import logging

import tmt

from src.generators import html_generator


class TestHtmlGenerator:
    def test_generate_test_html(self):
        logger = tmt.Logger(logging.Logger("tmt-logger"))
        test = tmt.Tree(logger=logger).tests(names=["/tests/objects/sample_test"])[0]
        data = html_generator.generate_test_html_page(test, logger)
        assert 'name: /tests/objects/sample_test<br>' in data
