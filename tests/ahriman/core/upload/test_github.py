import pytest
import requests

from pathlib import Path
from pytest_mock import MockerFixture
from typing import Any, Dict
from unittest import mock
from unittest.mock import MagicMock

from ahriman.core.upload.github import Github


def test_calculate_hash_empty(resource_path_root: Path) -> None:
    """
    must calculate checksum for empty file correctly
    """
    path = resource_path_root / "models" / "empty_file_checksum"
    assert Github.calculate_hash(path) == "d41d8cd98f00b204e9800998ecf8427e"


def test_calculate_hash_small(resource_path_root: Path) -> None:
    """
    must calculate checksum for path which is single chunk
    """
    path = resource_path_root / "models" / "package_ahriman_srcinfo"
    assert Github.calculate_hash(path) == "a55f82198e56061295d405aeb58f4062"


def test_get_body_get_hashes() -> None:
    """
    must generate readable body
    """
    source = {Path("c"): "c_md5", Path("a"): "a_md5", Path("b"): "b_md5"}
    body = Github.get_body(source)
    parsed = Github.get_hashes({"body": body})
    assert {fn.name: md5 for fn, md5 in source.items()} == parsed


def test_get_hashes_empty() -> None:
    """
    must read empty body
    """
    assert Github.get_hashes({"body": None}) == {}


def test_request(github: Github, mocker: MockerFixture) -> None:
    """
    must call request method
    """
    response_mock = MagicMock()
    request_mock = mocker.patch("requests.request", return_value=response_mock)

    github._request("GET", "url", arg="arg")
    request_mock.assert_called_once_with("GET", "url", auth=github.auth, arg="arg")
    response_mock.raise_for_status.assert_called_once()


def test_request_exception(github: Github, mocker: MockerFixture) -> None:
    """
    must call request method and log HTTPError exception
    """
    mocker.patch("requests.request", side_effect=requests.HTTPError())
    with pytest.raises(requests.HTTPError):
        github._request("GET", "url", arg="arg")


