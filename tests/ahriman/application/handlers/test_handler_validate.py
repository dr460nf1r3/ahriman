import argparse
import json

from pytest_mock import MockerFixture

from ahriman.application.handlers import Validate
from ahriman.core.configuration import Configuration
from ahriman.core.configuration.schema import CONFIGURATION_SCHEMA
from ahriman.core.configuration.validator import Validator
from ahriman.core.gitremote import RemotePullTrigger, RemotePushTrigger


def _default_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    default arguments for these test cases

    Args:
        args(argparse.Namespace): command line arguments fixture

    Returns:
        argparse.Namespace: generated arguments for these test cases
    """
    args.exit_code = False
    return args


def test_run(args: argparse.Namespace, configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must run command
    """
    args = _default_args(args)
    mocker.patch.object(Validator, "errors", {"node": ["error"]})
    print_mock = mocker.patch("ahriman.core.formatters.Printer.print")
    application_mock = mocker.patch("ahriman.core.configuration.validator.Validator.validate", return_value=False)

    Validate.run(args, "x86_64", configuration, report=False, unsafe=False)

    application_mock.assert_called_once_with(configuration.dump())
    print_mock.assert_called_once_with(verbose=True)


def test_run_skip(args: argparse.Namespace, configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must skip print if no errors found
    """
    args = _default_args(args)
    mocker.patch("ahriman.core.configuration.validator.Validator.validate", return_value=True)
    print_mock = mocker.patch("ahriman.core.formatters.Printer.print")

    Validate.run(args, "x86_64", configuration, report=False, unsafe=False)
    print_mock.assert_not_called()


def test_schema(configuration: Configuration) -> None:
    """
    must generate full schema correctly
    """
    schema = Validate.schema("x86_64", configuration)

    # defaults
    assert schema.pop("console")
    assert schema.pop("email")
    assert schema.pop("github")
    assert schema.pop("gitremote")
    assert schema.pop("html")
    assert schema.pop("keyring")
    assert schema.pop("keyring_generator")
    assert schema.pop("mirrorlist")
    assert schema.pop("mirrorlist_generator")
    assert schema.pop("remote-pull")
    assert schema.pop("remote-push")
    assert schema.pop("report")
    assert schema.pop("rsync")
    assert schema.pop("s3")
    assert schema.pop("telegram")
    assert schema.pop("upload")

    assert schema == CONFIGURATION_SCHEMA


def test_schema_invalid_trigger(configuration: Configuration) -> None:
    """
    must skip trigger if it caused exception on load
    """
    configuration.set_option("build", "triggers", "some.invalid.trigger.path.Trigger")
    configuration.remove_option("build", "triggers_known")
    assert Validate.schema("x86_64", configuration) == CONFIGURATION_SCHEMA


def test_schema_erase_required() -> None:
    """
    must remove required field from dictionaries recursively
    """
    # the easiest way is to just dump to string and check
    assert "required" not in json.dumps(Validate.schema_erase_required(CONFIGURATION_SCHEMA))


def test_schema_merge() -> None:
    """
    must merge schemas correctly
    """
    erased = Validate.schema_erase_required(CONFIGURATION_SCHEMA)
    assert Validate.schema_merge(erased, CONFIGURATION_SCHEMA) == CONFIGURATION_SCHEMA

    merged = Validate.schema_merge(RemotePullTrigger.CONFIGURATION_SCHEMA, RemotePushTrigger.CONFIGURATION_SCHEMA)
    for key in RemotePullTrigger.CONFIGURATION_SCHEMA["gitremote"]["schema"]:
        assert key in merged["gitremote"]["schema"]
    for key in RemotePushTrigger.CONFIGURATION_SCHEMA["gitremote"]["schema"]:
        assert key in merged["gitremote"]["schema"]


def test_disallow_auto_architecture_run() -> None:
    """
    must not allow multi architecture run
    """
    assert not Validate.ALLOW_AUTO_ARCHITECTURE_RUN
