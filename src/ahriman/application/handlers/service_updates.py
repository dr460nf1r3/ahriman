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
import argparse

from ahriman import __version__
from ahriman.application.application import Application
from ahriman.application.handlers import Handler
from ahriman.core.configuration import Configuration
from ahriman.core.formatters import UpdatePrinter
from ahriman.models.package import Package


class ServiceUpdates(Handler):
    """
    service updates handler
    """

    ALLOW_AUTO_ARCHITECTURE_RUN = False  # it should be called only as "no-architecture"

    @classmethod
    def run(cls, args: argparse.Namespace, architecture: str, configuration: Configuration, *, report: bool) -> None:
        """
        callback for command line

        Args:
            args(argparse.Namespace): command line args
            architecture(str): repository architecture
            configuration(Configuration): configuration instance
            report(bool): force enable or disable reporting
        """
        application = Application(architecture, configuration, report=report)

        remote = Package.from_aur("ahriman", application.repository.pacman, None)
        release = remote.version.rsplit("-", 1)[-1]  # we don't store pkgrel locally, so we just append it
        local_version = f"{__version__}-{release}"

        # technically we would like to compare versions, but it is fine to raise an exception in case if locally
        # installed package is newer than in AUR
        same_version = remote.version == local_version
        if same_version:
            return

        UpdatePrinter(remote, local_version).print(verbose=True, separator=" -> ")
        ServiceUpdates.check_if_empty(args.exit_code, not same_version)
