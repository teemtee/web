import logging

import tmt

from tmt_web.generators import yaml_generator


class TestYamlGenerator:
    def test_generate_test_yaml(self):
        logger = tmt.Logger(logging.getLogger("tmt-logger"))
        test = tmt.Tree(logger=logger).tests(names=["/tests/objects/sample_test"])[0]
        data = yaml_generator.generate_test_yaml(test, logger)
        assert 'name: /tests/objects/sample_test' in data

    def test_generate_plan_yaml(self):
        logger = tmt.Logger(logging.getLogger("tmt-logger"))
        plan = tmt.Tree(logger=logger).plans(names=["/tests/objects/sample_plan"])[0]
        data = yaml_generator.generate_plan_yaml(plan, logger)
        assert 'name: /tests/objects/sample_plan' in data

    def test_generate_testplan_yaml(self):
        logger = tmt.Logger(logging.getLogger("tmt-logger"))
        test = tmt.Tree(logger=logger).tests(names=["/tests/objects/sample_test"])[0]
        plan = tmt.Tree(logger=logger).plans(names=["/tests/objects/sample_plan"])[0]
        data = yaml_generator.generate_testplan_yaml(test, plan, logger)
        assert 'name: /tests/objects/sample_test' in data
        assert 'name: /tests/objects/sample_plan' in data
