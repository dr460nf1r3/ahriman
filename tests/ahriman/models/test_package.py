import pytest

from pathlib import Path
from pytest_mock import MockerFixture
from srcinfo.parse import parse_srcinfo
from unittest.mock import MagicMock

from ahriman.core.alpm.pacman import Pacman
from ahriman.core.exceptions import PackageInfoError
from ahriman.core.util import utcnow
from ahriman.models.aur_package import AURPackage
from ahriman.models.package import Package
from ahriman.models.package_description import PackageDescription
from ahriman.models.repository_paths import RepositoryPaths


def test_depends(package_python_schedule: Package) -> None:
    """
    must return combined list of dependencies
    """
    assert all(
        set(package_python_schedule.depends).intersection(package.depends)
        for package in package_python_schedule.packages.values()
    )


def test_depends_build(package_ahriman: Package, package_python_schedule: Package) -> None:
    """
    must return full list of packages required for build
    """
    assert all(
        set(package_ahriman.depends_build).intersection(package.depends)
        for package in package_ahriman.packages.values()
    )
    assert all(
        set(package_ahriman.depends_build).intersection(package.make_depends)
        for package in package_ahriman.packages.values()
    )
    assert all(
        set(package_ahriman.depends_build).intersection(package.check_depends)
        for package in package_ahriman.packages.values()
    )

    assert all(
        set(package_python_schedule.depends_build).intersection(package.depends)
        for package in package_python_schedule.packages.values()
    )
    # there is no make dependencies for python-schedule


def test_depends_build_with_version_and_overlap(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must load correct list of dependencies with version
    """

    srcinfo = (resource_path_root / "models" / "package_gcc10_srcinfo").read_text()
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)

    package_gcc10 = Package.from_build(Path("local"), "x86_64", None)
    assert package_gcc10.depends_build == {
        "glibc", "zstd",  # depends
        "doxygen", "binutils", "git", "libmpc", "python",  # make depends
        "dejagnu", "inetutils",  # check depends
    }


def test_depends_check(package_ahriman: Package) -> None:
    """
    must return list of test dependencies
    """
    assert all(
        set(package_ahriman.depends_check).intersection(package.check_depends)
        for package in package_ahriman.packages.values()
    )


def test_depends_make(package_ahriman: Package) -> None:
    """
    must return list of make dependencies
    """
    assert all(
        set(package_ahriman.depends_make).intersection(package.make_depends)
        for package in package_ahriman.packages.values()
    )


def test_depends_opt(package_ahriman: Package) -> None:
    """
    must return list of optional dependencies
    """
    assert all(
        set(package_ahriman.depends_opt).intersection(package.opt_depends)
        for package in package_ahriman.packages.values()
    )


def test_groups(package_ahriman: Package) -> None:
    """
    must return list of groups for each package
    """
    assert all(
        all(group in package_ahriman.groups for group in package.groups)
        for package in package_ahriman.packages.values()
    )
    assert sorted(package_ahriman.groups) == package_ahriman.groups


def test_is_single_package_false(package_python_schedule: Package) -> None:
    """
    python-schedule must not be single package
    """
    assert not package_python_schedule.is_single_package


def test_is_single_package_true(package_ahriman: Package) -> None:
    """
    ahriman must be single package
    """
    assert package_ahriman.is_single_package


def test_is_vcs_false(package_ahriman: Package) -> None:
    """
    ahriman must not be VCS package
    """
    assert not package_ahriman.is_vcs


def test_is_vcs_true(package_tpacpi_bat_git: Package) -> None:
    """
    tpacpi-bat-git must be VCS package
    """
    assert package_tpacpi_bat_git.is_vcs


def test_licenses(package_ahriman: Package) -> None:
    """
    must return list of licenses for each package
    """
    assert all(
        all(lic in package_ahriman.licenses for lic in package.licenses)
        for package in package_ahriman.packages.values()
    )
    assert sorted(package_ahriman.licenses) == package_ahriman.licenses


def test_packages_full(package_ahriman: Package) -> None:
    """
    must return full list of packages including provides
    """
    package_ahriman.packages[package_ahriman.base].provides = [f"{package_ahriman.base}-git"]
    assert package_ahriman.packages_full == [package_ahriman.base, f"{package_ahriman.base}-git"]


def test_from_archive(package_ahriman: Package, pyalpm_handle: MagicMock, mocker: MockerFixture) -> None:
    """
    must construct package from alpm library
    """
    mocker.patch("ahriman.models.package_description.PackageDescription.from_package",
                 return_value=package_ahriman.packages[package_ahriman.base])
    generated = Package.from_archive(Path("path"), pyalpm_handle)
    generated.remote = package_ahriman.remote

    assert generated == package_ahriman


def test_from_aur(package_ahriman: Package, aur_package_ahriman: AURPackage, pacman: Pacman,
                  mocker: MockerFixture) -> None:
    """
    must construct package from aur
    """
    mocker.patch("ahriman.core.alpm.remote.AUR.info", return_value=aur_package_ahriman)

    package = Package.from_aur(package_ahriman.base, pacman, package_ahriman.packager)
    assert package_ahriman.base == package.base
    assert package_ahriman.version == package.version
    assert package_ahriman.packages.keys() == package.packages.keys()
    assert package_ahriman.packager == package.packager


def test_from_build(package_ahriman: Package, mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must construct package from srcinfo
    """
    srcinfo = (resource_path_root / "models" / "package_ahriman_srcinfo").read_text()
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)

    package = Package.from_build(Path("path"), "x86_64", "packager")
    assert package_ahriman.packages.keys() == package.packages.keys()
    package_ahriman.packages = package.packages  # we are not going to test PackageDescription here
    package_ahriman.remote = package.remote
    assert package_ahriman == package


