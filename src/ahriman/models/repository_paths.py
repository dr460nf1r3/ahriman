#
# Copyright (c) 2021 ahriman team.
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

import shutil

from dataclasses import dataclass
from pathlib import Path
from typing import Set, Type


@dataclass
class RepositoryPaths:
    """
    repository paths holder. For the most operations with paths you want to use this object
    :ivar root: repository root (i.e. ahriman home)
    :ivar architecture: repository architecture
    """

    root: Path
    architecture: str

    @property
    def cache(self) -> Path:
        """
        :return: directory for packages cache (mainly used for VCS packages)
        """
        return self.root / "cache"

    @property
    def chroot(self) -> Path:
        """
        :return: directory for devtools chroot
        """
        # for the chroot directory devtools will create own tree and we don"t have to specify architecture here
        return self.root / "chroot"

    @property
    def manual(self) -> Path:
        """
        :return: directory for manual updates (i.e. from add command)
        """
        return self.root / "manual" / self.architecture

    @property
    def packages(self) -> Path:
        """
        :return: directory for built packages
        """
        return self.root / "packages" / self.architecture

    @property
    def patches(self) -> Path:
        """
        :return: directory for source patches
        """
        return self.root / "patches"

    @property
    def repository(self) -> Path:
        """
        :return: repository directory
        """
        return self.root / "repository" / self.architecture

    @property
    def sources(self) -> Path:
        """
        :return: directory for downloaded PKGBUILDs for current build
        """
        return self.root / "sources" / self.architecture

    @classmethod
    def known_architectures(cls: Type[RepositoryPaths], root: Path) -> Set[str]:
        """
        get known architectures
        :param root: repository root
        :return: list of architectures for which tree is created
        """
        paths = cls(root, "")
        return {
            path.name
            for path in paths.repository.iterdir()
            if path.is_dir()
        }

    def cache_for(self, package_base: str) -> Path:
        """
        get path to cached PKGBUILD and package sources for the package base
        :param package_base: package base name
        :return: full path to directory for specified package base cache
        """
        return self.cache / package_base

    def manual_for(self, package_base: str) -> Path:
        """
        get manual path for specific package base
        :param package_base: package base name
        :return: full path to directory for specified package base manual updates
        """
        return self.manual / package_base

    def patches_for(self, package_base: str) -> Path:
        """
        get patches path for specific package base
        :param package_base: package base name
        :return: full path to directory for specified package base patches
        """
        return self.patches / package_base

    def sources_for(self, package_base: str) -> Path:
        """
        get path to directory from where build will start for the package base
        :param package_base: package base name
        :return: full path to directory for specified package base sources
        """
        return self.sources / package_base

    def tree_clear(self, package_base: str) -> None:
        """
        clear package specific files
        :param package_base: package base name
        """
        for directory in (
                self.cache_for(package_base),
                self.manual_for(package_base),
                self.patches_for(package_base),
                self.sources_for(package_base)):
            shutil.rmtree(directory, ignore_errors=True)

    def tree_create(self) -> None:
        """
        create ahriman working tree
        """
        for directory in (
                self.cache,
                self.chroot,
                self.manual,
                self.packages,
                self.patches,
                self.repository,
                self.sources):
            directory.mkdir(mode=0o755, parents=True, exist_ok=True)
