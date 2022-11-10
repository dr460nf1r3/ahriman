import pytest

from pathlib import Path
from pytest_mock import MockerFixture

from ahriman.core.configuration import Configuration
from ahriman.core.exceptions import ExtensionError
from ahriman.core.triggers import TriggerLoader
from ahriman.models.package import Package
from ahriman.models.result import Result


def test_load_trigger_package(trigger_loader: TriggerLoader) -> None:
    """
    must load trigger from package
    """
    assert trigger_loader.load_trigger("ahriman.core.report.ReportTrigger")


def test_load_trigger_package_invalid_import(trigger_loader: TriggerLoader, mocker: MockerFixture) -> None:
    """
    must raise InvalidExtension on invalid import
    """
    mocker.patch("ahriman.core.triggers.trigger_loader.importlib.import_module", side_effect=ModuleNotFoundError())
    with pytest.raises(ExtensionError):
        trigger_loader.load_trigger("random.module")


def test_load_trigger_package_not_trigger(trigger_loader: TriggerLoader) -> None:
    """
    must raise InvalidExtension if imported module is not a type
    """
    with pytest.raises(ExtensionError):
        trigger_loader.load_trigger("ahriman.core.util.check_output")


def test_load_trigger_package_error_on_creation(trigger_loader: TriggerLoader, mocker: MockerFixture) -> None:
    """
    must raise InvalidException on trigger initialization if any exception is thrown
    """
    mocker.patch("ahriman.core.triggers.trigger.Trigger.__init__", side_effect=Exception())
    with pytest.raises(ExtensionError):
        trigger_loader.load_trigger("ahriman.core.report.ReportTrigger")


def test_load_trigger_package_is_not_trigger(trigger_loader: TriggerLoader) -> None:
    """
    must raise InvalidExtension if loaded class is not a trigger
    """
    with pytest.raises(ExtensionError):
        trigger_loader.load_trigger("ahriman.core.sign.gpg.GPG")


def test_load_trigger_path(trigger_loader: TriggerLoader, resource_path_root: Path) -> None:
    """
    must load trigger from path
    """
    path = resource_path_root.parent.parent / "src" / "ahriman" / "core" / "report" / "report_trigger.py"
    assert trigger_loader.load_trigger(f"{path}.ReportTrigger")


def test_load_trigger_path_directory(trigger_loader: TriggerLoader, resource_path_root: Path) -> None:
    """
    must raise InvalidExtension if provided import path is directory
    """
    path = resource_path_root.parent.parent / "src" / "ahriman" / "core" / "report"
    with pytest.raises(ExtensionError):
        trigger_loader.load_trigger(f"{path}.ReportTrigger")


def test_load_trigger_path_not_found(trigger_loader: TriggerLoader) -> None:
    """
    must raise InvalidExtension if file cannot be found
    """
    with pytest.raises(ExtensionError):
        trigger_loader.load_trigger("/some/random/path.py.SomeRandomModule")


def test_on_result(trigger_loader: TriggerLoader, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must run triggers
    """
    upload_mock = mocker.patch("ahriman.core.upload.UploadTrigger.on_result")
    report_mock = mocker.patch("ahriman.core.report.ReportTrigger.on_result")

    trigger_loader.on_result(Result(), [package_ahriman])
    report_mock.assert_called_once_with(Result(), [package_ahriman])
    upload_mock.assert_called_once_with(Result(), [package_ahriman])


def test_on_result_exception(trigger_loader: TriggerLoader, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must suppress exception during trigger run
    """
    upload_mock = mocker.patch("ahriman.core.upload.UploadTrigger.on_result", side_effect=Exception())
    report_mock = mocker.patch("ahriman.core.report.ReportTrigger.on_result")
    log_mock = mocker.patch("logging.Logger.exception")

    trigger_loader.on_result(Result(), [package_ahriman])
    report_mock.assert_called_once_with(Result(), [package_ahriman])
    upload_mock.assert_called_once_with(Result(), [package_ahriman])
    log_mock.assert_called_once()


def test_on_start(trigger_loader: TriggerLoader, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must run triggers on start
    """
    upload_mock = mocker.patch("ahriman.core.upload.UploadTrigger.on_start")
    report_mock = mocker.patch("ahriman.core.report.ReportTrigger.on_start")

    trigger_loader.on_start()
    assert trigger_loader._on_stop_requested
    report_mock.assert_called_once_with()
    upload_mock.assert_called_once_with()


def test_on_stop_with_on_start(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must call on_stop on exit if on_start was called
    """
    on_stop_mock = mocker.patch("ahriman.core.triggers.trigger_loader.TriggerLoader.on_stop")

    trigger_loader = TriggerLoader("x86_64", configuration)
    trigger_loader.on_start()
    del trigger_loader
    on_stop_mock.assert_called_once_with()


def test_on_stop_without_on_start(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must call not on_stop on exit if on_start wasn't called
    """
    on_stop_mock = mocker.patch("ahriman.core.triggers.trigger_loader.TriggerLoader.on_stop")

    trigger_loader = TriggerLoader("x86_64", configuration)
    del trigger_loader
    on_stop_mock.assert_not_called()


def test_on_stop(trigger_loader: TriggerLoader, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must run triggers on stop
    """
    upload_mock = mocker.patch("ahriman.core.upload.UploadTrigger.on_stop")
    report_mock = mocker.patch("ahriman.core.report.ReportTrigger.on_stop")

    trigger_loader.on_stop()
    report_mock.assert_called_once_with()
    upload_mock.assert_called_once_with()
