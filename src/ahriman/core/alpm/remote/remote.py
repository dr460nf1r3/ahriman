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
from ahriman import __version__
from ahriman.core.alpm.pacman import Pacman
from ahriman.core.log import LazyLogging
from ahriman.models.aur_package import AURPackage


class Remote(LazyLogging):
    """
    base class for remote package search

    Attributes:
        DEFAULT_USER_AGENT(str): (class attribute) default user agent

    Examples:
        These classes are designed to be used without instancing. In order to achieve it several class methods are
        provided: ``info``, ``multisearch`` and ``search``. Thus, the basic flow is the following::

            >>> from ahriman.core.alpm.remote import AUR, Official
            >>>
            >>> package = AUR.info("ahriman", pacman=pacman)
            >>> search_result = Official.multisearch("pacman", "manager", pacman=pacman)

        Differnece between ``search`` and ``multisearch`` is that ``search`` passes all arguments to underlying wrapper
        directly, whereas ``multisearch`` splits search one by one and finds intersection between search results.
    """

    DEFAULT_USER_AGENT = f"ahriman/{__version__}"

    @classmethod
    def info(cls, package_name: str, *, pacman: Pacman) -> AURPackage:
        """
        get package info by its name

        Args:
            package_name(str): package name to search
            pacman(Pacman): alpm wrapper instance

        Returns:
            AURPackage: package which match the package name
        """
        return cls().package_info(package_name, pacman=pacman)

    @classmethod
    def multisearch(cls, *keywords: str, pacman: Pacman) -> list[AURPackage]:
        """
        search in remote repository by using API with multiple words. This method is required in order to handle
        https://bugs.archlinux.org/task/49133. In addition, short words will be dropped

        Args:
            *keywords(str): search terms, e.g. "ahriman", "is", "cool"
            pacman(Pacman): alpm wrapper instance

        Returns:
            list[AURPackage]: list of packages each of them matches all search terms
        """
        instance = cls()
        packages: dict[str, AURPackage] = {}
        for term in filter(lambda word: len(word) >= 3, keywords):
            portion = instance.search(term, pacman=pacman)
            packages = {
                package.name: package  # not mistake to group them by name
                for package in portion
                if package.name in packages or not packages
            }
        return list(packages.values())

    @classmethod
    def remote_git_url(cls, package_base: str, repository: str) -> str:
        """
        generate remote git url from the package base

        Args
            package_base(str): package base
            repository(str): repository name

        Returns:
            str: git url for the specific base

        Raises:
            NotImplementedError: not implemented method
        """
        raise NotImplementedError

    @classmethod
    def remote_web_url(cls, package_base: str) -> str:
        """
        generate remote web url from the package base

        Args
            package_base(str): package base

        Returns:
            str: web url for the specific base

        Raises:
            NotImplementedError: not implemented method
        """
        raise NotImplementedError

    @classmethod
    def search(cls, *keywords: str, pacman: Pacman) -> list[AURPackage]:
        """
        search package in AUR web

        Args:
            *keywords(str): search terms, e.g. "ahriman", "is", "cool"
            pacman(Pacman): alpm wrapper instance

        Returns:
            list[AURPackage]: list of packages which match the criteria
        """
        return cls().package_search(*keywords, pacman=pacman)

    def package_info(self, package_name: str, *, pacman: Pacman) -> AURPackage:
        """
        get package info by its name

        Args:
            package_name(str): package name to search
            pacman(Pacman): alpm wrapper instance

        Returns:
            AURPackage: package which match the package name

        Raises:
            NotImplementedError: not implemented method
        """
        raise NotImplementedError

    def package_search(self, *keywords: str, pacman: Pacman) -> list[AURPackage]:
        """
        search package in AUR web

        Args:
            *keywords(str): keywords to search
            pacman(Pacman): alpm wrapper instance

        Returns:
            list[AURPackage]: list of packages which match the criteria

        Raises:
            NotImplementedError: not implemented method
        """
        raise NotImplementedError
