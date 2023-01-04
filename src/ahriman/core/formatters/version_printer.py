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
from typing import Dict, List

from ahriman.core.formatters import StringPrinter
from ahriman.models.property import Property


class VersionPrinter(StringPrinter):
    """
    print content of the python package versions

    Attributes:
        packages(Dict[str, str]): map of package name to its version
    """

    def __init__(self, title: str, packages: Dict[str, str]) -> None:
        """
        default constructor

        Args:
            title(str): title of the message
            packages(Dict[str, str]): map of package name to its version
        """
        StringPrinter.__init__(self, title)
        self.packages = packages

    def properties(self) -> List[Property]:
        """
        convert content into printable data

        Returns:
            List[Property]: list of content properties
        """
        return [
            Property(package, version, is_required=True)
            for package, version in sorted(self.packages.items())
        ]
