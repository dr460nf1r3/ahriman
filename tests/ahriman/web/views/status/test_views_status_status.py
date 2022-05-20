import pytest

from aiohttp.test_utils import TestClient
from pytest_mock import MockerFixture

import ahriman.version as version

from ahriman.models.build_status import BuildStatusEnum
from ahriman.models.internal_status import InternalStatus
from ahriman.models.package import Package
from ahriman.models.user_access import UserAccess
from ahriman.web.views.status.status import StatusView


async def test_get_permission() -> None:
    """
    must return correct permission for the request
    """
    for method in ("GET", "HEAD"):
        request = pytest.helpers.request("", "", method)
        assert await StatusView.get_permission(request) == UserAccess.Read
    for method in ("POST",):
        request = pytest.helpers.request("", "", method)
        assert await StatusView.get_permission(request) == UserAccess.Full


async def test_get(client: TestClient, package_ahriman: Package) -> None:
    """
    must generate web service status correctly
    """
    await client.post(f"/status-api/v1/packages/{package_ahriman.base}",
                      json={"status": BuildStatusEnum.Success.value, "package": package_ahriman.view()})

    response = await client.get("/status-api/v1/status")
    assert response.ok

    json = await response.json()
    assert json["version"] == version.__version__
    assert json["packages"]
    assert json["packages"]["total"] == 1


async def test_post(client: TestClient) -> None:
    """
    must update service status correctly
    """
    payload = {"status": BuildStatusEnum.Success.value}
    post_response = await client.post("/status-api/v1/status", json=payload)
    assert post_response.status == 204

    response = await client.get("/status-api/v1/status")
    status = InternalStatus.from_json(await response.json())

    assert response.ok
    assert status.status.status == BuildStatusEnum.Success


async def test_post_exception(client: TestClient) -> None:
    """
    must raise exception on invalid payload
    """
    post_response = await client.post("/status-api/v1/status", json={})
    assert post_response.status == 400


async def test_post_exception_inside(client: TestClient, mocker: MockerFixture) -> None:
    """
    exception handler must handle 500 errors
    """
    payload = {"status": BuildStatusEnum.Success.value}
    mocker.patch("ahriman.core.status.watcher.Watcher.update_self", side_effect=Exception())

    post_response = await client.post("/status-api/v1/status", json=payload)
    assert post_response.status == 500
