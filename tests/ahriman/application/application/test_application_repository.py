import pytest

from pytest_mock import MockerFixture
from unittest import mock

from ahriman.application.application.repository import Repository
from ahriman.core.tree import Leaf, Tree
from ahriman.models.package import Package


def test_finalize(application_repository: Repository) -> None:
    """
    must raise NotImplemented for missing finalize method
    """
    with pytest.raises(NotImplementedError):
        application_repository._finalize([])


def test_clean_build(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must clean build directory
    """
    clear_mock = mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_build")
    application_repository.clean(True, False, False, False, False, False)
    clear_mock.assert_called_once()


def test_clean_cache(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must clean cache directory
    """
    clear_mock = mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_cache")
    application_repository.clean(False, True, False, False, False, False)
    clear_mock.assert_called_once()


def test_clean_chroot(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must clean chroot directory
    """
    clear_mock = mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_chroot")
    application_repository.clean(False, False, True, False, False, False)
    clear_mock.assert_called_once()


def test_clean_manual(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must clean manual directory
    """
    clear_mock = mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_manual")
    application_repository.clean(False, False, False, True, False, False)
    clear_mock.assert_called_once()


def test_clean_packages(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must clean packages directory
    """
    clear_mock = mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_packages")
    application_repository.clean(False, False, False, False, True, False)
    clear_mock.assert_called_once()


def test_clean_patches(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must clean packages directory
    """
    clear_mock = mocker.patch("ahriman.core.repository.cleaner.Cleaner.clear_patches")
    application_repository.clean(False, False, False, False, False, True)
    clear_mock.assert_called_once()


def test_report(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must generate report
    """
    executor_mock = mocker.patch("ahriman.core.repository.executor.Executor.process_report")
    application_repository.report([], [])
    executor_mock.assert_called_once()


def test_sign(application_repository: Repository, package_ahriman: Package, package_python_schedule: Package,
              mocker: MockerFixture) -> None:
    """
    must sign world
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages",
                 return_value=[package_ahriman, package_python_schedule])
    copy_mock = mocker.patch("shutil.copy")
    update_mock = mocker.patch("ahriman.application.application.repository.Repository.update")
    sign_repository_mock = mocker.patch("ahriman.core.sign.gpg.GPG.process_sign_repository")
    finalize_mock = mocker.patch("ahriman.application.application.repository.Repository._finalize")

    application_repository.sign([])
    copy_mock.assert_has_calls([
        mock.call(pytest.helpers.anyvar(str), pytest.helpers.anyvar(str)),
        mock.call(pytest.helpers.anyvar(str), pytest.helpers.anyvar(str))
    ])
    update_mock.assert_called_once_with([])
    sign_repository_mock.assert_called_once()
    finalize_mock.assert_called_once()


def test_sign_skip(application_repository: Repository, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must skip sign packages with empty filename
    """
    package_ahriman.packages[package_ahriman.base].filename = None
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[package_ahriman])
    mocker.patch("ahriman.application.application.repository.Repository.update")
    mocker.patch("ahriman.application.application.repository.Repository._finalize")

    application_repository.sign([])


def test_sign_specific(application_repository: Repository, package_ahriman: Package, package_python_schedule: Package,
                       mocker: MockerFixture) -> None:
    """
    must sign only specified packages
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages",
                 return_value=[package_ahriman, package_python_schedule])
    copy_mock = mocker.patch("shutil.copy")
    update_mock = mocker.patch("ahriman.application.application.repository.Repository.update")
    sign_repository_mock = mocker.patch("ahriman.core.sign.gpg.GPG.process_sign_repository")
    finalize_mock = mocker.patch("ahriman.application.application.repository.Repository._finalize")

    application_repository.sign([package_ahriman.base])
    copy_mock.assert_called_once()
    update_mock.assert_called_once_with([])
    sign_repository_mock.assert_called_once()
    finalize_mock.assert_called_once()


def test_sync(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must sync to remote
    """
    executor_mock = mocker.patch("ahriman.core.repository.executor.Executor.process_sync")
    application_repository.sync([], [])
    executor_mock.assert_called_once()


def test_unknown_no_aur(application_repository: Repository, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must return empty list in case if there is locally stored PKGBUILD
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[package_ahriman])
    mocker.patch("ahriman.models.package.Package.from_aur", side_effect=Exception())
    mocker.patch("pathlib.Path.is_dir", return_value=True)
    mocker.patch("ahriman.core.build_tools.sources.Sources.has_remotes", return_value=False)

    assert not application_repository.unknown()


def test_unknown_no_aur_no_local(application_repository: Repository, package_ahriman: Package,
                                 mocker: MockerFixture) -> None:
    """
    must return list of packages missing in aur and in local storage
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[package_ahriman])
    mocker.patch("ahriman.models.package.Package.from_aur", side_effect=Exception())
    mocker.patch("pathlib.Path.is_dir", return_value=False)

    packages = application_repository.unknown()
    assert packages == [package_ahriman]


def test_unknown_no_local(application_repository: Repository, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must return empty list in case if there is package in AUR
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[package_ahriman])
    mocker.patch("ahriman.models.package.Package.from_aur")
    mocker.patch("pathlib.Path.is_dir", return_value=False)

    assert not application_repository.unknown()


def test_update(application_repository: Repository, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must process package updates
    """
    paths = [package.filepath for package in package_ahriman.packages.values()]
    tree = Tree([Leaf(package_ahriman, set())])

    mocker.patch("ahriman.core.tree.Tree.load", return_value=tree)
    mocker.patch("ahriman.core.repository.repository.Repository.packages_built", return_value=[])
    mocker.patch("ahriman.models.package.Package.load", return_value=package_ahriman)
    build_mock = mocker.patch("ahriman.core.repository.executor.Executor.process_build", return_value=paths)
    update_mock = mocker.patch("ahriman.core.repository.executor.Executor.process_update")
    finalize_mock = mocker.patch("ahriman.application.application.repository.Repository._finalize")

    application_repository.update([package_ahriman])
    build_mock.assert_called_once()
    update_mock.assert_called_once_with(paths)
    finalize_mock.assert_called_once_with([package_ahriman])


def test_updates_all(application_repository: Repository, package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must get updates for all
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[])
    updates_aur_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_aur",
                                    return_value=[package_ahriman])
    updates_manual_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_manual")

    application_repository.updates([], no_aur=False, no_manual=False, no_vcs=False, log_fn=print)
    updates_aur_mock.assert_called_once_with([], False)
    updates_manual_mock.assert_called_once()


def test_updates_disabled(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must get updates without anything
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[])
    updates_aur_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_aur")
    updates_manual_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_manual")

    application_repository.updates([], no_aur=True, no_manual=True, no_vcs=False, log_fn=print)
    updates_aur_mock.assert_not_called()
    updates_manual_mock.assert_not_called()


def test_updates_no_aur(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must get updates without aur
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[])
    updates_aur_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_aur")
    updates_manual_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_manual")

    application_repository.updates([], no_aur=True, no_manual=False, no_vcs=False, log_fn=print)
    updates_aur_mock.assert_not_called()
    updates_manual_mock.assert_called_once()


def test_updates_no_manual(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must get updates without manual
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[])
    updates_aur_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_aur")
    updates_manual_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_manual")

    application_repository.updates([], no_aur=False, no_manual=True, no_vcs=False, log_fn=print)
    updates_aur_mock.assert_called_once_with([], False)
    updates_manual_mock.assert_not_called()


def test_updates_no_vcs(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must get updates without VCS
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[])
    updates_aur_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_aur")
    updates_manual_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_manual")

    application_repository.updates([], no_aur=False, no_manual=False, no_vcs=True, log_fn=print)
    updates_aur_mock.assert_called_once_with([], True)
    updates_manual_mock.assert_called_once()


def test_updates_with_filter(application_repository: Repository, mocker: MockerFixture) -> None:
    """
    must get updates without VCS
    """
    mocker.patch("ahriman.core.repository.repository.Repository.packages", return_value=[])
    updates_aur_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_aur")
    updates_manual_mock = mocker.patch("ahriman.core.repository.update_handler.UpdateHandler.updates_manual")

    application_repository.updates(["filter"], no_aur=False, no_manual=False, no_vcs=False, log_fn=print)
    updates_aur_mock.assert_called_once_with(["filter"], False)
    updates_manual_mock.assert_called_once()