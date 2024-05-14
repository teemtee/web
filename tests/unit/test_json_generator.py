import logging

import tmt

from src.generators import json_generator


class TestJsonGenerator:
    def test_generate_test_json(self):
        logger = tmt.Logger(logging.Logger("tmt-logger"))
        test = tmt.Tree(logger=logger).tests(names=["/tests/objects/sample_test"])[0]
        data = json_generator.generate_test_json(test, logger)
        assert '"name": "/tests/objects/sample_test"' in data

    def test_generate_plan_json(self):
        logger = tmt.Logger(logging.Logger("tmt-logger"))
        plan = tmt.Tree(logger=logger).plans(names=["/tests/objects/sample_plan"])[0]
        data = json_generator.generate_plan_json(plan, logger)
        assert '"name": "/tests/objects/sample_plan"' in data

    def test_generate_testplan_json(self):
        logger = tmt.Logger(logging.Logger("tmt-logger"))
        test = tmt.Tree(logger=logger).tests(names=["/tests/objects/sample_test"])[0]
        plan = tmt.Tree(logger=logger).plans(names=["/tests/objects/sample_plan"])[0]
        data = json_generator.generate_testplan_json(test, plan, logger)
        assert '"name": "/tests/objects/sample_test"' in data
        assert '"name": "/tests/objects/sample_plan"' in data
