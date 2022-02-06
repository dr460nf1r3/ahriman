import json
import pytest
import requests

from pathlib import Path
from pytest_mock import MockerFixture
from unittest import mock
from unittest.mock import MagicMock

from ahriman.core.alpm.aur import AUR
from ahriman.core.exceptions import InvalidPackageInfo
from ahriman.models.aur_package import AURPackage


def _get_response(resource_path_root: Path) -> str:
    """
    load response from resource file
    :param resource_path_root: path to resource root
    :return: response text
    """
    return (resource_path_root / "models" / "package_ahriman_aur").read_text()


def test_info(mocker: MockerFixture) -> None:
    """
    must call info method
    """
    info_mock = mocker.patch("ahriman.core.alpm.aur.AUR.package_info")
    AUR.info("ahriman")
    info_mock.assert_called_once_with("ahriman")


def test_multisearch(aur_package_ahriman: AURPackage, mocker: MockerFixture) -> None:
    """
    must search in AUR with multiple words
    """
    terms = ["ahriman", "is", "cool"]
    search_mock = mocker.patch("ahriman.core.alpm.aur.AUR.search", return_value=[aur_package_ahriman])

    assert AUR.multisearch(*terms) == [aur_package_ahriman]
    search_mock.assert_has_calls([mock.call("ahriman"), mock.call("cool")])


def test_multisearch_empty(mocker: MockerFixture) -> None:
    """
    must return empty list if no long terms supplied
    """
    terms = ["it", "is"]
    search_mock = mocker.patch("ahriman.core.alpm.aur.AUR.search")

    assert AUR.multisearch(*terms) == []
    search_mock.assert_not_called()


def test_multisearch_single(aur_package_ahriman: AURPackage, mocker: MockerFixture) -> None:
    """
    must search in AUR with one word
    """
    search_mock = mocker.patch("ahriman.core.alpm.aur.AUR.search", return_value=[aur_package_ahriman])
    assert AUR.multisearch("ahriman") == [aur_package_ahriman]
    search_mock.assert_called_once_with("ahriman")


def test_search(mocker: MockerFixture) -> None:
    """
    must call search method
    """
    search_mock = mocker.patch("ahriman.core.alpm.aur.AUR.package_search")
    AUR.search("ahriman")
    search_mock.assert_called_once_with("ahriman")


def test_parse_response(aur_package_ahriman: AURPackage, resource_path_root: Path) -> None:
    """
    must parse success response
    """
    response = _get_response(resource_path_root)
    assert AUR.parse_response(json.loads(response)) == [aur_package_ahriman]


def test_parse_response_error(resource_path_root: Path) -> None:
    """
    must raise exception on invalid response
    """
    response = (resource_path_root / "models" / "aur_error").read_text()
    with pytest.raises(InvalidPackageInfo, match="Incorrect request type specified."):
        AUR.parse_response(json.loads(response))


def test_parse_response_unknown_error(resource_path_root: Path) -> None:
    """
    must raise exception on invalid response with empty error message
    """
    with pytest.raises(InvalidPackageInfo, match="Unknown API error"):
        AUR.parse_response({"type": "error"})


def test_make_request(aur: AUR, aur_package_ahriman: AURPackage,
                      mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must perform request to AUR
    """
    response_mock = MagicMock()
    response_mock.json.return_value = json.loads(_get_response(resource_path_root))
    request_mock = mocker.patch("requests.get", return_value=response_mock)

    assert aur.make_request("info", "ahriman") == [aur_package_ahriman]
    request_mock.assert_called_once_with(
        "https://aur.archlinux.org/rpc", params={"v": "5", "type": "info", "arg": ["ahriman"]})


def test_make_request_multi_arg(aur: AUR, aur_package_ahriman: AURPackage,
                                mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must perform request to AUR with multiple args
    """
    response_mock = MagicMock()
    response_mock.json.return_value = json.loads(_get_response(resource_path_root))
    request_mock = mocker.patch("requests.get", return_value=response_mock)

    assert aur.make_request("search", "ahriman", "is", "cool") == [aur_package_ahriman]
    request_mock.assert_called_once_with(
        "https://aur.archlinux.org/rpc", params={"v": "5", "type": "search", "arg[]": ["ahriman", "is", "cool"]})


def test_make_request_with_kwargs(aur: AUR, aur_package_ahriman: AURPackage,
                                  mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must perform request to AUR with named parameters
    """
    response_mock = MagicMock()
    response_mock.json.return_value = json.loads(_get_response(resource_path_root))
    request_mock = mocker.patch("requests.get", return_value=response_mock)

    assert aur.make_request("search", "ahriman", by="name") == [aur_package_ahriman]
    request_mock.assert_called_once_with(
        "https://aur.archlinux.org/rpc", params={"v": "5", "type": "search", "arg": ["ahriman"], "by": "name"})


def test_make_request_failed(aur: AUR, mocker: MockerFixture) -> None:
    """
    must reraise generic exception
    """
    mocker.patch("requests.get", side_effect=Exception())
    with pytest.raises(Exception):
        aur.make_request("info", "ahriman")


def test_make_request_failed_http_error(aur: AUR, mocker: MockerFixture) -> None:
    """
    must reraise http exception
    """
    mocker.patch("requests.get", side_effect=requests.exceptions.HTTPError())
    with pytest.raises(requests.exceptions.HTTPError):
        aur.make_request("info", "ahriman")


def test_package_info(aur: AUR, aur_package_ahriman: AURPackage, mocker: MockerFixture) -> None:
    """
    must make request for info
    """
    request_mock = mocker.patch("ahriman.core.alpm.aur.AUR.make_request", return_value=[aur_package_ahriman])
    assert aur.package_info(aur_package_ahriman.name) == aur_package_ahriman
    request_mock.assert_called_once_with("info", aur_package_ahriman.name)


def test_package_search(aur: AUR, aur_package_ahriman: AURPackage, mocker: MockerFixture) -> None:
    """
    must make request for search
    """
    request_mock = mocker.patch("ahriman.core.alpm.aur.AUR.make_request", return_value=[aur_package_ahriman])
    assert aur.package_search(aur_package_ahriman.name, by="name") == [aur_package_ahriman]
    request_mock.assert_called_once_with("search", aur_package_ahriman.name, by="name")
