from pathlib import Path
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, call

from ahriman.models.pkgbuild_patch import PkgbuildPatch


def test_post_init() -> None:
    """
    must remove empty keys
    """
    assert PkgbuildPatch("", "value").key is None
    assert PkgbuildPatch(None, "value").key is None
    assert PkgbuildPatch("key", "value").key == "key"


def test_is_function() -> None:
    """
    must correctly define key as function
    """
    assert not PkgbuildPatch("key", "value").is_function
    assert PkgbuildPatch("key()", "value").is_function


def test_is_plain_diff() -> None:
    """
    must correctly define key as function
    """
    assert not PkgbuildPatch("key", "value").is_plain_diff
    assert PkgbuildPatch(None, "value").is_plain_diff


def test_quote() -> None:
    """
    must quote strings if unsafe flag is not set
    """
    assert PkgbuildPatch("key", "value").quote("value") == """value"""
    assert PkgbuildPatch("key", "va'lue").quote("va'lue") == """'va'"'"'lue'"""
    assert PkgbuildPatch("key", "va'lue", unsafe=True).quote("va'lue") == """va'lue"""


def test_serialize() -> None:
    """
    must correctly serialize string values
    """
    assert PkgbuildPatch("key", "value").serialize() == "key=value"
    assert PkgbuildPatch("key", "42").serialize() == "key=42"
    assert PkgbuildPatch("key", "4'2").serialize() == """key='4'"'"'2'"""
    assert PkgbuildPatch("key", "4'2", unsafe=True).serialize() == "key=4'2"


def test_serialize_plain_diff() -> None:
    """
    must correctly serialize function values
    """
    assert PkgbuildPatch(None, "{ value }").serialize() == "{ value }"


def test_serialize_function() -> None:
    """
    must correctly serialize function values
    """
    assert PkgbuildPatch("key()", "{ value }", unsafe=True).serialize() == "key() { value }"


def test_serialize_list() -> None:
    """
    must correctly serialize list values
    """
    assert PkgbuildPatch("arch", ["i686", "x86_64"]).serialize() == """arch=(i686 x86_64)"""
    assert PkgbuildPatch("key", ["val'ue", "val\"ue2"]).serialize() == """key=('val'"'"'ue' 'val"ue2')"""
    assert PkgbuildPatch("key", ["val'ue", "val\"ue2"], unsafe=True).serialize() == """key=(val'ue val"ue2)"""


def test_write(mocker: MockerFixture) -> None:
    """
    must write serialized value to the file
    """
    file_mock = MagicMock()
    open_mock = mocker.patch("pathlib.Path.open")
    open_mock.return_value.__enter__.return_value = file_mock

    PkgbuildPatch("key", "value").write(Path("PKGBUILD"))
    open_mock.assert_called_once_with("a")
    file_mock.write.assert_has_calls([call("\n"), call("""key=value"""), call("\n")])
