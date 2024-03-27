import time

import pytest
import tmt
import logging

from src.utils import git_handler


class TestUtils:
    logger = tmt.Logger(logging.Logger("tmt-logger"))

    def test_clear_tmp_dir(self):
        git_handler.clear_tmp_dir(self.logger)

    def test_get_path_to_repository(self):
        assert git_handler.get_path_to_repository("https://github.com/teemtee/tmt").exists()

    def test_check_if_repository_exists(self):
        assert git_handler.check_if_repository_exists("https://github.com/teemtee/tmt")

    def test_clone_repository(self):
        # Give the script enough time for the repository to be deleted
        while git_handler.check_if_repository_exists("https://github.com/teemtee/tmt") is True:
            git_handler.clear_tmp_dir(self.logger)
            time.sleep(1)
        git_handler.clone_repository("https://github.com/teemtee/tmt", logger=self.logger)
        with pytest.raises(FileExistsError):
            git_handler.clone_repository("https://github.com/teemtee/tmt", logger=self.logger)