def test_from_build_multiple_packages(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must construct package from srcinfo with dependencies per-package overrides
    """
    srcinfo = (resource_path_root / "models" / "package_gcc10_srcinfo").read_text()
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)

    package = Package.from_build(Path("path"), "x86_64", None)
    assert package.packages == {
        "gcc10": PackageDescription(
            depends=["gcc10-libs=10.3.0-2", "binutils>=2.28", "libmpc", "zstd"],
            make_depends=["binutils", "doxygen", "git", "libmpc", "python"],
            opt_depends=[],
            check_depends=["dejagnu", "inetutils"],
        ),
        "gcc10-libs": PackageDescription(
            depends=["glibc>=2.27"],
            make_depends=["binutils", "doxygen", "git", "libmpc", "python"],
            opt_depends=[],
            check_depends=["dejagnu", "inetutils"],
        ),
        "gcc10-fortran": PackageDescription(
            depends=["gcc10=10.3.0-2"],
            make_depends=["binutils", "doxygen", "git", "libmpc", "python"],
            opt_depends=[],
            check_depends=["dejagnu", "inetutils"],
        ),
    }


def test_from_build_architecture(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must construct package with architecture specific depends list
    """
    srcinfo = (resource_path_root / "models" / "package_jellyfin-ffmpeg5-bin_srcinfo").read_text()
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)

    package = Package.from_build(Path("path"), "x86_64", None)
    assert package.packages == {
        "jellyfin-ffmpeg5-bin": PackageDescription(
            depends=["glibc"],
            make_depends=[],
            opt_depends=[
                "intel-media-driver: for Intel VAAPI support (Broadwell and newer)",
                "intel-media-sdk: for Intel Quick Sync Video",
                "onevpl-intel-gpu: for Intel Quick Sync Video (12th Gen and newer)",
                "intel-compute-runtime: for Intel OpenCL runtime based Tonemapping",
                "libva-intel-driver: for Intel legacy VAAPI support (10th Gen and older)",
                "libva-mesa-driver: for AMD VAAPI support",
                "nvidia-utils: for Nvidia NVDEC/NVENC support",
                "opencl-amd: for AMD OpenCL runtime based Tonemapping",
                "vulkan-radeon: for AMD RADV Vulkan support",
                "vulkan-intel: for Intel ANV Vulkan support",
            ],
        ),
    }


