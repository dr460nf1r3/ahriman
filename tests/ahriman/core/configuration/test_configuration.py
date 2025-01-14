import configparser
import pytest

from pathlib import Path
from pytest_mock import MockerFixture
from unittest.mock import call as MockCall

from ahriman.core.configuration import Configuration
from ahriman.core.exceptions import InitializeError
from ahriman.models.repository_paths import RepositoryPaths


def test_repository_name(configuration: Configuration) -> None:
    """
    must return valid repository name
    """
    assert configuration.repository_name == "aur-clone"


def test_repository_paths(configuration: Configuration, repository_paths: RepositoryPaths) -> None:
    """
    must return repository paths
    """
    assert configuration.repository_paths == repository_paths


def test_from_path(mocker: MockerFixture) -> None:
    """
    must load configuration
    """
    mocker.patch("pathlib.Path.is_file", return_value=True)
    read_mock = mocker.patch("ahriman.core.configuration.Configuration.read")
    load_includes_mock = mocker.patch("ahriman.core.configuration.Configuration.load_includes")
    path = Path("path")

    configuration = Configuration.from_path(path, "x86_64")
    assert configuration.path == path
    read_mock.assert_called_once_with(path)
    load_includes_mock.assert_called_once_with()


def test_from_path_file_missing(mocker: MockerFixture) -> None:
    """
    must load configuration based on package files
    """
    mocker.patch("pathlib.Path.is_file", return_value=False)
    mocker.patch("ahriman.core.configuration.Configuration.load_includes")
    read_mock = mocker.patch("ahriman.core.configuration.Configuration.read")

    configuration = Configuration.from_path(Path("path"), "x86_64")
    read_mock.assert_called_once_with(configuration.SYSTEM_CONFIGURATION_PATH)


def test_check_loaded(configuration: Configuration) -> None:
    """
    must return valid path and architecture
    """
    path, architecture = configuration.check_loaded()
    assert path == configuration.path
    assert architecture == configuration.architecture


def test_check_loaded_path(configuration: Configuration) -> None:
    """
    must raise exception if path is none
    """
    configuration.path = None
    with pytest.raises(InitializeError):
        configuration.check_loaded()


def test_check_loaded_architecture(configuration: Configuration) -> None:
    """
    must raise exception if architecture is none
    """
    configuration.architecture = None
    with pytest.raises(InitializeError):
        configuration.check_loaded()


def test_dump(configuration: Configuration) -> None:
    """
    dump must not be empty
    """
    assert configuration.dump()


def test_dump_architecture_specific(configuration: Configuration) -> None:
    """
    dump must contain architecture specific settings
    """
    section = configuration.section_name("build", "x86_64")
    configuration.set_option(section, "archbuild_flags", "hello flag")
    configuration.merge_sections("x86_64")

    dump = configuration.dump()
    assert dump
    assert "build" in dump
    assert section not in dump
    assert dump["build"]["archbuild_flags"] == "hello flag"


def test_section_name(configuration: Configuration) -> None:
    """
    must return architecture specific group
    """
    assert configuration.section_name("build", "x86_64") == "build:x86_64"


def test_getlist(configuration: Configuration) -> None:
    """
    must return list of string correctly
    """
    configuration.set_option("build", "test_list", "a b c")
    assert configuration.getlist("build", "test_list") == ["a", "b", "c"]


def test_getlist_empty(configuration: Configuration) -> None:
    """
    must return list of string correctly for non-existing option
    """
    assert configuration.getlist("build", "test_list", fallback=[]) == []
    configuration.set_option("build", "test_list", "")
    assert configuration.getlist("build", "test_list") == []


def test_getlist_single(configuration: Configuration) -> None:
    """
    must return list of strings for single string
    """
    configuration.set_option("build", "test_list", "a")
    assert configuration.getlist("build", "test_list") == ["a"]
    assert configuration.getlist("build", "test_list") == ["a"]


def test_getlist_with_spaces(configuration: Configuration) -> None:
    """
    must return list of string if there is string with spaces in quotes
    """
    configuration.set_option("build", "test_list", """"ahriman is" cool""")
    assert configuration.getlist("build", "test_list") == ["""ahriman is""", """cool"""]
    configuration.set_option("build", "test_list", """'ahriman is' cool""")
    assert configuration.getlist("build", "test_list") == ["""ahriman is""", """cool"""]


def test_getlist_with_quotes(configuration: Configuration) -> None:
    """
    must return list of string if there is string with quote inside quote
    """
    configuration.set_option("build", "test_list", """"ahriman is" c"'"ool""")
    assert configuration.getlist("build", "test_list") == ["""ahriman is""", """c'ool"""]
    configuration.set_option("build", "test_list", """'ahriman is' c'"'ool""")
    assert configuration.getlist("build", "test_list") == ["""ahriman is""", """c"ool"""]


