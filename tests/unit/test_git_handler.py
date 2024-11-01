import logging
from pathlib import Path

import pytest
import tmt
from tmt.utils import Command, GeneralError, GitUrlError, RunError

from tmt_web import settings
from tmt_web.utils import git_handler


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


@pytest.fixture
def test_repo_path():
    """Get the test repository path."""
    return (git_handler.ROOT_DIR / settings.CLONE_DIR_PATH).resolve()


@pytest.fixture
def _clean_repo_dir(test_repo_path, logger):
    """Ensure clean repository directory before and after tests."""
    # Clean before test
    git_handler.clear_tmp_dir(logger)

    yield

    # Clean after test
    git_handler.clear_tmp_dir(logger)


class TestGitHandler:
    """Test Git repository handling utilities."""

    TEST_REPO = "https://github.com/teemtee/tmt"
    INVALID_REPO = "https://invalid.repo/not/exists"
    MALFORMED_URL = "not-a-url"

    def test_clear_tmp_dir(self, test_repo_path, logger):
        """Test clearing temporary directory."""
        # Create test files
        test_file = test_repo_path / "test.txt"
        test_repo_path.mkdir(exist_ok=True, parents=True)
        test_file.touch()

        # Clear directory
        git_handler.clear_tmp_dir(logger)
        # Force a refresh of the path's status
        test_repo_path = test_repo_path.resolve()
        assert not test_repo_path.exists()

    def test_clear_tmp_dir_error(self, mocker, logger):
        """Test clear_tmp_dir with error."""
        # Create test directory
        test_repo_path = (git_handler.ROOT_DIR / settings.CLONE_DIR_PATH).resolve()
        test_repo_path.mkdir(exist_ok=True, parents=True)

        # Mock rmtree to fail
        mocker.patch("tmt_web.utils.git_handler.rmtree", side_effect=Exception("Failed to remove"))

        with pytest.raises(GeneralError, match="Failed to clear repository clone directory"):
            git_handler.clear_tmp_dir(logger)

    def test_get_unique_clone_path_valid_url(self):
        """Test getting unique clone path with valid URL."""
        path = git_handler.get_unique_clone_path(self.TEST_REPO)
        assert isinstance(path, Path)
        assert ".repos" in str(path)

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_clone_repository_invalid_url(self, logger):
        """Test cloning with invalid repository URL."""
        with pytest.raises(GitUrlError):
            git_handler.clone_repository(self.INVALID_REPO, logger)

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_get_git_repository_new(self, logger):
        """Test getting repository that doesn't exist yet."""
        path = git_handler.get_git_repository(self.TEST_REPO, logger, None)
        assert path.exists()
        assert (path / ".git").exists()

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_get_git_repository_existing(self, logger):
        """Test getting existing repository."""
        # First clone
        path1 = git_handler.get_git_repository(self.TEST_REPO, logger, None)
        # Second request should reuse
        path2 = git_handler.get_git_repository(self.TEST_REPO, logger, None)
        assert path1 == path2
        assert path1.exists()

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_get_git_repository_with_ref(self, logger):
        """Test getting repository with specific ref."""
        path = git_handler.get_git_repository(self.TEST_REPO, logger, "main")
        assert path.exists()
        assert (path / ".git").exists()

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_get_git_repository_checkout_error(self, mocker, logger):
        """Test get_git_repository with checkout error."""
        # Mock git clone to only try once
        mocker.patch("tmt.utils.git.git_clone", side_effect=Exception("Failed to checkout"), kwargs={"attempts": 1})

        with pytest.raises(AttributeError, match="Failed to checkout ref"):
            git_handler.get_git_repository(self.TEST_REPO, logger, "invalid-branch")

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_get_git_repository_existing_checkout_error(self, mocker, logger):
        """Test get_git_repository with checkout error on existing repo."""
        # First create the repo
        path = git_handler.get_git_repository(self.TEST_REPO, logger, None)
        assert path.exists()

        # Mock checkout to fail
        cmd = Command("git", "checkout", "invalid-branch")
        mocker.patch("tmt.utils.Command.run", side_effect=RunError("Command failed", cmd, 1))

        # Try to get same repo with invalid ref
        with pytest.raises(AttributeError, match="Failed to checkout ref"):
            git_handler.get_git_repository(self.TEST_REPO, logger, "invalid-branch")
