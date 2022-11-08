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
from typing import Set

from ahriman.application.application.application_packages import ApplicationPackages
from ahriman.application.application.application_repository import ApplicationRepository
from ahriman.models.result import Result


class Application(ApplicationPackages, ApplicationRepository):
    """
    base application class

    Examples:
        This class groups ``Repository`` methods into specific method which process all supposed actions caused by
        underlying action. E.g.::

            >>> from ahriman.core.configuration import Configuration
            >>> from ahriman.models.package_source import PackageSource
            >>>
            >>> configuration = Configuration()
            >>> application = Application("x86_64", configuration, no_report=False, unsafe=False)
            >>> # add packages to build queue
            >>> application.add(["ahriman"], PackageSource.AUR, without_dependencies=False)
            >>>
            >>> # check for updates
            >>> updates = application.updates([], no_aur=False, no_local=False, no_manual=False, no_vcs=False, log_fn=print)
            >>> # updates for specified packages
            >>> application.update(updates)

        In case if specific actions or their order are required, the direct access to ``Repository`` must
        be used instead.
    """

    def _known_packages(self) -> Set[str]:
        """
        load packages from repository and pacman repositories

        Returns:
            Set[str]: list of known packages
        """
        known_packages: Set[str] = set()
        # local set
        for base in self.repository.packages():
            for package, properties in base.packages.items():
                known_packages.add(package)
                known_packages.update(properties.provides)
        known_packages.update(self.repository.pacman.packages())
        return known_packages

    def on_result(self, result: Result) -> None:
        """
        generate report and sync to remote server

        Args:
            result(Result): build result
        """
        packages = self.repository.packages()
        self.repository.triggers.on_result(result, packages)

    def on_start(self) -> None:
        """
        run triggers on start of the application
        """
        self.repository.triggers.on_start()

    def on_stop(self) -> None:
        """
        run triggers on stop of the application. Note, however, that in most cases this method should not be called
        directly as it will be called after on_start action
        """
        self.repository.triggers.on_stop()
