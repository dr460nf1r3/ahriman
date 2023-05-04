#
# Copyright (c) 2021-2023 ahriman team.
#
# This file is part of ahriman
# (see https://github.com/arcan1s/ahriman).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# pylint: disable=too-many-lines,too-many-public-methods
from __future__ import annotations

import copy

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from pyalpm import vercmp  # type: ignore[import]
from srcinfo.parse import parse_srcinfo  # type: ignore[import]
from typing import Any, Self

from ahriman.core.alpm.pacman import Pacman
from ahriman.core.alpm.remote import AUR, Official, OfficialSyncdb
from ahriman.core.exceptions import PackageInfoError
from ahriman.core.log import LazyLogging
from ahriman.core.util import check_output, full_version, utcnow
from ahriman.models.package_description import PackageDescription
from ahriman.models.package_source import PackageSource
from ahriman.models.remote_source import RemoteSource
from ahriman.models.repository_paths import RepositoryPaths


@dataclass(kw_only=True)
class Package(LazyLogging):
    """
    package properties representation

    Attributes:
        base(str): package base name
        packages(dict[str, PackageDescription): map of package names to their properties.
            Filled only on load from archive
        remote(RemoteSource | None): package remote source if applicable
        version(str): package full version

    Examples:
        Different usages of this class may generate different (incomplete) data, e.g. if instantiating class from json::

            >>> package = Package.from_json(dump)

        it will contain every data available in the json body. Otherwise, if generate package from local archive::

            >>> package = Package.from_archive(local_path, pacman, remote=None)

        it will probably miss file descriptions (in case if there are multiple packages which belong to the base).

        The specific class load method must be defined based on the source provided. The following methods (mostly) must
        be used: ``from_archive``, ``from_aur``, ``from_build``, ``from_official`` for sources
        ``PackageSource.Archive``, ``PackageSource.AUR``, ``PackageSource.Local`` and ``PackageSource.Repository``
        repsectively:

            >>> ahriman_package = Package.from_aur("ahriman", pacman)
            >>> pacman_package = Package.from_official("pacman", pacman)
    """

    base: str
    version: str
    remote: RemoteSource | None
    packages: dict[str, PackageDescription]

    _check_output = check_output

    @property
    def depends(self) -> list[str]:
        """
        get package base dependencies

        Returns:
            list[str]: sum of dependencies per each package
        """
        return sorted(set(sum((package.depends for package in self.packages.values()), start=[])))

    @property
    def depends_build(self) -> set[str]:
        """
        get full list of external dependencies which has to be installed for build process

        Returns:
            set[str]: full dependencies list used by devtools
        """
        return (set(self.depends) | set(self.depends_make)).difference(self.packages_full)

    @property
    def depends_make(self) -> list[str]:
        """
        get package make dependencies

        Returns:
            list[str]: sum of make dependencies per each package
        """
        return sorted(set(sum((package.make_depends for package in self.packages.values()), start=[])))

    @property
    def depends_opt(self) -> list[str]:
        """
        get package optional dependencies

        Returns:
            list[str]: sum of optional dependencies per each package
        """
        return sorted(set(sum((package.opt_depends for package in self.packages.values()), start=[])))

    @property
    def groups(self) -> list[str]:
        """
        get package base groups

        Returns:
            list[str]: sum of groups per each package
        """
        return sorted(set(sum((package.groups for package in self.packages.values()), start=[])))

    @property
    def is_single_package(self) -> bool:
        """
        is it possible to transform package base to single package or not

        Returns:
            bool: true in case if this base has only one package with the same name
        """
        return self.base in self.packages and len(self.packages) == 1

    @property
    def is_vcs(self) -> bool:
        """
        get VCS flag based on the package base

        Returns:
            bool: True in case if package base looks like VCS package and False otherwise
        """
        return self.base.endswith("-bzr") \
            or self.base.endswith("-csv")\
            or self.base.endswith("-darcs")\
            or self.base.endswith("-git")\
            or self.base.endswith("-hg")\
            or self.base.endswith("-svn")

    @property
    def licenses(self) -> list[str]:
        """
        get package base licenses

        Returns:
            list[str]: sum of licenses per each package
        """
        return sorted(set(sum((package.licenses for package in self.packages.values()), start=[])))

    @property
    def packages_full(self) -> list[str]:
        """
        get full packages list including provides

        Returns:
            list[str]: full list of packages which this base contains
        """
        packages = set()
        for package, properties in self.packages.items():
            packages.add(package)
            packages.update(properties.provides)
        return sorted(packages)

    @classmethod
    def from_archive(cls, path: Path, pacman: Pacman, remote: RemoteSource | None) -> Self:
        """
        construct package properties from package archive

        Args:
            path(Path): path to package archive
            pacman(Pacman): alpm wrapper instance
            remote(RemoteSource): package remote source if applicable

        Returns:
            Self: package properties
        """
        package = pacman.handle.load_pkg(str(path))
        description = PackageDescription.from_package(package, path)
        return cls(base=package.base, version=package.version, remote=remote, packages={package.name: description})

    @classmethod
    def from_aur(cls, name: str, pacman: Pacman) -> Self:
        """
        construct package properties from AUR page

        Args:
            name(str): package name (either base or normal name)
            pacman(Pacman): alpm wrapper instance

        Returns:
            Self: package properties
        """
        package = AUR.info(name, pacman=pacman)
        remote = RemoteSource.from_source(PackageSource.AUR, package.package_base, package.repository)
        return cls(
            base=package.package_base,
            version=package.version,
            remote=remote,
            packages={package.name: PackageDescription.from_aur(package)})

    @classmethod
    def from_build(cls, path: Path, architecture: str) -> Self:
        """
        construct package properties from sources directory

        Args:
            path(Path): path to package sources directory
            architecture(str): load package for specific architecture

        Returns:
            Self: package properties

        Raises:
            InvalidPackageInfo: if there are parsing errors
        """
        srcinfo_source = Package._check_output("makepkg", "--printsrcinfo", cwd=path)
        srcinfo, errors = parse_srcinfo(srcinfo_source)
        if errors:
            raise PackageInfoError(errors)

        def get_property(key: str, properties: dict[str, Any], default: Any) -> Any:
            return properties.get(key) or srcinfo.get(key) or default

        def get_list(key: str, properties: dict[str, Any]) -> Any:
            return get_property(key, properties, []) + get_property(f"{key}_{architecture}", properties, [])

        packages = {
            package: PackageDescription(
                depends=get_list("depends", properties),
                make_depends=get_list("makedepends", properties),
                opt_depends=get_list("optdepends", properties),
            )
            for package, properties in srcinfo["packages"].items()
        }
        version = full_version(srcinfo.get("epoch"), srcinfo["pkgver"], srcinfo["pkgrel"])

        return cls(base=srcinfo["pkgbase"], version=version, remote=None, packages=packages)

    @classmethod
    def from_json(cls, dump: dict[str, Any]) -> Self:
        """
        construct package properties from json dump

        Args:
            dump(dict[str, Any]): json dump body

        Returns:
            Self: package properties
        """
        packages_json = dump.get("packages") or {}
        packages = {
            key: PackageDescription.from_json(value)
            for key, value in packages_json.items()
        }
        remote = dump.get("remote") or {}
        return cls(base=dump["base"], version=dump["version"], remote=RemoteSource.from_json(remote), packages=packages)

    @classmethod
    def from_official(cls, name: str, pacman: Pacman, *, use_syncdb: bool = True) -> Self:
        """
        construct package properties from official repository page

        Args:
            name(str): package name (either base or normal name)
            pacman(Pacman): alpm wrapper instance
            use_syncdb(bool, optional): use pacman databases instead of official repositories RPC (Default value = True)

        Returns:
            Self: package properties
        """
        package = OfficialSyncdb.info(name, pacman=pacman) if use_syncdb else Official.info(name, pacman=pacman)
        remote = RemoteSource.from_source(PackageSource.Repository, package.package_base, package.repository)
        return cls(
            base=package.package_base,
            version=package.version,
            remote=remote,
            packages={package.name: PackageDescription.from_aur(package)})

    @staticmethod
    def supported_architectures(path: Path) -> set[str]:
        """
        load supported architectures from package sources

        Args:
            path(Path): path to package sources directory

        Returns:
            set[str]: list of package supported architectures

        Raises:
            InvalidPackageInfo: if there are parsing errors
        """
        srcinfo_source = Package._check_output("makepkg", "--printsrcinfo", cwd=path)
        srcinfo, errors = parse_srcinfo(srcinfo_source)
        if errors:
            raise PackageInfoError(errors)
        return set(srcinfo.get("arch", []))

    def actual_version(self, paths: RepositoryPaths) -> str:
        """
        additional method to handle VCS package versions

        Args:
            paths(RepositoryPaths): repository paths instance

        Returns:
            str: package version if package is not VCS and current version according to VCS otherwise

        Raises:
            InvalidPackageInfo: if there are parsing errors
        """
        if not self.is_vcs:
            return self.version

        from ahriman.core.build_tools.sources import Sources

        Sources.load(paths.cache_for(self.base), self, [], paths)

        try:
            # update pkgver first
            Package._check_output("makepkg", "--nodeps", "--nobuild",
                                  cwd=paths.cache_for(self.base), logger=self.logger)
            # generate new .SRCINFO and put it to parser
            srcinfo_source = Package._check_output("makepkg", "--printsrcinfo",
                                                   cwd=paths.cache_for(self.base), logger=self.logger)
            srcinfo, errors = parse_srcinfo(srcinfo_source)
            if errors:
                raise PackageInfoError(errors)

            return full_version(srcinfo.get("epoch"), srcinfo["pkgver"], srcinfo["pkgrel"])
        except Exception:
            self.logger.exception("cannot determine version of VCS package, make sure that VCS tools are installed")

        return self.version

    def full_depends(self, pacman: Pacman, packages: Iterable[Package]) -> list[str]:
        """
        generate full dependencies list including transitive dependencies

        Args:
            pacman(Pacman): alpm wrapper instance
            packages(Iterable[Package]): repository package list

        Returns:
            list[str]: all dependencies of the package
        """
        dependencies = {}
        # load own package dependencies
        for package_base in packages:
            for name, repo_package in package_base.packages.items():
                dependencies[name] = repo_package.depends
                for provides in repo_package.provides:
                    dependencies[provides] = repo_package.depends
        # load repository dependencies
        for database in pacman.handle.get_syncdbs():
            for pacman_package in database.pkgcache:
                dependencies[pacman_package.name] = pacman_package.depends
                for provides in pacman_package.provides:
                    dependencies[provides] = pacman_package.depends

        result = set(self.depends)
        current_depends: set[str] = set()
        while result != current_depends:
            current_depends = copy.deepcopy(result)
            for package in current_depends:
                result.update(dependencies.get(package, []))

        return sorted(result)

    def is_newer_than(self, timestamp: float | int) -> bool:
        """
        check if package was built after the specified timestamp

        Args:
            timestamp(float | int): timestamp to check build date against

        Returns:
            bool: True in case if package was built after the specified date and False otherwise. In case if build date
                is not set by any of packages, it returns False
        """
        return any(
            package.build_date > timestamp
            for package in self.packages.values()
            if package.build_date is not None
        )

    def is_outdated(self, remote: Package, paths: RepositoryPaths, *,
                    vcs_allowed_age: float | int = 0,
                    calculate_version: bool = True) -> bool:
        """
        check if package is out-of-dated

        Args:
            remote(Package): package properties from remote source
            paths(RepositoryPaths): repository paths instance. Required for VCS packages cache
            vcs_allowed_age(float | int, optional): max age of the built packages before they will be
                forced to calculate actual version (Default value = 0)
            calculate_version(bool, optional): expand version to actual value (by calculating git versions)
                (Default value = True)

        Returns:
            bool: True if the package is out-of-dated and False otherwise
        """
        min_vcs_build_date = utcnow().timestamp() - vcs_allowed_age
        if calculate_version and not self.is_newer_than(min_vcs_build_date):
            remote_version = remote.actual_version(paths)
        else:
            remote_version = remote.version

        result: int = vercmp(self.version, remote_version)
        return result < 0

    def pretty_print(self) -> str:
        """
        generate pretty string representation

        Returns:
            str: print-friendly string
        """
        details = "" if self.is_single_package else f""" ({" ".join(sorted(self.packages.keys()))})"""
        return f"{self.base}{details}"

    def view(self) -> dict[str, Any]:
        """
        generate json package view

        Returns:
            dict[str, Any]: json-friendly dictionary
        """
        return asdict(self)