def test_getlist_unmatched_quote(configuration: Configuration) -> None:
    """
    must raise exception on unmatched quote in string value
    """
    configuration.set_option("build", "test_list", """ahri"man is cool""")
    with pytest.raises(ValueError):
        configuration.getlist("build", "test_list")
    configuration.set_option("build", "test_list", """ahri'man is cool""")
    with pytest.raises(ValueError):
        configuration.getlist("build", "test_list")


def test_getpath_absolute_to_absolute(configuration: Configuration) -> None:
    """
    must not change path for absolute path in settings
    """
    path = Path("/a/b/c")
    configuration.set_option("build", "path", str(path))
    assert configuration.getpath("build", "path") == path


def test_getpath_absolute_to_relative(configuration: Configuration) -> None:
    """
    must prepend root path to relative path
    """
    path = Path("a")
    configuration.set_option("build", "path", str(path))
    result = configuration.getpath("build", "path")
    assert result.is_absolute()
    assert result.parent == configuration.path.parent
    assert result.name == path.name


def test_getpath_with_fallback(configuration: Configuration) -> None:
    """
    must return fallback path
    """
    path = Path("a")
    assert configuration.getpath("some", "option", fallback=path).name == str(path)
    assert configuration.getpath("some", "option", fallback=None) is None


def test_getpath_without_fallback(configuration: Configuration) -> None:
    """
    must raise exception without fallback
    """
    with pytest.raises(configparser.NoSectionError):
        assert configuration.getpath("some", "option")
    with pytest.raises(configparser.NoOptionError):
        assert configuration.getpath("build", "option")


def test_gettype(configuration: Configuration) -> None:
    """
    must extract type from variable
    """
    section, provider = configuration.gettype("customs3", "x86_64")
    assert section == "customs3"
    assert provider == "s3"


def test_gettype_with_fallback(configuration: Configuration) -> None:
    """
    must return same provider name as in fallback
    """
    section, provider = configuration.gettype("rsync", "x86_64", fallback="abracadabra")
    assert section == "rsync"
    assert provider == "abracadabra"


def test_gettype_from_section(configuration: Configuration) -> None:
    """
    must extract type from section name
    """
    section, provider = configuration.gettype("rsync", "x86_64")
    assert section == "rsync"
    assert provider == "rsync"


def test_gettype_from_section_with_architecture(configuration: Configuration) -> None:
    """
    must extract type from section name with architecture
    """
    section, provider = configuration.gettype("github", "x86_64")
    assert section == "github:x86_64"
    assert provider == "github"


def test_gettype_from_section_no_section(configuration: Configuration) -> None:
    """
    must raise NoSectionError during type extraction from section name with architecture
    """
    # technically rsync:x86_64 is valid section
    # but in current configuration it must be considered as missing section
    with pytest.raises(configparser.NoSectionError):
        configuration.gettype("rsync:x86_64", "x86_64")


def test_load_includes_missing(configuration: Configuration) -> None:
    """
    must not fail if not include directory found
    """
    configuration.set_option("settings", "include", "path")
    configuration.load_includes()


def test_load_includes_no_option(configuration: Configuration) -> None:
    """
    must not fail if no option set
    """
    configuration.remove_option("settings", "include")
    configuration.load_includes()


def test_load_includes_no_section(configuration: Configuration) -> None:
    """
    must not fail if no section set
    """
    configuration.remove_section("settings")
    configuration.load_includes()


def test_merge_sections_missing(configuration: Configuration) -> None:
    """
    must merge create section if not exists
    """
    section = configuration.section_name("build", "x86_64")
    configuration.remove_section("build")
    configuration.set_option(section, "key", "value")

    configuration.merge_sections("x86_64")
    assert configuration.get("build", "key") == "value"


def test_reload(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must reload configuration
    """
    load_mock = mocker.patch("ahriman.core.configuration.Configuration.load")
    merge_mock = mocker.patch("ahriman.core.configuration.Configuration.merge_sections")

    configuration.reload()
    load_mock.assert_called_once_with(configuration.path)
    merge_mock.assert_called_once_with(configuration.architecture)


def test_reload_clear(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must clear current settings before configuration reload
    """
    clear_mock = mocker.patch("ahriman.core.configuration.Configuration.remove_section")
    sections = configuration.sections()

    configuration.reload()
    clear_mock.assert_has_calls([MockCall(section) for section in sections])


def test_reload_no_architecture(configuration: Configuration) -> None:
    """
    must raise exception on reload if no architecture set
    """
    configuration.architecture = None
    with pytest.raises(InitializeError):
        configuration.reload()


def test_reload_no_path(configuration: Configuration) -> None:
    """
    must raise exception on reload if no path set
    """
    configuration.path = None
    with pytest.raises(InitializeError):
        configuration.reload()


def test_set_option(configuration: Configuration) -> None:
    """
    must set option correctly
    """
    configuration.set_option("settings", "option", "value")
    assert configuration.get("settings", "option") == "value"


def test_set_option_new_section(configuration: Configuration) -> None:
    """
    must set option correctly even if no section found
    """
    configuration.set_option("section", "option", "value")
    assert configuration.get("section", "option") == "value"
