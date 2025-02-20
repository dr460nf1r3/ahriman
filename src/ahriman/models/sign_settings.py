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
from __future__ import annotations

from enum import Enum


class SignSettings(str, Enum):
    """
    sign targets enumeration

    Attributes:
        Disabled(SignSettings): (class attribute) option which generates no report for testing purpose
        Packages(SignSettings): (class attribute) sign each package
        Repository(SignSettings): (class attribute) sign repository database file
    """

    Disabled = "disabled"
    Packages = "packages"
    Repository = "repository"

    @staticmethod
    def from_option(value: str) -> SignSettings:
        """
        construct value from configuration

        Args:
            value(str): configuration value

        Returns:
            SignSettings: parsed value
        """
        if value.lower() in ("package", "packages", "sign-package"):
            return SignSettings.Packages
        if value.lower() in ("repository", "sign-repository"):
            return SignSettings.Repository
        return SignSettings.Disabled
