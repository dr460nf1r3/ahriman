from pytest_mock import MockerFixture
from unittest.mock import call as MockCall

from ahriman.core.configuration import Configuration
from ahriman.core.database import SQLite
from ahriman.core.sign.gpg import GPG
from ahriman.core.support import KeyringTrigger
from ahriman.models.context_key import ContextKey


def test_configuration_sections(configuration: Configuration) -> None:
    """
    must correctly parse target list
    """
    configuration.set_option("keyring", "target", "a b c")
    assert KeyringTrigger.configuration_sections(configuration) == ["a", "b", "c"]

    configuration.remove_option("keyring", "target")
    assert KeyringTrigger.configuration_sections(configuration) == []


def test_on_start(configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must run report for specified targets
    """
    context_mock = mocker.patch("ahriman.core._Context.get")
    run_mock = mocker.patch("ahriman.core.support.package_creator.PackageCreator.run")

    trigger = KeyringTrigger("x86_64", configuration)
    trigger.on_start()
    context_mock.assert_has_calls([MockCall(ContextKey("sign", GPG)), MockCall(ContextKey("database", SQLite))])
    run_mock.assert_called_once_with()