def test_from_build_failed(package_ahriman: Package, mocker: MockerFixture) -> None:
    """
    must raise exception if there are errors during srcinfo load
    """
    mocker.patch("ahriman.models.package.Package._check_output", return_value="")
    mocker.patch("ahriman.models.package.parse_srcinfo", return_value=({"packages": {}}, ["an error"]))

    with pytest.raises(PackageInfoError):
        Package.from_build(Path("path"), "x86_64", None)


def test_from_json_view_1(package_ahriman: Package) -> None:
    """
    must construct same object from json
    """
    assert Package.from_json(package_ahriman.view()) == package_ahriman


def test_from_json_view_2(package_python_schedule: Package) -> None:
    """
    must construct same object from json
    """
    assert Package.from_json(package_python_schedule.view()) == package_python_schedule


def test_from_json_view_3(package_tpacpi_bat_git: Package) -> None:
    """
    must construct same object from json
    """
    assert Package.from_json(package_tpacpi_bat_git.view()) == package_tpacpi_bat_git


def test_from_official(package_ahriman: Package, aur_package_ahriman: AURPackage, pacman: Pacman,
                       mocker: MockerFixture) -> None:
    """
    must construct package from official repository
    """
    mocker.patch("ahriman.core.alpm.remote.Official.info", return_value=aur_package_ahriman)

    package = Package.from_official(package_ahriman.base, pacman, package_ahriman.packager)
    assert package_ahriman.base == package.base
    assert package_ahriman.version == package.version
    assert package_ahriman.packages.keys() == package.packages.keys()
    assert package_ahriman.packager == package.packager


def test_local_files(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must extract local file sources
    """
    srcinfo = (resource_path_root / "models" / "package_yay_srcinfo").read_text()
    parsed_srcinfo, _ = parse_srcinfo(srcinfo)
    parsed_srcinfo["source"] = ["local-file.tar.gz"]
    mocker.patch("ahriman.models.package.parse_srcinfo", return_value=(parsed_srcinfo, []))
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)
    mocker.patch("ahriman.models.package.Package.supported_architectures", return_value=["any"])

    assert list(Package.local_files(Path("path"))) == [Path("local-file.tar.gz")]


def test_local_files_empty(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must extract empty local files list when there is no local files
    """
    srcinfo = (resource_path_root / "models" / "package_yay_srcinfo").read_text()
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)
    mocker.patch("ahriman.models.package.Package.supported_architectures", return_value=["any"])

    assert list(Package.local_files(Path("path"))) == []


