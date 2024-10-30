"""
Git repository handling utilities.

This module provides functions for cloning and managing Git repositories,
with support for reference (branch/tag) checkout and repository reuse.
It uses tmt's Git utilities for robust clone operations with retry logic.
"""

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
        raise GeneralError(
            f"Failed to clear repository clone directory '{path}'") from err


def clone_repository(url: str, logger: Logger, ref: str | None = None) -> Path:
    """
    Clone a Git repository to a unique path.

    :param url: Repository URL
    :param logger: Logger instance
    :param ref: Optional reference to checkout
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

    # If ref provided, checkout after clone
    if ref:
        common = Common(logger=logger)
        try:
            common.run(Command("git", "checkout", ref), cwd=destination)
        except RunError as err:
            logger.fail(f"Failed to checkout ref '{ref}'")
            raise AttributeError(f"Failed to checkout ref '{ref}': {err}") from err

    return destination


def get_git_repository(url: str, logger: Logger, ref: str | None = None) -> Path:
    """
    Get a Git repository by cloning or reusing an existing clone.

    :param url: Repository URL
    :param logger: Logger instance
    :param ref: Optional reference to checkout
    :return: Path to the cloned repository
    :raises: GitUrlError if URL is invalid
    :raises: GeneralError if clone fails
    :raises: AttributeError if ref doesn't exist
    """
    destination = get_unique_clone_path(url)
    if not destination.exists():
        clone_repository(url, logger, ref)
    elif ref:
        common = Common(logger=logger)
        try:
            common.run(Command("git", "checkout", ref), cwd=destination)
        except RunError as err:
            logger.fail(f"Failed to checkout ref '{ref}'")
            raise AttributeError(f"Failed to checkout ref '{ref}': {err}") from err
    return destination
