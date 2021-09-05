import argparse

from pytest_mock import MockerFixture

from ahriman.application.handlers import KeyImport
from ahriman.core.configuration import Configuration


def _default_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    default arguments for these test cases
    :param args: command line arguments fixture
    :return: generated arguments for these test cases
    """
    args.key = "0xE989490C"
    args.key_server = "pgp.mit.edu"
    return args


def test_run(args: argparse.Namespace, configuration: Configuration, mocker: MockerFixture) -> None:
    """
    must run command
    """
    args = _default_args(args)
    mocker.patch("pathlib.Path.mkdir")
    application_mock = mocker.patch("ahriman.core.sign.gpg.GPG.import_key")

    KeyImport.run(args, "x86_64", configuration)
    application_mock.assert_called_once()
