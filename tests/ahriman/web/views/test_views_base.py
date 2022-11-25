import pytest

from multidict import MultiDict

from ahriman.web.views.base import BaseView


def test_configuration(base: BaseView) -> None:
    """
    must return configuration
    """
    assert base.configuration


def test_service(base: BaseView) -> None:
    """
    must return service
    """
    assert base.service


def test_spawn(base: BaseView) -> None:
    """
    must return spawn thread
    """
    assert base.spawner


def test_validator(base: BaseView) -> None:
    """
    must return service
    """
    assert base.validator


async def test_get_permission(base: BaseView) -> None:
    """
    must search for permission attribute in class
    """
    for method in ("DELETE", "GET", "HEAD", "POST"):
        request = pytest.helpers.request(base.request.app, "", method)
        setattr(BaseView, f"{method.upper()}_PERMISSION", "permission")
        assert await base.get_permission(request) == "permission"


def test_get_non_empty() -> None:
    """
    must correctly extract non-empty values
    """
    assert BaseView.get_non_empty(lambda k: k, "key")

    with pytest.raises(KeyError):
        BaseView.get_non_empty(lambda k: None, "key")

    with pytest.raises(KeyError):
        BaseView.get_non_empty(lambda k: "", "key")

    assert BaseView.get_non_empty(lambda k: [k], "key")

    with pytest.raises(KeyError):
        BaseView.get_non_empty(lambda k: [], "key")


async def test_extract_data_json(base: BaseView) -> None:
    """
    must parse and return json
    """
    json = {"key1": "value1", "key2": "value2"}

    async def get_json():
        return json

    base._request = pytest.helpers.request(base.request.app, "", "", json=get_json)
    assert await base.extract_data() == json


async def test_extract_data_post(base: BaseView) -> None:
    """
    must parse and return form data
    """
    json = {"key1": "value1", "key2": "value2"}

    async def get_json():
        raise ValueError()

    async def get_data():
        return json

    base._request = pytest.helpers.request(base.request.app, "", "", json=get_json, data=get_data)
    assert await base.extract_data() == json


async def test_data_as_json(base: BaseView) -> None:
    """
    must parse multi value form payload
    """
    json = {"key1": "value1", "key2": ["value2", "value3"], "key3": ["value4", "value5", "value6"]}

    async def get_data():
        result = MultiDict()
        for key, values in json.items():
            if isinstance(values, list):
                for value in values:
                    result.add(key, value)
            else:
                result.add(key, values)
        return result

    base._request = pytest.helpers.request(base.request.app, "", "", data=get_data)
    assert await base.data_as_json([]) == json


async def test_data_as_json_with_list_keys(base: BaseView) -> None:
    """
    must parse multi value form payload with forced list
    """
    json = {"key1": "value1"}

    async def get_data():
        return json

    base._request = pytest.helpers.request(base.request.app, "", "", data=get_data)
    assert await base.data_as_json(["key1"]) == {"key1": ["value1"]}
