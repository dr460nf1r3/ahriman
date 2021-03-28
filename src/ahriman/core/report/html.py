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
import jinja2

from typing import Callable, Dict, Iterable

from ahriman.core.configuration import Configuration
from ahriman.core.report.report import Report
from ahriman.core.util import pretty_size, pretty_datetime
from ahriman.models.package import Package
from ahriman.models.sign_settings import SignSettings


class HTML(Report):
    """
    html report generator

    It uses jinja2 templates for report generation, the following variables are allowed:

        homepage - link to homepage, string, optional
        link_path - prefix fo packages to download, string, required
        has_package_signed - True in case if package sign enabled, False otherwise, required
        has_repo_signed - True in case if repository database sign enabled, False otherwise, required
        packages - sorted list of packages properties: archive_size, build_date, filename, installed_size, name, version. Required
        pgp_key - default PGP key ID, string, optional
        repository - repository name, string, required

    :ivar homepage: homepage link if any (for footer)
    :ivar link_path: prefix fo packages to download
    :ivar name: repository name
    :ivar pgp_key: default PGP key
    :ivar report_path: output path to html report
    :ivar sign_targets: targets to sign enabled in configuration
    :ivar tempate_path: path to directory with jinja templates
    """

    def __init__(self, architecture: str, config: Configuration) -> None:
        """
        default constructor
        :param architecture: repository architecture
        :param config: configuration instance
        """
        Report.__init__(self, architecture, config)
        section = config.get_section_name("html", architecture)
        self.report_path = config.getpath(section, "path")
        self.link_path = config.get(section, "link_path")
        self.template_path = config.getpath(section, "template_path")

        # base template vars
        self.homepage = config.get(section, "homepage", fallback=None)
        self.name = config.get("repository", "name")

        sign_section = config.get_section_name("sign", architecture)
        self.sign_targets = [SignSettings.from_option(opt) for opt in config.getlist(sign_section, "target")]
        self.pgp_key = config.get(sign_section, "key") if self.sign_targets else None

    def generate(self, packages: Iterable[Package]) -> None:
        """
        generate report for the specified packages
        :param packages: list of packages to generate report
        """
        # idea comes from https://stackoverflow.com/a/38642558
        loader = jinja2.FileSystemLoader(searchpath=self.template_path.parent)
        environment = jinja2.Environment(loader=loader)
        template = environment.get_template(self.template_path.name)

        content = [
            {
                "archive_size": pretty_size(properties.archive_size),
                "build_date": pretty_datetime(properties.build_date),
                "filename": properties.filename,
                "installed_size": pretty_size(properties.installed_size),
                "name": package,
                "version": base.version
            } for base in packages for package, properties in base.packages.items()
        ]
        comparator: Callable[[Dict[str, str]], str] = lambda item: item["filename"]

        html = template.render(
            homepage=self.homepage,
            link_path=self.link_path,
            has_package_signed=SignSettings.SignPackages in self.sign_targets,
            has_repo_signed=SignSettings.SignRepository in self.sign_targets,
            packages=sorted(content, key=comparator),
            pgp_key=self.pgp_key,
            repository=self.name)

        self.report_path.write_text(html)
