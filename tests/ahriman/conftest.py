import datetime
import pytest

from pathlib import Path
from pytest_mock import MockerFixture
from typing import Any, Dict, Type, TypeVar
from unittest.mock import MagicMock

from ahriman.core.auth.auth import Auth
from ahriman.core.configuration import Configuration
from ahriman.core.database.sqlite import SQLite
from ahriman.core.spawn import Spawn
from ahriman.core.status.watcher import Watcher
from ahriman.models.aur_package import AURPackage
from ahriman.models.build_status import BuildStatus, BuildStatusEnum
from ahriman.models.package import Package
from ahriman.models.package_description import PackageDescription
from ahriman.models.repository_paths import RepositoryPaths
from ahriman.models.result import Result
from ahriman.models.user import User
from ahriman.models.user_access import UserAccess


T = TypeVar("T")


# helpers
# https://stackoverflow.com/a/21611963
@pytest.helpers.register
def anyvar(cls: Type[T], strict: bool = False) -> T:
    """
    any value helper for mocker calls check

    Args:
        strict(bool, optional): if True then check type of supplied argument (Default value = False)

    Returns:
        T: any wrapper
    """
    class AnyVar(cls):
        """any value wrapper"""

        def __eq__(self, other: Any) -> bool:
            """
            compare object to other

            Args:
                other(Any): other object to compare

            Returns:
                bool: True in case if objects are equal
            """
            return not strict or isinstance(other, cls)

    return AnyVar()


@pytest.helpers.register
def get_package_status(package: Package) -> Dict[str, Any]:
    """
    helper to extract package status from package

    Args:
        package(Package): package object

    Returns:
        Dict[str, Any]: simplified package status map (with only status and view)
    """
    return {"status": BuildStatusEnum.Unknown.value, "package": package.view()}


@pytest.helpers.register
def get_package_status_extended(package: Package) -> Dict[str, Any]:
    """
    helper to extract package status from package

    Args:
        package(Package): package object

    Returns:
        Dict[str, Any]: full package status map (with timestamped build status and view)
    """
    return {"status": BuildStatus().view(), "package": package.view()}


# generic fixtures
@pytest.fixture
def aur_package_ahriman() -> AURPackage:
    """
    fixture for AUR package

    Returns:
        AURPackage: AUR package test instance
    """
    return AURPackage(
        id=1009791,
        name="ahriman",
        package_base_id=165427,
        package_base="ahriman",
        version="1.7.0-1",
        description="ArcH Linux ReposItory MANager",
        num_votes=0,
        popularity=0,
        first_submitted=datetime.datetime(2021, 4, 9, 22, 44, 45),
        last_modified=datetime.datetime(2021, 12, 25, 23, 11, 11),
        url_path="/cgit/aur.git/snapshot/ahriman.tar.gz",
        url="https://github.com/arcan1s/ahriman",
        out_of_date=None,
        maintainer="arcanis",
        depends=[
            "devtools",
            "git",
            "pyalpm",
            "python-aur",
            "python-passlib",
            "python-srcinfo",
        ],
        make_depends=["python-pip"],
        opt_depends=[
            "breezy",
            "darcs",
            "mercurial",
            "python-aioauth-client",
            "python-aiohttp",
            "python-aiohttp-debugtoolbar",
            "python-aiohttp-jinja2",
            "python-aiohttp-security",
            "python-aiohttp-session",
            "python-boto3",
            "python-cryptography",
            "python-jinja",
            "rsync",
            "subversion",
        ],
        conflicts=[],
        provides=[],
        license=["GPL3"],
        keywords=[],
    )


@pytest.fixture
def aur_package_akonadi() -> AURPackage:
    """
    fixture for AUR package

    Returns:
        AURPackage: AUR package test instance
    """
    return AURPackage(
        id=0,
        name="akonadi",
        package_base_id=0,
        package_base="akonadi",
        version="21.12.3-2",
        description="PIM layer, which provides an asynchronous API to access all kind of PIM data",
        num_votes=0,
        popularity=0,
        first_submitted=datetime.datetime(1970, 1, 1, 0, 0, 0),
        last_modified=datetime.datetime(2022, 3, 6, 8, 39, 50, 610000),
        url_path="",
        url="https://kontact.kde.org",
        out_of_date=None,
        maintainer="felixonmars",
        depends=[
            "libakonadi",
            "mariadb",
        ],
        make_depends=[
            "boost",
            "doxygen",
            "extra-cmake-modules",
            "kaccounts-integration",
            "kitemmodels",
            "postgresql",
            "qt5-tools",
        ],
        opt_depends=[
            "postgresql: PostgreSQL backend",
        ],
        conflicts=[],
        provides=[],
        license=["LGPL"],
        keywords=[],
    )


@pytest.fixture
def auth(configuration: Configuration) -> Auth:
    """
    auth provider fixture

    Args:
        configuration(Configuration): configuration fixture

    Returns:
        Auth: auth service instance
    """
    return Auth(configuration)


