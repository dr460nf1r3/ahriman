import aur
import datetime
import logging
import pytest
import subprocess

from pathlib import Path
from pytest_mock import MockerFixture
from unittest import mock

from ahriman.core.exceptions import InvalidOption, UnsafeRun
from ahriman.core.util import aur_search, check_output, check_user, filter_json, package_like, pretty_datetime, \
    pretty_size, walk
from ahriman.models.package import Package


def test_aur_search(aur_package_ahriman: aur.Package, mocker: MockerFixture) -> None:
    """
    must search in AUR with multiple words
    """
    terms = ["ahriman", "is", "cool"]
    search_mock = mocker.patch("aur.search", return_value=[aur_package_ahriman])

    assert aur_search(*terms) == [aur_package_ahriman]
    search_mock.assert_has_calls([mock.call("ahriman"), mock.call("cool")])


def test_aur_search_empty(mocker: MockerFixture) -> None:
    """
    must return empty list if no long terms supplied
    """
    terms = ["it", "is"]
    search_mock = mocker.patch("aur.search")

    assert aur_search(*terms) == []
    search_mock.assert_not_called()


def test_aur_search_single(aur_package_ahriman: aur.Package, mocker: MockerFixture) -> None:
    """
    must search in AUR with one word
    """
    search_mock = mocker.patch("aur.search", return_value=[aur_package_ahriman])
    assert aur_search("ahriman") == [aur_package_ahriman]
    search_mock.assert_called_once_with("ahriman")


def test_check_output(mocker: MockerFixture) -> None:
    """
    must run command and log result
    """
    logger_mock = mocker.patch("logging.Logger.debug")

    assert check_output("echo", "hello", exception=None) == "hello"
    logger_mock.assert_not_called()

    assert check_output("echo", "hello", exception=None, logger=logging.getLogger("")) == "hello"
    logger_mock.assert_called_once()


def test_check_output_failure(mocker: MockerFixture) -> None:
    """
    must process exception correctly
    """
    logger_mock = mocker.patch("logging.Logger.debug")
    mocker.patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "echo"))

    with pytest.raises(subprocess.CalledProcessError):
        check_output("echo", "hello", exception=None)
        logger_mock.assert_not_called()

    with pytest.raises(subprocess.CalledProcessError):
        check_output("echo", "hello", exception=None, logger=logging.getLogger(""))
        logger_mock.assert_not_called()


def test_check_output_failure_log(mocker: MockerFixture) -> None:
    """
    must process exception correctly and log it
    """
    logger_mock = mocker.patch("logging.Logger.debug")
    mocker.patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "echo", output=b"result"))

    with pytest.raises(subprocess.CalledProcessError):
        check_output("echo", "hello", exception=None, logger=logging.getLogger(""))
        logger_mock.assert_called_once()


def test_check_user(mocker: MockerFixture) -> None:
    """
    must check user correctly
    """
    cwd = Path.cwd()
    mocker.patch("os.getuid", return_value=cwd.stat().st_uid)
    check_user(cwd)


def test_check_user_no_directory(mocker: MockerFixture) -> None:
    """
    must not fail in case if no directory found
    """
    mocker.patch("pathlib.Path.exists", return_value=False)
    check_user(Path.cwd())


def test_check_user_exception(mocker: MockerFixture) -> None:
    """
    must raise exception if user differs
    """
    cwd = Path.cwd()
    mocker.patch("os.getuid", return_value=cwd.stat().st_uid + 1)

    with pytest.raises(UnsafeRun):
        check_user(cwd)


def test_filter_json(package_ahriman: Package) -> None:
    """
    must filter fields by known list
    """
    expected = package_ahriman.view()
    probe = package_ahriman.view()
    probe["unknown_field"] = "value"

    assert expected == filter_json(probe, expected.keys())


