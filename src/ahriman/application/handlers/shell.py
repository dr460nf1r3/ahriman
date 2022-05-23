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
import argparse
import code
import sys

from pathlib import Path
from typing import Type

from ahriman.application.application import Application
from ahriman.application.handlers import Handler
from ahriman.core.configuration import Configuration
from ahriman.core.formatters import StringPrinter


class Shell(Handler):
    """
    python shell handler
    """

    ALLOW_MULTI_ARCHITECTURE_RUN = False

    @classmethod
    def run(cls: Type[Handler], args: argparse.Namespace, architecture: str,
            configuration: Configuration, no_report: bool, unsafe: bool) -> None:
        """
        callback for command line

        Args:
            args(argparse.Namespace): command line args
            architecture(str): repository architecture
            configuration(Configuration): configuration instance
            no_report(bool): force disable reporting
            unsafe(bool): if set no user check will be performed before path creation
        """
        # pylint: disable=possibly-unused-variable
        application = Application(architecture, configuration, no_report, unsafe)
        if args.verbose:
            # licensed by https://creativecommons.org/licenses/by-sa/3.0
            path = Path(sys.prefix) / "share" / "ahriman" / "templates" / "shell"
            StringPrinter(path.read_text(encoding="utf8")).print(verbose=False)
        code.interact(local=locals())
