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
from typing import Iterable

from ahriman.core.configuration import Configuration
from ahriman.core.report.jinja_template import JinjaTemplate
from ahriman.core.report.report import Report
from ahriman.models.package import Package
from ahriman.models.result import Result


class HTML(Report, JinjaTemplate):
    """
    html report generator
    :ivar report_path: output path to html report
    :ivar template_path: path to template for full package list
    """

    def __init__(self, architecture: str, configuration: Configuration, section: str) -> None:
        """
        default constructor
        :param architecture: repository architecture
        :param configuration: configuration instance
        :param section: settings section name
        """
        Report.__init__(self, architecture, configuration)
        JinjaTemplate.__init__(self, section, configuration)

        self.report_path = configuration.getpath(section, "path")
        self.template_path = configuration.getpath(section, "template_path")

    def generate(self, packages: Iterable[Package], result: Result) -> None:
        """
        generate report for the specified packages
        :param packages: list of packages to generate report
        :param result: build result
        """
        html = self.make_html(Result(success=packages), self.template_path)
        self.report_path.write_text(html)
