#
# Copyright (c) 2021 Evgenii Alekseev.
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
from __future__ import annotations

import aur  # type: ignore
import logging
import os

from dataclasses import asdict, dataclass
from pyalpm import vercmp  # type: ignore
from srcinfo.parse import parse_srcinfo  # type: ignore
from typing import Any, Dict, List, Optional, Set, Type

from ahriman.core.alpm.pacman import Pacman
from ahriman.core.exceptions import InvalidPackageInfo
from ahriman.core.util import check_output
from ahriman.models.package_desciption import PackageDescription
from ahriman.models.repository_paths import RepositoryPaths


@dataclass
class Package:
    '''
    package properties representation
    :ivar aurl_url: AUR root url
    :ivar base: package base name
    :ivar packages: map of package names to their properties. Filled only on load from archive
    :ivar version: package full version
    '''

    base: str
    version: str
    aur_url: str
    packages: Dict[str, PackageDescription]

    @property
    def git_url(self) -> str:
        '''
        :return: package git url to clone
        '''
        return f'{self.aur_url}/{self.base}.git'

    @property
    def is_vcs(self) -> bool:
        '''
        :return: True in case if package base looks like VCS package and false otherwise
        '''
        return self.base.endswith('-bzr') \
            or self.base.endswith('-csv')\
            or self.base.endswith('-darcs')\
            or self.base.endswith('-git')\
            or self.base.endswith('-hg')\
            or self.base.endswith('-svn')

    @property
    def web_url(self) -> str:
        '''
        :return: package AUR url
        '''
        return f'{self.aur_url}/packages/{self.base}'

    @classmethod
    def from_archive(cls: Type[Package], path: str, pacman: Pacman, aur_url: str) -> Package:
        '''
        construct package properties from package archive
        :param path: path to package archive
        :param pacman: alpm wrapper instance
        :param aur_url: AUR root url
        :return: package properties
        '''
        package = pacman.handle.load_pkg(path)
        properties = PackageDescription(package.size, package.builddate, os.path.basename(path), package.isize)
        return cls(package.base, package.version, aur_url, {package.name: properties})

    @classmethod
    def from_aur(cls: Type[Package], name: str, aur_url: str) -> Package:
        '''
        construct package properties from AUR page
        :param name: package name (either base or normal name)
        :param aur_url: AUR root url
        :return: package properties
        '''
        package = aur.info(name)
        return cls(package.package_base, package.version, aur_url, {package.name: PackageDescription()})

    @classmethod
    def from_build(cls: Type[Package], path: str, aur_url: str) -> Package:
        '''
        construct package properties from sources directory
        :param path: path to package sources directory
        :param aur_url: AUR root url
        :return: package properties
        '''
        with open(os.path.join(path, '.SRCINFO')) as srcinfo_file:
            srcinfo, errors = parse_srcinfo(srcinfo_file.read())
        if errors:
            raise InvalidPackageInfo(errors)
        packages = {key: PackageDescription() for key in srcinfo['packages']}
        version = cls.full_version(srcinfo.get('epoch'), srcinfo['pkgver'], srcinfo['pkgrel'])

        return cls(srcinfo['pkgbase'], version, aur_url, packages)

    @classmethod
    def from_json(cls: Type[Package], dump: Dict[str, Any]) -> Package:
        '''
        construct package properties from json dump
        :param dump: json dump body
        :return: package properties
        '''
        packages = {
            key: PackageDescription(**value)
            for key, value in dump.get('packages', {})
        }
        return Package(
            base=dump['base'],
            version=dump['version'],
            aur_url=dump['aur_url'],
            packages=packages)

    @staticmethod
    def dependencies(path: str) -> Set[str]:
        '''
        load dependencies from package sources
        :param path: path to package sources directory
        :return: list of package dependencies including makedepends array, but excluding packages from this base
        '''
        with open(os.path.join(path, '.SRCINFO')) as srcinfo_file:
            srcinfo, errors = parse_srcinfo(srcinfo_file.read())
        if errors:
            raise InvalidPackageInfo(errors)
        makedepends = srcinfo.get('makedepends', [])
        # sum over each package
        depends: List[str] = srcinfo.get('depends', [])
        for package in srcinfo['packages'].values():
            depends.extend(package.get('depends', []))
        # we are not interested in dependencies inside pkgbase
        packages = set(srcinfo['packages'].keys())
        return set(depends + makedepends) - packages

    @staticmethod
    def full_version(epoch: Optional[str], pkgver: str, pkgrel: str) -> str:
        '''
        generate full version from components
        :param epoch: package epoch if any
        :param pkgver: package version
        :param pkgrel: package release version (archlinux specific)
        :return: generated version
        '''
        prefix = f'{epoch}:' if epoch else ''
        return f'{prefix}{pkgver}-{pkgrel}'

    @staticmethod
    def load(path: str, pacman: Pacman, aur_url: str) -> Package:
        '''
        package constructor from available sources
        :param path: one of path to sources directory, path to archive or package name/base
        :param pacman: alpm wrapper instance (required to load from archive)
        :param aur_url: AUR root url
        :return: package properties
        '''
        try:
            if os.path.isdir(path):
                package: Package = Package.from_build(path, aur_url)
            elif os.path.exists(path):
                package = Package.from_archive(path, pacman, aur_url)
            else:
                package = Package.from_aur(path, aur_url)
            return package
        except InvalidPackageInfo:
            raise
        except Exception as e:
            raise InvalidPackageInfo(str(e))

    def actual_version(self, paths: RepositoryPaths) -> str:
        '''
        additional method to handle VCS package versions
        :param paths: repository paths instance
        :return: package version if package is not VCS and current version according to VCS otherwise
        '''
        if not self.is_vcs:
            return self.version

        from ahriman.core.build_tools.task import Task

        clone_dir = os.path.join(paths.cache, self.base)
        logger = logging.getLogger('build_details')
        Task.fetch(clone_dir, self.git_url)

        # update pkgver first
        check_output('makepkg', '--nodeps', '--nobuild', exception=None, cwd=clone_dir, logger=logger)
        # generate new .SRCINFO and put it to parser
        srcinfo_source = check_output('makepkg', '--printsrcinfo', exception=None, cwd=clone_dir, logger=logger)
        srcinfo, errors = parse_srcinfo(srcinfo_source)
        if errors:
            raise InvalidPackageInfo(errors)

        return self.full_version(srcinfo.get('epoch'), srcinfo['pkgver'], srcinfo['pkgrel'])

    def is_outdated(self, remote: Package, paths: RepositoryPaths) -> bool:
        '''
        check if package is out-of-dated
        :param remote: package properties from remote source
        :param paths: repository paths instance. Required for VCS packages cache
        :return: True if the package is out-of-dated and False otherwise
        '''
        remote_version = remote.actual_version(paths)  # either normal version or updated VCS
        result: int = vercmp(self.version, remote_version)
        return result < 0

    def view(self) -> Dict[str, Any]:
        '''
        generate json package view
        :return: json-friendly dictionary
        '''
        return asdict(self)
