import pytest

from aiohttp import web
from asyncio import BaseEventLoop
from pytest_aiohttp import TestClient
from pytest_mock import MockerFixture
from typing import Any

from ahriman.web.views.base import BaseView


@pytest.fixture
def base(application: web.Application) -> BaseView:
    """
    base view fixture
    :param application: application fixture
    :return: generated base view fixture
    """
    return BaseView(pytest.helpers.request(application, "", ""))


@pytest.fixture
def client(application: web.Application, loop: BaseEventLoop,
           aiohttp_client: Any, mocker: MockerFixture) -> TestClient:
    """
    web client fixture
    :param application: application fixture
    :param loop: context event loop
    :param aiohttp_client: aiohttp client fixture
    :param mocker: mocker object
    :return: web client test instance
    """
    mocker.patch("pathlib.Path.iterdir", return_value=[])
    return loop.run_until_complete(aiohttp_client(application))


@pytest.fixture
def client_with_auth(application_with_auth: web.Application, loop: BaseEventLoop,
                     aiohttp_client: Any, mocker: MockerFixture) -> TestClient:
    """
    web client fixture with full authorization functions
    :param application_with_auth: application fixture
    :param loop: context event loop
    :param aiohttp_client: aiohttp client fixture
    :param mocker: mocker object
    :return: web client test instance
    """
    mocker.patch("pathlib.Path.iterdir", return_value=[])
    return loop.run_until_complete(aiohttp_client(application_with_auth))