@pytest.fixture
def configuration(resource_path_root: Path) -> Configuration:
    """
    configuration fixture

    Args:
        resource_path_root(Path): resource path root directory

    Returns:
        Configuration: configuration test instance
    """
    path = resource_path_root / "core" / "ahriman.ini"
    return Configuration.from_path(path=path, architecture="x86_64", quiet=False)


@pytest.fixture
def database(configuration: Configuration) -> SQLite:
    """
    database fixture

    Args:
        configuration(Configuration): configuration fixture

    Returns:
        SQLite: database test instance
    """
    database = SQLite.load(configuration)
    yield database
    database.path.unlink()


@pytest.fixture
def package_ahriman(package_description_ahriman: PackageDescription) -> Package:
    """
    package fixture

    Args:
        package_description_ahriman(PackageDescription): description fixture

    Returns:
        Package: package test instance
    """
    packages = {"ahriman": package_description_ahriman}
    return Package(
        base="ahriman",
        version="1.7.0-1",
        aur_url="https://aur.archlinux.org",
        packages=packages)


@pytest.fixture
def package_python_schedule(
        package_description_python_schedule: PackageDescription,
        package_description_python2_schedule: PackageDescription) -> Package:
    """
    multi package fixture

    Args:
        package_description_python_schedule(PackageDescription): description fixture
        package_description_python2_schedule(PackageDescription): description fixture

    Returns:
        Package: multi package test instance
    """
    packages = {
        "python-schedule": package_description_python_schedule,
        "python2-schedule": package_description_python2_schedule
    }
    return Package(
        base="python-schedule",
        version="1.0.0-2",
        aur_url="https://aur.archlinux.org",
        packages=packages)


@pytest.fixture
def package_description_ahriman() -> PackageDescription:
    """
    package description fixture

    Returns:
        PackageDescription: package description test instance
    """
    return PackageDescription(
        architecture="x86_64",
        archive_size=4200,
        build_date=42,
        depends=[
            "devtools",
            "git",
            "pyalpm",
            "python-aur",
            "python-passlib",
            "python-srcinfo",
        ],
        description="ArcH Linux ReposItory MANager",
        filename="ahriman-1.7.0-1-any.pkg.tar.zst",
        groups=[],
        installed_size=4200000,
        licenses=["GPL3"],
        url="https://github.com/arcan1s/ahriman")


@pytest.fixture
def package_description_python_schedule() -> PackageDescription:
    """
    package description fixture

    Returns:
        PackageDescription: package description test instance
    """
    return PackageDescription(
        architecture="x86_64",
        archive_size=4201,
        build_date=421,
        depends=["python"],
        description="Python job scheduling for humans.",
        filename="python-schedule-1.0.0-2-any.pkg.tar.zst",
        groups=[],
        installed_size=4200001,
        licenses=["MIT"],
        url="https://github.com/dbader/schedule")


@pytest.fixture
def package_description_python2_schedule() -> PackageDescription:
    """
    package description fixture

    Returns:
        PackageDescription: package description test instance
    """
    return PackageDescription(
        architecture="x86_64",
        archive_size=4202,
        build_date=422,
        depends=["python2"],
        description="Python job scheduling for humans.",
        filename="python2-schedule-1.0.0-2-any.pkg.tar.zst",
        groups=[],
        installed_size=4200002,
        licenses=["MIT"],
        url="https://github.com/dbader/schedule")


@pytest.fixture
def repository_paths(configuration: Configuration) -> RepositoryPaths:
    """
    repository paths fixture

    Args:
        configuration(Configuration): configuration fixture

    Returns:
        RepositoryPaths: repository paths test instance
    """
    return configuration.repository_paths


@pytest.fixture
def result(package_ahriman: Package) -> Result:
    """
    result fixture

    Args:
        package_ahriman(Package): package fixture

    Returns:
        Result: result test instance
    """
    result = Result()
    result.add_success(package_ahriman)
    return result


@pytest.fixture
def spawner(configuration: Configuration) -> Spawn:
    """
    spawner fixture

    Args:
        configuration(Configuration): configuration fixture

    Returns:
        Spawn: spawner fixture
    """
    return Spawn(MagicMock(), "x86_64", configuration)


@pytest.fixture
def user() -> User:
    """
    fixture for user descriptor

    Returns:
        User: user descriptor instance
    """
    return User("user", "pa55w0rd", UserAccess.Read)


@pytest.fixture
def watcher(configuration: Configuration, database: SQLite, mocker: MockerFixture) -> Watcher:
    """
    package status watcher fixture

    Args:
        configuration(Configuration): configuration fixture
        database(SQLite): database fixture
        mocker(MockerFixture): mocker object

    Returns:
        Watcher: package status watcher test instance
    """
    mocker.patch("ahriman.models.repository_paths.RepositoryPaths.tree_create")
    return Watcher("x86_64", configuration, database)