def test_filter_json_empty_value(package_ahriman: Package) -> None:
    """
    must return empty values from object
    """
    probe = package_ahriman.view()
    probe["base"] = None
    assert "base" not in filter_json(probe, probe.keys())


def test_package_like(package_ahriman: Package) -> None:
    """
    package_like must return true for archives
    """
    assert package_like(package_ahriman.packages[package_ahriman.base].filepath)


def test_package_like_sig(package_ahriman: Package) -> None:
    """
    package_like must return false for signature files
    """
    package_file = package_ahriman.packages[package_ahriman.base].filepath
    sig_file = package_file.parent / f"{package_file.name}.sig"
    assert not package_like(sig_file)


def test_pretty_datetime() -> None:
    """
    must generate string from timestamp value
    """
    assert pretty_datetime(0) == "1970-01-01 00:00:00"


def test_pretty_datetime_datetime() -> None:
    """
    must generate string from datetime object
    """
    assert pretty_datetime(datetime.datetime(1970, 1, 1, 0, 0, 0)) == "1970-01-01 00:00:00"


def test_pretty_datetime_empty() -> None:
    """
    must generate empty string from None timestamp
    """
    assert pretty_datetime(None) == ""


def test_pretty_size_bytes() -> None:
    """
    must generate bytes string for bytes value
    """
    value, abbrev = pretty_size(42).split()
    assert value == "42.0"
    assert abbrev == "B"


def test_pretty_size_kbytes() -> None:
    """
    must generate kibibytes string for kibibytes value
    """
    value, abbrev = pretty_size(42 * 1024).split()
    assert value == "42.0"
    assert abbrev == "KiB"


def test_pretty_size_mbytes() -> None:
    """
    must generate mebibytes string for mebibytes value
    """
    value, abbrev = pretty_size(42 * 1024 * 1024).split()
    assert value == "42.0"
    assert abbrev == "MiB"


def test_pretty_size_gbytes() -> None:
    """
    must generate gibibytes string for gibibytes value
    """
    value, abbrev = pretty_size(42 * 1024 * 1024 * 1024).split()
    assert value == "42.0"
    assert abbrev == "GiB"


def test_pretty_size_pbytes() -> None:
    """
    must generate pebibytes string for pebibytes value
    """
    value, abbrev = pretty_size(42 * 1024 * 1024 * 1024 * 1024).split()
    assert value == "43008.0"
    assert abbrev == "GiB"


def test_pretty_size_pbytes_failure() -> None:
    """
    must raise exception if level >= 4 supplied
    """
    with pytest.raises(InvalidOption):
        pretty_size(42 * 1024 * 1024 * 1024 * 1024, 4).split()


def test_pretty_size_empty() -> None:
    """
    must generate empty string for None value
    """
    assert pretty_size(None) == ""


def test_walk(resource_path_root: Path) -> None:
    """
    must traverse directory recursively
    """
    expected = sorted([
        resource_path_root / "core/ahriman.ini",
        resource_path_root / "core/logging.ini",
        resource_path_root / "models/big_file_checksum",
        resource_path_root / "models/empty_file_checksum",
        resource_path_root / "models/package_ahriman_srcinfo",
        resource_path_root / "models/package_tpacpi-bat-git_srcinfo",
        resource_path_root / "models/package_yay_srcinfo",
        resource_path_root / "web/templates/build-status/login-modal.jinja2",
        resource_path_root / "web/templates/build-status/package-actions-modals.jinja2",
        resource_path_root / "web/templates/build-status/package-actions-script.jinja2",
        resource_path_root / "web/templates/static/favicon.ico",
        resource_path_root / "web/templates/utils/bootstrap-scripts.jinja2",
        resource_path_root / "web/templates/utils/style.jinja2",
        resource_path_root / "web/templates/build-status.jinja2",
        resource_path_root / "web/templates/email-index.jinja2",
        resource_path_root / "web/templates/repo-index.jinja2",
    ])
    local_files = list(sorted(walk(resource_path_root)))
    assert local_files == expected
