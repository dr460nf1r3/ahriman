import argparse
import pytest

from pytest_mock import MockerFixture

from ahriman.application.handlers import Add
from ahriman.core.configuration import Configuration
from ahriman.core.repository import Repository
from ahriman.models.package import Package
from ahriman.models.package_source import PackageSource
from ahriman.models.packagers import Packagers
from ahriman.models.result import Result


def _default_args(args: argparse.Namespace) -> argparse.Namespace:
    """
    default arguments for these test cases

    Args:
        args(argparse.Namespace): command line arguments fixture

    Returns:
        argparse.Namespace: generated arguments for these test cases
    """
    args.package = []
    args.exit_code = False
    args.increment = True
    args.now = False
    args.refresh = 0
    args.source = PackageSource.Auto
    args.dependencies = True
    args.username = "username"
    return args


def test_run(args: argparse.Namespace, configuration: Configuration, repository: Repository,
             mocker: MockerFixture) -> None:
    """
    must run command
    """
    args = _default_args(args)
    mocker.patch("ahriman.core.repository.Repository.load", return_value=repository)
    application_mock = mocker.patch("ahriman.application.application.Application.add")
    dependencies_mock = mocker.patch("ahriman.application.application.Application.with_dependencies")
    on_start_mock = mocker.patch("ahriman.application.application.Application.on_start")

    Add.run(args, "x86_64", configuration, report=False)
    application_mock.assert_called_once_with(args.package, args.source, args.username)
    dependencies_mock.assert_not_called()
    on_start_mock.assert_called_once_with()


def test_run_with_updates(args: argparse.Namespace, configuration: Configuration, repository: Repository,
                          package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must run command with updates after
    """
    args = _default_args(args)
    args.now = True
    result = Result()
    result.add_success(package_ahriman)
    mocker.patch("ahriman.application.application.Application.add")
    mocker.patch("ahriman.core.repository.Repository.load", return_value=repository)
    application_mock = mocker.patch("ahriman.application.application.Application.update", return_value=result)
    check_mock = mocker.patch("ahriman.application.handlers.Handler.check_if_empty")
    updates_mock = mocker.patch("ahriman.application.application.Application.updates", return_value=[package_ahriman])
    dependencies_mock = mocker.patch("ahriman.application.application.Application.with_dependencies",
                                     return_value=[package_ahriman])
    print_mock = mocker.patch("ahriman.application.application.Application.print_updates")

    Add.run(args, "x86_64", configuration, report=False)
    updates_mock.assert_called_once_with(args.package, aur=False, local=False, manual=True, vcs=False)
    application_mock.assert_called_once_with([package_ahriman],
                                             Packagers(args.username, {package_ahriman.base: "packager"}),
                                             bump_pkgrel=args.increment)
    dependencies_mock.assert_called_once_with([package_ahriman], process_dependencies=args.dependencies)
    check_mock.assert_called_once_with(False, False)
    print_mock.assert_called_once_with([package_ahriman], log_fn=pytest.helpers.anyvar(int))


def test_run_empty_exception(args: argparse.Namespace, configuration: Configuration, repository: Repository,
                             mocker: MockerFixture) -> None:
    """
    must raise ExitCode exception on empty result
    """
    args = _default_args(args)
    args.now = True
    args.exit_code = True
    mocker.patch("ahriman.application.application.Application.add")
    mocker.patch("ahriman.core.repository.Repository.load", return_value=repository)
    mocker.patch("ahriman.application.application.Application.update", return_value=Result())
    mocker.patch("ahriman.application.application.Application.with_dependencies")
    mocker.patch("ahriman.application.application.Application.updates")
    mocker.patch("ahriman.application.application.Application.print_updates")
    check_mock = mocker.patch("ahriman.application.handlers.Handler.check_if_empty")

    Add.run(args, "x86_64", configuration, report=False)
    check_mock.assert_called_once_with(True, True)
