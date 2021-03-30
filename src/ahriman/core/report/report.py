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
import logging

from typing import Iterable

from ahriman.core.configuration import Configuration
from ahriman.core.exceptions import ReportFailed
from ahriman.models.package import Package
from ahriman.models.report_settings import ReportSettings


class Report:
    """
    base report generator
    :ivar architecture: repository architecture
    :ivar configuration: configuration instance
    :ivar logger: class logger
    """

    def __init__(self, architecture: str, configuration: Configuration) -> None:
        """
        default constructor
        :param architecture: repository architecture
        :param configuration: configuration instance
        """
        self.logger = logging.getLogger("builder")
        self.architecture = architecture
        self.configuration = configuration

    @staticmethod
    def run(architecture: str, configuration: Configuration, target: str, packages: Iterable[Package]) -> None:
        """
        run report generation
        :param architecture: repository architecture
        :param configuration: configuration instance
        :param target: target to generate report (e.g. html)
        :param packages: list of packages to generate report
        """
        provider = ReportSettings.from_option(target)
        if provider == ReportSettings.HTML:
            from ahriman.core.report.html import HTML
            report: Report = HTML(architecture, configuration)
        else:
            report = Report(architecture, configuration)

        try:
            report.generate(packages)
        except Exception:
            report.logger.exception(f"report generation failed for target {provider.name}")
            raise ReportFailed()

    def generate(self, packages: Iterable[Package]) -> None:
        """
        generate report for the specified packages
        :param packages: list of packages to generate report
        """
