import pytest

from sqlite3 import Connection

from ahriman.core.database.migrations import Migrations


@pytest.fixture
def migrations(connection: Connection) -> Migrations:
    """
    fixture for migrations object

    Args:
        connection(Connection): sqlite connection fixture

    Returns:
        Migrations: migrations test instance
    """
    return Migrations(connection)