def test_local_files_error(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must raise exception on package parsing for local sources
    """
    mocker.patch("ahriman.models.package.Package._check_output", return_value="")
    mocker.patch("ahriman.models.package.parse_srcinfo", return_value=({"packages": {}}, ["an error"]))

    with pytest.raises(PackageInfoError):
        list(Package.local_files(Path("path")))


def test_local_files_schema(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must skip local file source when file schema is used
    """
    srcinfo = (resource_path_root / "models" / "package_yay_srcinfo").read_text()
    parsed_srcinfo, _ = parse_srcinfo(srcinfo)
    parsed_srcinfo["source"] = ["file:///local-file.tar.gz"]
    mocker.patch("ahriman.models.package.parse_srcinfo", return_value=(parsed_srcinfo, []))
    mocker.patch("ahriman.models.package.Package._check_output", return_value="")
    mocker.patch("ahriman.models.package.Package.supported_architectures", return_value=["any"])

    assert list(Package.local_files(Path("path"))) == []


def test_local_files_with_install(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must extract local file sources with install file
    """
    srcinfo = (resource_path_root / "models" / "package_yay_srcinfo").read_text()
    parsed_srcinfo, _ = parse_srcinfo(srcinfo)
    parsed_srcinfo["install"] = "install"
    mocker.patch("ahriman.models.package.parse_srcinfo", return_value=(parsed_srcinfo, []))
    mocker.patch("ahriman.models.package.Package._check_output", return_value="")
    mocker.patch("ahriman.models.package.Package.supported_architectures", return_value=["any"])

    assert list(Package.local_files(Path("path"))) == [Path("install")]


def test_supported_architectures(mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must generate list of available architectures
    """
    srcinfo = (resource_path_root / "models" / "package_yay_srcinfo").read_text()
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)
    assert Package.supported_architectures(Path("path")) == \
        {"i686", "pentium4", "x86_64", "arm", "armv7h", "armv6h", "aarch64"}


def test_supported_architectures_failed(mocker: MockerFixture) -> None:
    """
    must raise exception if there are errors during srcinfo load for architectures
    """
    mocker.patch("ahriman.models.package.Package._check_output", return_value="")
    mocker.patch("ahriman.models.package.parse_srcinfo", return_value=({"packages": {}}, ["an error"]))

    with pytest.raises(PackageInfoError):
        Package.supported_architectures(Path("path"))


def test_actual_version(package_ahriman: Package, repository_paths: RepositoryPaths) -> None:
    """
    must return same actual_version as version is
    """
    assert package_ahriman.actual_version(repository_paths) == package_ahriman.version


def test_actual_version_vcs(package_tpacpi_bat_git: Package, repository_paths: RepositoryPaths,
                            mocker: MockerFixture, resource_path_root: Path) -> None:
    """
    must return valid actual_version for VCS package
    """
    srcinfo = (resource_path_root / "models" / "package_tpacpi-bat-git_srcinfo").read_text()
    mocker.patch("ahriman.models.package.Package._check_output", return_value=srcinfo)
    mocker.patch("ahriman.core.build_tools.sources.Sources.load")

    assert package_tpacpi_bat_git.actual_version(repository_paths) == "3.1.r13.g4959b52-1"


def test_actual_version_srcinfo_failed(package_tpacpi_bat_git: Package, repository_paths: RepositoryPaths,
                                       mocker: MockerFixture) -> None:
    """
    must return same version in case if exception occurred
    """
    mocker.patch("ahriman.models.package.Package._check_output", side_effect=Exception())
    mocker.patch("ahriman.core.build_tools.sources.Sources.load")

    assert package_tpacpi_bat_git.actual_version(repository_paths) == package_tpacpi_bat_git.version


def test_actual_version_vcs_failed(package_tpacpi_bat_git: Package, repository_paths: RepositoryPaths,
                                   mocker: MockerFixture) -> None:
    """
    must return same version in case if there are errors during parse
    """
    mocker.patch("pathlib.Path.read_text", return_value="")
    mocker.patch("ahriman.models.package.parse_srcinfo", return_value=({"packages": {}}, ["an error"]))
    mocker.patch("ahriman.models.package.Package._check_output")
    mocker.patch("ahriman.core.build_tools.sources.Sources.load")

    assert package_tpacpi_bat_git.actual_version(repository_paths) == package_tpacpi_bat_git.version


def test_full_depends(package_ahriman: Package, package_python_schedule: Package, pyalpm_package_ahriman: MagicMock,
                      pyalpm_handle: MagicMock) -> None:
    """
    must extract all dependencies from the package
    """
    package_python_schedule.packages[package_python_schedule.base].provides = ["python3-schedule"]

    database_mock = MagicMock()
    database_mock.pkgcache = [pyalpm_package_ahriman]
    pyalpm_handle.handle.get_syncdbs.return_value = [database_mock]

    assert package_ahriman.full_depends(pyalpm_handle, [package_python_schedule]) == package_ahriman.depends

    package_python_schedule.packages[package_python_schedule.base].depends = [package_ahriman.base]
    expected = sorted(set(package_python_schedule.depends + package_ahriman.depends))
    assert package_python_schedule.full_depends(pyalpm_handle, [package_python_schedule]) == expected


def test_is_newer_than(package_ahriman: Package, package_python_schedule: Package) -> None:
    """
    must correctly check if package is newer than specified timestamp
    """
    # base checks, true/false
    assert package_ahriman.is_newer_than(package_ahriman.packages[package_ahriman.base].build_date - 1)
    assert not package_ahriman.is_newer_than(package_ahriman.packages[package_ahriman.base].build_date + 1)

    # list check
    min_date = min(package.build_date for package in package_python_schedule.packages.values())
    assert package_python_schedule.is_newer_than(min_date)

    # null list check
    package_python_schedule.packages["python-schedule"].build_date = None
    assert package_python_schedule.is_newer_than(min_date)

    package_python_schedule.packages["python2-schedule"].build_date = None
    assert not package_python_schedule.is_newer_than(min_date)


def test_is_outdated_false(package_ahriman: Package, repository_paths: RepositoryPaths, mocker: MockerFixture) -> None:
    """
    must be not outdated for the same package
    """
    actual_version_mock = mocker.patch("ahriman.models.package.Package.actual_version",
                                       return_value=package_ahriman.version)
    assert not package_ahriman.is_outdated(package_ahriman, repository_paths)
    actual_version_mock.assert_called_once_with(repository_paths)


def test_is_outdated_true(package_ahriman: Package, repository_paths: RepositoryPaths, mocker: MockerFixture) -> None:
    """
    must be outdated for the new version
    """
    other = Package.from_json(package_ahriman.view())
    other.version = other.version.replace("-1", "-2")
    actual_version_mock = mocker.patch("ahriman.models.package.Package.actual_version", return_value=other.version)

    assert package_ahriman.is_outdated(other, repository_paths)
    actual_version_mock.assert_called_once_with(repository_paths)


def test_is_outdated_no_version_calculation(package_ahriman: Package, repository_paths: RepositoryPaths,
                                            mocker: MockerFixture) -> None:
    """
    must not call actual version if calculation is disabled
    """
    actual_version_mock = mocker.patch("ahriman.models.package.Package.actual_version")
    assert not package_ahriman.is_outdated(package_ahriman, repository_paths, calculate_version=False)
    actual_version_mock.assert_not_called()


def test_is_outdated_fresh_package(package_ahriman: Package, repository_paths: RepositoryPaths,
                                   mocker: MockerFixture) -> None:
    """
    must not call actual version if package is never than specified time
    """
    actual_version_mock = mocker.patch("ahriman.models.package.Package.actual_version")
    assert not package_ahriman.is_outdated(package_ahriman, repository_paths, vcs_allowed_age=utcnow().timestamp())
    actual_version_mock.assert_not_called()


def test_next_pkgrel(package_ahriman: Package) -> None:
    """
    must correctly bump pkgrel
    """
    assert package_ahriman.next_pkgrel(package_ahriman.version) == "1.1"

    package_ahriman.version = "1.0.0-1.1"
    assert package_ahriman.next_pkgrel(package_ahriman.version) == "1.2"

    package_ahriman.version = "1.0.0-1.2.1"
    assert package_ahriman.next_pkgrel(package_ahriman.version) == "1.2.2"

    package_ahriman.version = "1:1.0.0-1"
    assert package_ahriman.next_pkgrel("1:1.0.1-1") is None
    assert package_ahriman.next_pkgrel("2:1.0.0-1") is None

    package_ahriman.version = "1.0.0-1.1"
    assert package_ahriman.next_pkgrel("1.0.1-2") is None
    assert package_ahriman.next_pkgrel("1.0.0-2") == "2.1"

    package_ahriman.version = "1.0.0-2"
    assert package_ahriman.next_pkgrel("1.0.0-1.1") is None


def test_build_status_pretty_print(package_ahriman: Package) -> None:
    """
    must return string in pretty print function
    """
    assert package_ahriman.pretty_print()
    assert isinstance(package_ahriman.pretty_print(), str)
