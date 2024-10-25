import contextlib
import hashlib
from shutil import rmtree

from tmt import Logger
from tmt.utils import (  # type: ignore[attr-defined]
    Command,
    Common,
    GeneralError,
    GitUrlError,
    Path,
    RunError,
)
from tmt.utils.git import check_git_url, git_clone

from tmt_web import settings

# Root directory is two levels up from this file
ROOT_DIR = Path(__file__).resolve().parents[2]


def checkout_branch(path: Path, logger: Logger, ref: str) -> None:
    """
    Checks out the given branch in the repository.

    :param ref: Name of the ref to check out
    :param path: Path to the repository
    :param logger: Instance of Logger
    :raises: AttributeError if ref doesn't exist
    """
    try:
        logger.debug(f"Checking out ref '{ref}'")
        common_instance = Common(logger=logger)
        common_instance.run(command=Command("git", "checkout", ref), cwd=path)
        logger.debug(f"Checked out ref '{ref}'")
    except RunError as err:
        logger.fail(f"Failed to checkout ref '{ref}'")
        raise AttributeError(f"Failed to checkout ref '{ref}'") from err


def get_path_to_repository(url: str) -> Path:
    """
    Returns the path to the cloned repository from the given URL. The repository url is hashed to
    avoid repository name collisions.

    The repository url is hashed to avoid repository name collisions.

    :param url: URL to the repository
    :return: Path to the cloned repository
    :raises: GitUrlError if URL is invalid
    """
    url = url.rstrip("/")
    try:
        repo_name = url.rsplit("/", 1)[-1]
    except Exception as err:
        raise GitUrlError(f"Invalid repository URL: {url}") from err

    clone_dir_name = str(abs(hash(url)))  # abs in case of negative numbers
    return ROOT_DIR / settings.CLONE_DIR_PATH / repo_name / clone_dir_name


def check_if_repository_exists(url: str) -> bool:
    """
    Checks if the repository from the given URL is already cloned.

    :param url: URL to the repository
    :return: True if the repository is already cloned, False otherwise
    :raises: GitUrlError if URL is invalid
    """
    return get_path_to_repository(url).exists()


def clone_repository(url: str, logger: Logger, ref: str | None = None) -> None:
    """
    Clones the repository from the given URL and optionally checks out a specific ref.

    :param url: URL to the repository
    :param logger: Instance of Logger
    :param ref: Optional name of the ref to check out
    :raises: GitUrlError if URL is invalid
    :raises: FileExistsError if repository already exists
    :raises: AttributeError if ref doesn't exist
    """
    logger.debug(f"Cloning repository from {url}")
    try:
        # Validate URL before proceeding
        url = check_git_url(url, logger)
        path = get_path_to_repository(url)
    except GitUrlError as err:
        logger.fail(str(err))
        raise

    if check_if_repository_exists(url):
        if ref:
            try:
                checkout_branch(path=path, logger=logger, ref=ref)
            except AttributeError as err:
                logger.fail(f"Repository exists but failed to checkout ref '{ref}'")
                raise AttributeError(
                    f"Repository exists but failed to checkout ref '{ref}'") from err
        logger.debug("Repository already exists")
        raise FileExistsError(f"Repository already exists at '{path}'")

    try:
        # Use tmt's git_clone with retry logic
        git_clone(url=url, destination=path, logger=logger)
        logger.debug("Repository cloned successfully")

        if ref:
            checkout_branch(path=path, logger=logger, ref=ref)

    except RunError as err:
        logger.fail(f"Failed to clone repository from '{url}'")
        raise GeneralError(f"Failed to clone repository from '{url}'") from err


def clear_tmp_dir(logger: Logger) -> None:
    """
    Clears the .tmp directory.

    :param logger: Instance of Logger
    :raises: GeneralError if directory cleanup fails (but not if directory doesn't exist)
    """
    logger.debug("Clearing repository clone directory")
    path = ROOT_DIR / settings.CLONE_DIR_PATH

    try:
        if path.exists():
            rmtree(path)
            logger.debug("Repository clone directory cleared")
    except Exception as err:
        logger.fail(f"Failed to clear repository clone directory '{path}'")
        raise GeneralError(
            f"Failed to clear repository clone directory '{path}'") from err


def get_git_repository(url: str, logger: Logger, ref: str | None) -> Path:
    """
    Clones the repository from the given URL and returns the path to the cloned repository.
    If the repository already exists, it will be reused.

    :param url: URL to the repository
    :param logger: Instance of Logger
    :param ref: Optional reference (branch, tag, commit) to checkout
    :return: Path to the cloned repository
    :raises: GitUrlError if URL is invalid
    :raises: AttributeError if ref doesn't exist
    """
    with contextlib.suppress(FileExistsError):
        clone_repository(url, logger, ref)

    return get_path_to_repository(url)
