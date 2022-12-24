import pytest

from pytest_mock import MockerFixture

from ahriman.core.configuration import Configuration
from ahriman.core.database import SQLite
from ahriman.core.repository.cleaner import Cleaner
from ahriman.core.repository.executor import Executor
from ahriman.core.repository.update_handler import UpdateHandler


@pytest.fixture
def cleaner(configuration: Configuration, database: SQLite, mocker: MockerFixture) -> Cleaner:
    """
    fixture for cleaner

    Args:
        configuration(Configuration): configuration fixture
        database(SQLite): database fixture
        mocker(MockerFixture): mocker object

    Returns:
        Cleaner: cleaner test instance
    """
    mocker.patch("ahriman.models.repository_paths.RepositoryPaths.tree_create")
    return Cleaner("x86_64", configuration, database, report=False, unsafe=False, refresh_pacman_database=0)


@pytest.fixture
def executor(configuration: Configuration, database: SQLite, mocker: MockerFixture) -> Executor:
    """
    fixture for executor

    Args:
        configuration(Configuration): configuration fixture
        database(SQLite): database fixture
        mocker(MockerFixture): mocker object

    Returns:
        Executor: executor test instance
    """
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_cache")
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_chroot")
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_packages")
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_queue")
    mocker.patch("ahriman.models.repository_paths.RepositoryPaths.tree_create")
    return Executor("x86_64", configuration, database, report=False, unsafe=False, refresh_pacman_database=0)


@pytest.fixture
def update_handler(configuration: Configuration, database: SQLite, mocker: MockerFixture) -> UpdateHandler:
    """
    fixture for update handler

    Args:
        configuration(Configuration): configuration fixture
        database(SQLite): database fixture
        mocker(MockerFixture): mocker object

    Returns:
        UpdateHandler: update handler test instance
    """
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_cache")
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_chroot")
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_packages")
    mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_queue")
    mocker.patch("ahriman.models.repository_paths.RepositoryPaths.tree_create")
    return UpdateHandler("x86_64", configuration, database, report=False, unsafe=False, refresh_pacman_database=0)
