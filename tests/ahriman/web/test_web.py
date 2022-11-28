import pytest

from aiohttp import web
from pytest_mock import MockerFixture

from ahriman.core.exceptions import InitializeError
from ahriman.core.log.filtered_access_logger import FilteredAccessLogger
from ahriman.core.status.watcher import Watcher
from ahriman.web.web import on_shutdown, on_startup, run_server


async def test_on_shutdown(application: web.Application, mocker: MockerFixture) -> None:
    """
    must write information to log
    """
    logging_mock = mocker.patch("logging.Logger.warning")
    await on_shutdown(application)
    logging_mock.assert_called_once_with(pytest.helpers.anyvar(str, True))


async def test_on_startup(application: web.Application, watcher: Watcher, mocker: MockerFixture) -> None:
    """
    must call load method
    """
    mocker.patch("aiohttp.web.Application.__getitem__", return_value=watcher)
    load_mock = mocker.patch("ahriman.core.status.watcher.Watcher.load")

    await on_startup(application)
    load_mock.assert_called_once_with()


async def test_on_startup_exception(application: web.Application, watcher: Watcher, mocker: MockerFixture) -> None:
    """
    must throw exception on load error
    """
    mocker.patch("aiohttp.web.Application.__getitem__", return_value=watcher)
    mocker.patch("ahriman.core.status.watcher.Watcher.load", side_effect=Exception())

    with pytest.raises(InitializeError):
        await on_startup(application)


def test_run(application: web.Application, mocker: MockerFixture) -> None:
    """
    must run application
    """
    port = 8080
    application["configuration"].set_option("web", "port", str(port))
    run_application_mock = mocker.patch("aiohttp.web.run_app")

    run_server(application)
    run_application_mock.assert_called_once_with(
        application, host="127.0.0.1", port=port, path=None, handle_signals=False,
        access_log=pytest.helpers.anyvar(int), access_log_class=FilteredAccessLogger
    )


def test_run_with_auth(application_with_auth: web.Application, mocker: MockerFixture) -> None:
    """
    must run application with enabled authorization
    """
    port = 8080
    application_with_auth["configuration"].set_option("web", "port", str(port))
    run_application_mock = mocker.patch("aiohttp.web.run_app")

    run_server(application_with_auth)
    run_application_mock.assert_called_once_with(
        application_with_auth, host="127.0.0.1", port=port, path=None, handle_signals=False,
        access_log=pytest.helpers.anyvar(int), access_log_class=FilteredAccessLogger
    )


def test_run_with_debug(application_with_debug: web.Application, mocker: MockerFixture) -> None:
    """
    must run application with enabled debug panel
    """
    port = 8080
    application_with_debug["configuration"].set_option("web", "port", str(port))
    run_application_mock = mocker.patch("aiohttp.web.run_app")

    run_server(application_with_debug)
    run_application_mock.assert_called_once_with(
        application_with_debug, host="127.0.0.1", port=port, path=None, handle_signals=False,
        access_log=pytest.helpers.anyvar(int), access_log_class=FilteredAccessLogger
    )


def test_run_with_socket(application: web.Application, mocker: MockerFixture) -> None:
    """
    must run application
    """
    port = 8080
    socket = "/run/ahriman.sock"
    application["configuration"].set_option("web", "port", str(port))
    application["configuration"].set_option("web", "unix_socket", socket)
    run_application_mock = mocker.patch("aiohttp.web.run_app")

    run_server(application)
    run_application_mock.assert_called_once_with(
        application, host="127.0.0.1", port=port, path=socket, handle_signals=False,
        access_log=pytest.helpers.anyvar(int), access_log_class=FilteredAccessLogger
    )
