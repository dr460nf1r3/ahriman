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

from ahriman.application.handlers import Handler
from ahriman.core.configuration import Configuration
from ahriman.core.formatters import ConfigurationPathsPrinter, ConfigurationPrinter, StringPrinter


class Dump(Handler):
    """
    dump configuration handler
    """

    ALLOW_AUTO_ARCHITECTURE_RUN = False

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
        root, _ = configuration.check_loaded()
        ConfigurationPathsPrinter(root, configuration.includes).print(verbose=True, separator=" = ")

        # empty line
        StringPrinter("").print(verbose=False)

        dump = configuration.dump()
        for section, values in sorted(dump.items()):
            ConfigurationPrinter(section, values).print(verbose=not args.secure, separator=" = ")
