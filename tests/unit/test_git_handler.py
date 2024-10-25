import logging
import os
from pathlib import Path

import pytest
import tmt
from tmt.utils import GitUrlError

from tmt_web.utils import git_handler


@pytest.fixture
def logger():
    return tmt.Logger(logging.getLogger("tmt-logger"))


@pytest.fixture
def test_repo_path():
    """Get the test repository path."""
    return Path(__file__).resolve().parents[2].joinpath(os.getenv("CLONE_DIR_PATH", "./.repos/"))


@pytest.fixture
def _clean_repo_dir(test_repo_path, logger):
    """Ensure clean repository directory before and after tests."""
    # Clean before test
    git_handler.clear_tmp_dir(logger)
    test_repo_path.mkdir(exist_ok=True)

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
        test_repo_path.mkdir(exist_ok=True)
        test_file.touch()

        # Clear directory
        git_handler.clear_tmp_dir(logger)
        assert not test_repo_path.exists()

    def test_get_path_to_repository_valid_url(self):
        """Test getting repository path with valid URL."""
        path = git_handler.get_path_to_repository(self.TEST_REPO)
        assert isinstance(path, Path)
        assert ".repos" in str(path)
        assert "tmt" in str(path)

    def test_get_path_to_repository_invalid_url(self):
        """Test getting repository path with invalid URL."""
        with pytest.raises(GitUrlError, match="Invalid repository URL format"):
            git_handler.get_path_to_repository(self.MALFORMED_URL)

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_check_if_repository_exists(self, logger):
        """Test repository existence check."""
        # Initially should not exist
        assert not git_handler.check_if_repository_exists(self.TEST_REPO)

        # Clone and check again
        git_handler.clone_repository(self.TEST_REPO, logger)
        assert git_handler.check_if_repository_exists(self.TEST_REPO)

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_clone_repository_success(self, logger):
        """Test successful repository cloning."""
        git_handler.clone_repository(self.TEST_REPO, logger)
        path = git_handler.get_path_to_repository(self.TEST_REPO)
        assert path.exists()
        assert (path / ".git").exists()

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_clone_repository_already_exists(self, logger):
        """Test cloning when repository already exists."""
        git_handler.clone_repository(self.TEST_REPO, logger)
        with pytest.raises(FileExistsError):
            git_handler.clone_repository(self.TEST_REPO, logger)

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_clone_repository_invalid_url(self, logger):
        """Test cloning with invalid repository URL."""
        with pytest.raises(GitUrlError):
            git_handler.clone_repository(self.INVALID_REPO, logger)

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_clone_repository_with_ref(self, logger):
        """Test cloning with specific ref."""
        git_handler.clone_repository(self.TEST_REPO, logger, ref="main")
        path = git_handler.get_path_to_repository(self.TEST_REPO)
        assert path.exists()

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_clone_repository_invalid_ref(self, logger):
        """Test cloning with invalid ref."""
        with pytest.raises(AttributeError, match="Failed to checkout ref"):
            git_handler.clone_repository(self.TEST_REPO, logger, ref="invalid-branch")

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_checkout_branch_success(self, logger):
        """Test successful branch checkout."""
        git_handler.clone_repository(self.TEST_REPO, logger)
        path = git_handler.get_path_to_repository(self.TEST_REPO)

        # Test switching between valid branches
        git_handler.checkout_branch(path, logger, "quay")
        git_handler.checkout_branch(path, logger, "main")

    @pytest.mark.usefixtures("_clean_repo_dir")
    def test_checkout_branch_invalid(self, logger):
        """Test checkout with invalid branch."""
        git_handler.clone_repository(self.TEST_REPO, logger)
        path = git_handler.get_path_to_repository(self.TEST_REPO)

        with pytest.raises(AttributeError, match="Failed to checkout ref"):
            git_handler.checkout_branch(path, logger, "invalid-branch")

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
