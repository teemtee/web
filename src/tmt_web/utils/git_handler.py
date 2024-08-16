import contextlib
import os
from shutil import rmtree

from tmt import Logger
from tmt.utils import Command, Common, GeneralError, Path, RunError, git_clone


def checkout_branch(path: Path, logger: Logger, ref: str) -> None:
    """
    Checks out the given branch in the repository.
    :param ref: Name of the ref to check out
    :param path: Path to the repository
    :param logger: Instance of Logger
    :return:
    """
    try:
        common_instance = Common(logger=logger)
        common_instance.run(
            command=Command('git', 'checkout', ref), cwd=path)
    except RunError as err:
        logger.print("Failed to do checkout in the repository!", color="red")
        raise AttributeError from err


def clone_repository(url: str, logger: Logger, ref: str) -> None:
    """
    Clones the repository from the given URL.
    Raises FileExistsError if the repository is already cloned and raises Exception if the cloning fails.
    :param ref: Name of the ref to check out
    :param url: URL to the repository
    :param logger: Instance of Logger
    :return:
    """
    logger.print("Cloning the repository...")
    path = get_path_to_repository(url)
    if check_if_repository_exists(url):
        if ref != "default":
            try:
                checkout_branch(ref=ref, path=path, logger=logger)
            except AttributeError as err:
                raise AttributeError from err
        logger.print("Repository already cloned!", color="yellow")
        raise FileExistsError
    try:
        git_clone(url=url, destination=path, logger=logger)
        if ref != "default":
            try:
                checkout_branch(ref=ref, path=path, logger=logger)
            except AttributeError as err:
                raise AttributeError from err
            checkout_branch(ref=ref, path=path, logger=logger)
    except GeneralError as e:
        logger.print("Failed to clone the repository!", color="red")
        raise Exception from e
    logger.print("Repository cloned successfully!", color="green")


def get_path_to_repository(url: str) -> Path:
    """
    Returns the path to the cloned repository from the given URL.
    :param url: URL to the repository
    :return: Path to the cloned repository
    """
    repo_name = url.rstrip('/').rsplit('/', 1)[-1]
    root_dir = Path(__file__).resolve().parents[2]  # going up from src/utils/git_handler.py
    return root_dir / os.getenv("CLONE_DIR_PATH", "./.repos/") / repo_name


def check_if_repository_exists(url: str) -> bool:
    """
    Checks if the repository from the given URL is already cloned.
    :param url: URL to the repository
    :return: True if the repository is already cloned, False otherwise
    """
    return get_path_to_repository(url).exists()


def clear_tmp_dir(logger: Logger) -> None:
    """
    Clears the .tmp directory.
    :param logger: Instance of Logger
    :return:
    """
    logger.print("Clearing the .tmp directory...")
    root_dir = Path(__file__).resolve().parents[2]  # going up from src/utils/git_handler.py
    path = root_dir / os.getenv("CLONE_DIR_PATH", "./.repos/")
    try:
        rmtree(path)
    except Exception as e:
        logger.print("Failed to clear the repository clone directory!", color="red")
        raise e
    logger.print("Repository clone directory cleared successfully!", color="green")


def get_git_repository(url: str, logger: Logger, ref: str) -> Path:
    """
    Clones the repository from the given URL and returns the path to the cloned repository.
    :param url: URL to the repository
    :param logger: Instance of Logger
    :return: Path to the cloned repository
    """
    with contextlib.suppress(FileExistsError):
        clone_repository(url, logger, ref)
    return get_path_to_repository(url)


if __name__ == "__main__":
    print("This is not executable file!")