def test_asset_remove(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must remove asset from the release
    """
    request_mock = mocker.patch("ahriman.core.upload.github.Github._request")
    github.asset_remove(github_release, "asset_name")
    request_mock.assert_called_with("DELETE", "asset_url")


def test_asset_remove_unknown(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must not fail if no asset found
    """
    request_mock = mocker.patch("ahriman.core.upload.github.Github._request")
    github.asset_remove(github_release, "unknown_asset_name")
    request_mock.assert_not_called()


def test_asset_upload(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must upload asset to the repository
    """
    mocker.patch("pathlib.Path.open", return_value=b"")
    request_mock = mocker.patch("ahriman.core.upload.github.Github._request")
    remove_mock = mocker.patch("ahriman.core.upload.github.Github.asset_remove")

    github.asset_upload(github_release, Path("/root/new.tar.xz"))
    request_mock.assert_called_with("POST", "upload_url", params={"name": "new.tar.xz"},
                                    data=b"", headers={"Content-Type": "application/x-tar"})
    remove_mock.assert_not_called()


def test_asset_upload_with_removal(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must remove existing file before upload
    """
    mocker.patch("pathlib.Path.open", return_value=b"")
    mocker.patch("ahriman.core.upload.github.Github._request")
    remove_mock = mocker.patch("ahriman.core.upload.github.Github.asset_remove")

    github.asset_upload(github_release, Path("asset_name"))
    remove_mock.assert_called_with(github_release, "asset_name")

    github.asset_upload(github_release, Path("/root/asset_name"))
    remove_mock.assert_called_with(github_release, "asset_name")


def test_asset_upload_empty_mimetype(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must upload asset to the repository with empty mime type if cannot guess it
    """
    mocker.patch("pathlib.Path.open", return_value=b"")
    mocker.patch("ahriman.core.upload.github.Github.asset_remove")
    mocker.patch("mimetypes.guess_type", return_value=(None, None))
    request_mock = mocker.patch("ahriman.core.upload.github.Github._request")

    github.asset_upload(github_release, Path("/root/new.tar.xz"))
    request_mock.assert_called_with("POST", "upload_url", params={"name": "new.tar.xz"},
                                    data=b"", headers={"Content-Type": "application/octet-stream"})


def test_get_local_files(github: Github, resource_path_root: Path, mocker: MockerFixture) -> None:
    """
    must get all local files recursively
    """
    walk_mock = mocker.patch("ahriman.core.util.walk")
    github.get_local_files(resource_path_root)
    walk_mock.assert_called()


def test_files_remove(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must remove files from the remote
    """
    remove_mock = mocker.patch("ahriman.core.upload.github.Github.asset_remove")
    github.files_remove(github_release, {Path("a"): "a"}, {"a": "a", "b": "b"})
    remove_mock.assert_called_once_with(github_release, "b")


def test_files_remove_empty(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must remove nothing if nothing changed
    """
    remove_mock = mocker.patch("ahriman.core.upload.github.Github.asset_remove")
    github.files_remove(github_release, {Path("a"): "a"}, {"a": "a"})
    remove_mock.assert_not_called()


def test_files_upload(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must upload files to the remote
    """
    upload_mock = mocker.patch("ahriman.core.upload.github.Github.asset_upload")
    github.files_upload(github_release, {Path("a"): "a", Path("b"): "c", Path("c"): "c"}, {"a": "a", "b": "b"})
    upload_mock.assert_has_calls([
        mock.call(github_release, Path("b")),
        mock.call(github_release, Path("c")),
    ])


def test_files_upload_empty(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must upload nothing if nothing changed
    """
    upload_mock = mocker.patch("ahriman.core.upload.github.Github.asset_upload")
    github.files_upload(github_release, {Path("a"): "a"}, {"a": "a"})
    upload_mock.assert_not_called()


def test_release_create(github: Github, mocker: MockerFixture) -> None:
    """
    must create release
    """
    request_mock = mocker.patch("ahriman.core.upload.github.Github._request")
    github.release_create()
    request_mock.assert_called_once_with("POST", pytest.helpers.anyvar(str, True),
                                         json={"tag_name": github.architecture, "name": github.architecture})


def test_release_get(github: Github, mocker: MockerFixture) -> None:
    """
    must get release
    """
    request_mock = mocker.patch("ahriman.core.upload.github.Github._request")
    github.release_get()
    request_mock.assert_called_once_with("GET", pytest.helpers.anyvar(str, True))


def test_release_get_empty(github: Github, mocker: MockerFixture) -> None:
    """
    must return nothing in case of 404 status code
    """
    response = requests.Response()
    response.status_code = 404
    mocker.patch("ahriman.core.upload.github.Github._request", side_effect=requests.HTTPError(response=response))
    assert github.release_get() is None


def test_release_get_exception(github: Github, mocker: MockerFixture) -> None:
    """
    must re-raise non HTTPError exception
    """
    mocker.patch("ahriman.core.upload.github.Github._request", side_effect=Exception())
    with pytest.raises(Exception):
        github.release_get()


def test_release_get_exception_http_error(github: Github, mocker: MockerFixture) -> None:
    """
    must re-raise HTTPError exception with code differs from 404
    """
    exception = requests.HTTPError(response=requests.Response())
    mocker.patch("ahriman.core.upload.github.Github._request", side_effect=exception)
    with pytest.raises(requests.HTTPError):
        github.release_get()


def test_release_update(github: Github, github_release: Dict[str, Any], mocker: MockerFixture) -> None:
    """
    must update release
    """
    request_mock = mocker.patch("ahriman.core.upload.github.Github._request")
    github.release_update(github_release, "body")
    request_mock.assert_called_once_with("POST", "release_url", json={"body": "body"})


def test_release_sync(github: Github, mocker: MockerFixture) -> None:
    """
    must run sync command
    """
    release_get_mock = mocker.patch("ahriman.core.upload.github.Github.release_get")
    get_hashes_mock = mocker.patch("ahriman.core.upload.github.Github.get_hashes")
    get_local_files_mock = mocker.patch("ahriman.core.upload.github.Github.get_local_files")
    files_upload_mock = mocker.patch("ahriman.core.upload.github.Github.files_upload")
    files_remove_mock = mocker.patch("ahriman.core.upload.github.Github.files_remove")
    release_update_mock = mocker.patch("ahriman.core.upload.github.Github.release_update")

    github.sync(Path("local"), [])
    release_get_mock.assert_called_once()
    get_hashes_mock.assert_called_once()
    get_local_files_mock.assert_called_once()
    files_upload_mock.assert_called_once()
    files_remove_mock.assert_called_once()
    release_update_mock.assert_called_once()


def test_release_sync_create_release(github: Github, mocker: MockerFixture) -> None:
    """
    must create release in case if it does not exist
    """
    mocker.patch("ahriman.core.upload.github.Github.release_get", return_value=None)
    mocker.patch("ahriman.core.upload.github.Github.get_hashes")
    mocker.patch("ahriman.core.upload.github.Github.get_local_files")
    mocker.patch("ahriman.core.upload.github.Github.files_upload")
    mocker.patch("ahriman.core.upload.github.Github.files_remove")
    mocker.patch("ahriman.core.upload.github.Github.release_update")
    release_create_mock = mocker.patch("ahriman.core.upload.github.Github.release_create")

    github.sync(Path("local"), [])
    release_create_mock.assert_called_once()
