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
from ahriman.core.formatters import StringPrinter
from ahriman.models.build_status import BuildStatus


class StatusPrinter(StringPrinter):
    """
    print content of the status object
    """

    def __init__(self, status: BuildStatus) -> None:
        """
        default constructor

        Args:
            status(BuildStatus): build status
        """
        StringPrinter.__init__(self, status.pretty_print())
