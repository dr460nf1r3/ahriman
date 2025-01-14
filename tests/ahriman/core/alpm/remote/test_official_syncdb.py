import pytest

from pytest_mock import MockerFixture

from ahriman.core.alpm.pacman import Pacman
from ahriman.core.alpm.remote import OfficialSyncdb
from ahriman.core.exceptions import UnknownPackageError
from ahriman.models.aur_package import AURPackage


def test_package_info(official_syncdb: OfficialSyncdb, aur_package_akonadi: AURPackage, pacman: Pacman,
                      mocker: MockerFixture) -> None:
    """
    must return package info from the database
    """
    mocker.patch("ahriman.models.aur_package.AURPackage.from_pacman", return_value=aur_package_akonadi)
    get_mock = mocker.patch("ahriman.core.alpm.pacman.Pacman.package_get", return_value=[aur_package_akonadi])

    package = official_syncdb.package_info(aur_package_akonadi.name, pacman=pacman)
    get_mock.assert_called_once_with(aur_package_akonadi.name)
    assert package == aur_package_akonadi


def test_package_info_not_found(official_syncdb: OfficialSyncdb, aur_package_akonadi: AURPackage, pacman: Pacman,
                                mocker: MockerFixture) -> None:
    """
    must raise UnknownPackage exception in case if no package was found
    """
    mocker.patch("ahriman.core.alpm.pacman.Pacman.package_get", return_value=[])
    with pytest.raises(UnknownPackageError, match=aur_package_akonadi.name):
        assert official_syncdb.package_info(aur_package_akonadi.name, pacman=pacman)
