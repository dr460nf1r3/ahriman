#
# Copyright (c) 2021-2022 ahriman team.
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
import requests

from typing import Any, Dict, List, Type

from ahriman.core.alpm.pacman import Pacman
from ahriman.core.alpm.remote import Remote
from ahriman.core.exceptions import InvalidPackageInfo
from ahriman.core.util import exception_response_text
from ahriman.models.aur_package import AURPackage


class Official(Remote):
    """
    official repository RPC wrapper

    Attributes:
        DEFAULT_ARCHLINUX_URL(str): (class attribute) default archlinux url
        DEFAULT_SEARCH_REPOSITORIES(List[str]): (class attribute) default list of repositories to search
        DEFAULT_RPC_URL(str): (class attribute) default archlinux repositories RPC url
    """

    DEFAULT_ARCHLINUX_URL = "https://archlinux.org"
    DEFAULT_SEARCH_REPOSITORIES = ["Core", "Extra", "Multilib", "Community"]
    DEFAULT_RPC_URL = "https://archlinux.org/packages/search/json"

    @staticmethod
    def parse_response(response: Dict[str, Any]) -> List[AURPackage]:
        """
        parse RPC response to package list

        Args:
            response(Dict[str, Any]): RPC response json

        Returns:
            List[AURPackage]: list of parsed packages

        Raises:
            InvalidPackageInfo: for error API response
        """
        if not response["valid"]:
            raise InvalidPackageInfo("API validation error")
        return [AURPackage.from_repo(package) for package in response["results"]]

    @classmethod
    def remote_git_url(cls: Type[Remote], package_base: str, repository: str) -> str:
        """
        generate remote git url from the package base

        Args
            package_base(str): package base
            repository(str): repository name

        Returns:
            str: git url for the specific base
        """
        if repository.lower() in ("core", "extra", "testing", "kde-unstable"):
            return "https://github.com/archlinux/svntogit-packages.git"  # hardcoded, ok
        return "https://github.com/archlinux/svntogit-community.git"

    @classmethod
    def remote_web_url(cls: Type[Remote], package_base: str) -> str:
        """
        generate remote web url from the package base

        Args
            package_base(str): package base

        Returns:
            str: web url for the specific base
        """
        return f"{Official.DEFAULT_ARCHLINUX_URL}/packages/{package_base}"

    def make_request(self, *args: str, by: str) -> List[AURPackage]:
        """
        perform request to official repositories RPC

        Args:
            *args(str): list of arguments to be passed as args query parameter
            by(str): search by the field

        Returns:
            List[AURPackage]: response parsed to package list
        """
        try:
            response = requests.get(self.DEFAULT_RPC_URL, params={by: args, "repo": self.DEFAULT_SEARCH_REPOSITORIES})
            response.raise_for_status()
            return self.parse_response(response.json())
        except requests.HTTPError as e:
            self.logger.exception("could not perform request: %s", exception_response_text(e))
            raise
        except Exception:
            self.logger.exception("could not perform request")
            raise

    def package_info(self, package_name: str, *, pacman: Pacman) -> AURPackage:
        """
        get package info by its name

        Args:
            package_name(str): package name to search
            pacman(Pacman): alpm wrapper instance

        Returns:
            AURPackage: package which match the package name
        """
        packages = self.make_request(package_name, by="name")
        return next(package for package in packages if package.name == package_name)

    def package_search(self, *keywords: str, pacman: Pacman) -> List[AURPackage]:
        """
        search package in AUR web

        Args:
            *keywords(str): keywords to search
            pacman(Pacman): alpm wrapper instance

        Returns:
            List[AURPackage]: list of packages which match the criteria
        """
        return self.make_request(*keywords, by="q")