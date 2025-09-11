"""
Git repository handling utilities.

This module provides functions for cloning and managing Git repositories,
with support for refs (branch/tag) checkout and repository reuse.
It uses tmt's Git utilities for robust clone operations with retry logic.
"""

import re
from shutil import rmtree

from tmt import Logger
from tmt._compat.pathlib import Path
from tmt.utils import Command, Common, GeneralError, RunError
from tmt.utils.git import check_git_url, git_clone

from tmt_web import settings

# Root directory is two levels up from this file
ROOT_DIR = Path(__file__).resolve().parents[2]


def get_unique_clone_path(url: str) -> Path:
    """
    Generate a unique path for cloning a repository.

    :param url: Repository URL
    :return: Unique path for cloning
    """
    url = url.rstrip("/")
    clone_dir_name = str(abs(hash(url)))
    return ROOT_DIR / settings.CLONE_DIR_PATH / clone_dir_name


def clear_tmp_dir(logger: Logger) -> None:
    """
    Clear the temporary directory where repositories are cloned.

    :param logger: Logger instance
    :raises: GeneralError if cleanup fails
    """
    logger.debug("Clearing repository clone directory")
    path = (ROOT_DIR / settings.CLONE_DIR_PATH).resolve()

    try:
        if path.exists():
            rmtree(path, ignore_errors=True)
            logger.debug("Repository clone directory cleared")
    except Exception as err:
        logger.fail(f"Failed to clear repository clone directory '{path}'")
        raise GeneralError(f"Failed to clear repository clone directory '{path}'") from err


def clone_repository(url: str, logger: Logger) -> Path:
    """
    Clone a Git repository to a unique path.

    :param url: Repository URL
    :param logger: Logger instance
    :param ref: Optional ref to checkout
    :return: Path to the cloned repository
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if clone fails
    :raises: AttributeError if ref doesn't exist
    """
    # Validate URL
    url = check_git_url(url, logger)

    # Get unique path
    destination = get_unique_clone_path(url)

    # Clone with retry logic
    git_clone(url=url, destination=destination, logger=logger)

    return destination


def get_git_repository(url: str, logger: Logger, ref: str | None = None) -> Path:
    """
    Get a Git repository by cloning or reusing an existing clone.

    :param url: Repository URL
    :param logger: Logger instance
    :param ref: Optional ref to checkout
    :return: Path to the cloned repository
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if cloning, fetching, or updating a branch fails
    :raises: AttributeError if ref doesn't exist
    """
    destination = get_unique_clone_path(url)
    if not destination.exists():
        clone_repository(url, logger)

    common = Common(logger=logger)

    # Fetch remote refs
    _fetch_remote(common, destination, logger)

    # If no ref is specified, the default branch is used
    ref = ref or _get_default_branch(common, destination, logger)

    try:
        common.run(Command("git", "checkout", ref), cwd=destination)
    except RunError as err:
        logger.fail(f"Failed to checkout ref '{ref}'")
        raise AttributeError(f"Failed to checkout ref '{ref}'") from err

    # If the ref is a branch, ensure it's up to date
    if _is_branch(common, destination, ref):
        _update_branch(common, destination, ref, logger)

    return destination


def _get_default_branch(common: Common, repo_path: Path, logger: Logger) -> str:
    """Determine the default branch of a Git repository using a remote HEAD."""
    try:
        output = common.run(
            Command("git", "symbolic-ref", "refs/remotes/origin/HEAD"), cwd=repo_path
        )
        if output.stdout:
            match = re.search(r"refs/remotes/origin/(.*)", output.stdout.strip())
            if match:
                return match.group(1)

        logger.fail(f"Failed to determine default branch for repository '{repo_path}'")
        raise GeneralError(f"Failed to determine default branch for repository '{repo_path}'")

    except RunError as err:
        logger.fail(f"Failed to determine default branch for repository '{repo_path}'")
        raise GeneralError(
            f"Failed to determine default branch for repository '{repo_path}'"
        ) from err


def _fetch_remote(common: Common, repo_path: Path, logger: Logger) -> None:
    """Fetch updates from the remote repository."""
    try:
        common.run(Command("git", "fetch"), cwd=repo_path)
    except RunError as err:
        logger.fail(f"Failed to fetch remote for repository '{repo_path}'")
        raise GeneralError(f"Failed to fetch remote for repository '{repo_path}'") from err


def _update_branch(common: Common, repo_path: Path, branch: str, logger: Logger) -> None:
    """Ensure the specified branch is up to date with its remote counterpart."""
    try:
        common.run(Command("git", "show-branch", f"origin/{branch}"), cwd=repo_path)
    except RunError as err:
        logger.fail(f"Branch '{branch}' does not exist in repository '{repo_path}'")
        raise GeneralError(f"Branch {branch}' does not exist in repository '{repo_path}'") from err
    try:
        # Check if the branch is already up to date
        common.run(Command("git", "diff", "--quiet", branch, f"origin/{branch}"), cwd=repo_path)
        return
    except RunError:
        # Branch is not up to date, proceed with update
        try:
            common.run(Command("git", "reset", "--hard", f"origin/{branch}"), cwd=repo_path)
        except RunError as err:
            logger.fail(f"Failed to update branch '{branch}' for repository '{repo_path}'")
            raise GeneralError(
                f"Failed to update branch '{branch}' for repository '{repo_path}'"
            ) from err


def _is_branch(common: Common, repo_path: Path, ref: str) -> bool:
    """
    Check if the given ref is a branch in the Git repository.

    :return: True if the ref is a branch, False otherwise.
    """
    try:
        common.run(Command("git", "show-ref", "-q", "--verify", f"refs/heads/{ref}"), cwd=repo_path)
        return True
    except RunError:
        return False
