import contextlib
import hashlib
from shutil import rmtree

from tmt import Logger
from tmt.utils import (  # type: ignore[attr-defined]
    Command,
    Common,
    GeneralError,
    Path,
    RunError,
    git,
)

from tmt_web import settings

# Root directory is two levels up from this file
ROOT_DIR = Path(__file__).resolve().parents[2]


def checkout_branch(path: Path, logger: Logger, ref: str) -> None:
    """
    Checks out the given branch in the repository.

    :param ref: Name of the ref to check out
    :param path: Path to the repository
    :param logger: Instance of Logger
    :raises: GeneralError if checkout fails
    """
    try:
        common_instance = Common(logger=logger)
        common_instance.run(command=Command("git", "checkout", ref), cwd=path)
        logger.print(f"Checked out ref: {ref}", color="green")
    except RunError as err:
        logger.print("Failed to do checkout in the repository!", color="red")
        raise GeneralError(f"Failed to checkout ref '{ref}'") from err


def get_path_to_repository(url: str) -> Path:
    """
    Returns the path to the cloned repository from the given URL. The repository url is hashed to
    avoid repository name collisions.

    The repository url is hashed to avoid repository name collisions.

    :param url: URL to the repository
    :return: Path to the cloned repository
    """
    url = url.rstrip("/")
    clone_dir_name = hashlib.md5(url.encode()).hexdigest()  # noqa: S324
    repo_name = url.rsplit("/", 1)[-1]
    return ROOT_DIR / settings.CLONE_DIR_PATH / repo_name / clone_dir_name


def check_if_repository_exists(url: str) -> bool:
    """
    Checks if the repository from the given URL is already cloned.

    :param url: URL to the repository
    :return: True if the repository is already cloned, False otherwise
    """
    return get_path_to_repository(url).exists()


def clone_repository(url: str, logger: Logger, ref: str | None = None) -> None:
    """
    Clones the repository from the given URL and optionally checks out a specific ref.

    :param url: URL to the repository
    :param logger: Instance of Logger
    :param ref: Optional name of the ref to check out
    :raises: GeneralError if repository already exists or if cloning/checkout fails
    """
    logger.print("Cloning the repository...")
    path = get_path_to_repository(url)

    if check_if_repository_exists(url):
        if ref:
            try:
                checkout_branch(path=path, logger=logger, ref=ref)
            except GeneralError as err:
                raise GeneralError(
                    f"Repository exists but failed to checkout ref '{ref}'") from err
        raise GeneralError(f"Repository already exists at '{path}'")

    try:
        git.git_clone(url=url, destination=path, logger=logger)
        logger.print("Repository cloned successfully!", color="green")

        if ref:
            checkout_branch(path=path, logger=logger, ref=ref)

    except GeneralError as err:
        logger.print("Failed to clone the repository!", color="red")
        raise GeneralError(f"Failed to clone repository from '{url}'") from err


def clear_tmp_dir(logger: Logger) -> None:
    """
    Clears the .tmp directory.

    :param logger: Instance of Logger
    :raises: GeneralError if directory cleanup fails
    """
    logger.print("Clearing the .tmp directory...")
    path = ROOT_DIR / settings.CLONE_DIR_PATH

    try:
        rmtree(path)
        logger.print("Repository clone directory cleared successfully!", color="green")
    except Exception as err:
        logger.print("Failed to clear the repository clone directory!", color="red")
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
    :raises: GeneralError if cloning or checkout fails
    """
    with contextlib.suppress(GeneralError):
        clone_repository(url, logger, ref)

    return get_path_to_repository(url)
