import pytest

from asyncio import BaseEventLoop
from aiohttp import web
from aiohttp.test_utils import TestClient
from collections import namedtuple
from pytest_mock import MockerFixture
from typing import Any
from unittest.mock import MagicMock

import ahriman.core.auth.helpers

from ahriman.core.auth import OAuth
from ahriman.core.configuration import Configuration
from ahriman.core.database import SQLite
from ahriman.core.spawn import Spawn
from ahriman.models.user import User
from ahriman.web.web import setup_service


_request = namedtuple("_request", ["app", "path", "method", "json", "post"])


@pytest.helpers.register
def request(app: web.Application, path: str, method: str, json: Any = None, data: Any = None) -> _request:
    """
    request generator helper

    Args:
        app(web.Application): application fixture
        path(str): path for the request
        method(str): method for the request
        json(Any, optional): json payload of the request (Default value = None)
        data(Any, optional): form data payload of the request (Default value = None)

    Returns:
        _request: dummy request object
    """
    return _request(app, path, method, json, data)


@pytest.fixture
def application(configuration: Configuration, spawner: Spawn, database: SQLite,
                mocker: MockerFixture) -> web.Application:
    """
    application fixture

    Args:
        configuration(Configuration): configuration fixture
        spawner(Spawn): spawner fixture
        database(SQLite): database fixture
        mocker(MockerFixture): mocker object

    Returns:
        web.Application: application test instance
    """
    mocker.patch("ahriman.core.database.SQLite.load", return_value=database)
    mocker.patch("ahriman.models.repository_paths.RepositoryPaths.tree_create")
    mocker.patch.object(ahriman.core.auth.helpers, "_has_aiohttp_security", False)
    return setup_service("x86_64", configuration, spawner)


@pytest.fixture
def application_with_auth(configuration: Configuration, user: User, spawner: Spawn, database: SQLite,
                          mocker: MockerFixture) -> web.Application:
    """
    application fixture with auth enabled

    Args:
        configuration(Configuration): configuration fixture
        user(User): user descriptor fixture
        spawner(Spawn): spawner fixture
        database(SQLite): database fixture
        mocker(MockerFixture): mocker object

    Returns:
        web.Application: application test instance
    """
    configuration.set_option("auth", "target", "configuration")
    mocker.patch("ahriman.core.database.SQLite.load", return_value=database)
    mocker.patch("ahriman.models.repository_paths.RepositoryPaths.tree_create")
    mocker.patch.object(ahriman.core.auth.helpers, "_has_aiohttp_security", True)
    application = setup_service("x86_64", configuration, spawner)

    generated = user.hash_password(application["validator"].salt)
    mocker.patch("ahriman.core.database.SQLite.user_get", return_value=generated)

    return application


@pytest.fixture
def application_with_debug(configuration: Configuration, user: User, spawner: Spawn, database: SQLite,
                           mocker: MockerFixture) -> web.Application:
    """
    application fixture with debug enabled

    Args:
        configuration(Configuration): configuration fixture
        user(User): user descriptor fixture
        spawner(Spawn): spawner fixture
        database(SQLite): database fixture
        mocker(MockerFixture): mocker object

    Returns:
        web.Application: application test instance
    """
    configuration.set_option("web", "debug", "yes")
    mocker.patch("ahriman.core.database.SQLite.load", return_value=database)
    mocker.patch("ahriman.models.repository_paths.RepositoryPaths.tree_create")
    mocker.patch.object(ahriman.core.auth.helpers, "_has_aiohttp_security", False)
    return setup_service("x86_64", configuration, spawner)


@pytest.fixture
def client(application: web.Application, event_loop: BaseEventLoop,
           aiohttp_client: Any, mocker: MockerFixture) -> TestClient:
    """
    web client fixture

    Args:
        application(web.Application): application fixture
        event_loop(BaseEventLoop): context event loop
        aiohttp_client(Any): aiohttp client fixture
        mocker(MockerFixture): mocker object

    Returns:
        TestClient: web client test instance
    """
    mocker.patch("pathlib.Path.iterdir", return_value=[])
    return event_loop.run_until_complete(aiohttp_client(application))


@pytest.fixture
def client_with_auth(application_with_auth: web.Application, event_loop: BaseEventLoop,
                     aiohttp_client: Any, mocker: MockerFixture) -> TestClient:
    """
    web client fixture with full authorization functions

    Args:
        application_with_auth(web.Application): application fixture
        event_loop(BaseEventLoop): context event loop
        aiohttp_client(Any): aiohttp client fixture
        mocker(MockerFixture): mocker object

    Returns:
        TestClient: web client test instance
    """
    mocker.patch("pathlib.Path.iterdir", return_value=[])
    return event_loop.run_until_complete(aiohttp_client(application_with_auth))


@pytest.fixture
def client_with_oauth_auth(application_with_auth: web.Application, event_loop: BaseEventLoop,
                           aiohttp_client: Any, mocker: MockerFixture) -> TestClient:
    """
    web client fixture with full authorization functions

    Args:
        application_with_auth(web.Application): application fixture
        event_loop(BaseEventLoop): context event loop
        aiohttp_client(Any): aiohttp client fixture
        mocker(MockerFixture): mocker object

    Returns:
        TestClient: web client test instance
    """
    mocker.patch("pathlib.Path.iterdir", return_value=[])
    application_with_auth["validator"] = MagicMock(spec=OAuth)
    return event_loop.run_until_complete(aiohttp_client(application_with_auth))
