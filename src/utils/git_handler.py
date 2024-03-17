import sys
from subprocess import Popen
from tmt import Logger
import os
import tmt.utils
from pathlib import Path


def clone_repository(url: str, logger: Logger) -> None:
    """
    Clones the repository from the given URL.
    Raises FileExistsError if the repository is already cloned and raises Exception if the cloning fails.
    :param url: URL to the repository
    :param logger: Instance of Logger
    :return:
    """
    logger.print("Cloning the repository...")
    path = get_path_to_repository(url)
    if check_if_repository_exists(url):
        logger.print("Repository already cloned!", color="yellow")
        raise FileExistsError
    try:
        tmt.utils.git_clone(url=url, shallow=True, destination=path, logger=logger)
    except tmt.utils.GeneralError as e:
        logger.print("Failed to clone the repository!", color="red")
        raise Exception
    logger.print("Repository cloned successfully!", color="green")


def get_path_to_repository(url: str) -> Path:
    """
    Returns the path to the cloned repository from the given URL.
    :param url: URL to the repository
    :return: Path to the cloned repository
    """
    repo_name = url.rsplit('/', 1)[-1]
    path = os.path.realpath(__file__)
    path = path.replace("src/utils/git_handler.py", "")
    path = Path(path + "/.tmp/" + repo_name)
    return path


def check_if_repository_exists(url: str) -> bool:
    """
    Checks if the repository from the given URL is already cloned.
    :param url: URL to the repository
    :return: True if the repository is already cloned, False otherwise
    """
    path = get_path_to_repository(url)
    return path.exists()


def clear_tmp_dir(logger: Logger) -> None:
    """
    Clears the .tmp directory.
    :param logger: Instance of Logger
    :return:
    """
    logger.print("Clearing the .tmp directory...")
    path = os.path.realpath(__file__)
    path = path.replace("src/utils/git_handler.py", "")
    path = Path(path + "/.tmp")
    try:
        Popen(["rm", "-rf", path])
    except Exception as e:
        logger.print("Failed to clear the .tmp directory!", color="red")
        raise e
    logger.print(".tmp directory cleared successfully!", color="green")


def get_git_repository(url: str, logger: Logger) -> Path:
    """
    Clones the repository from the given URL and returns the path to the cloned repository.
    :param url: URL to the repository
    :param logger: Instance of Logger
    :return: Path to the cloned repository
    """
    try:
        clone_repository(url, logger)
    except FileExistsError:
        pass
    return get_path_to_repository(url)


if __name__ == "__main__":
    print("This is not executable file!")
