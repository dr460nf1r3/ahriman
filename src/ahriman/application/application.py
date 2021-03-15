#
# Copyright (c) 2021 Evgenii Alekseev.
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
import os
import shutil

from typing import Callable, Iterable, List, Optional, Set

from ahriman.core.build_tools.task import Task
from ahriman.core.configuration import Configuration
from ahriman.core.repository import Repository
from ahriman.core.tree import Tree
from ahriman.models.package import Package


class Application:
    '''
    base application class
    :ivar architecture: repository architecture
    :ivar config: configuration instance
    :ivar logger: application logger
    :ivar repository: repository instance
    '''

    def __init__(self, architecture: str, config: Configuration) -> None:
        '''
        default constructor
        :param architecture: repository architecture
        :param config: configuration instance
        '''
        self.logger = logging.getLogger('root')
        self.config = config
        self.architecture = architecture
        self.repository = Repository(architecture, config)

    def _known_packages(self) -> Set[str]:
        '''
        load packages from repository and pacman repositories
        :return: list of known packages
        '''
        known_packages: Set[str] = set()
        # local set
        for package in self.repository.packages():
            known_packages.update(package.packages.keys())
        known_packages.update(self.repository.pacman.all_packages())
        return known_packages

    def _finalize(self) -> None:
        '''
        generate report and sync to remote server
        '''
        self.report()
        self.sync()

    def get_updates(self, filter_packages: List[str], no_aur: bool, no_manual: bool, no_vcs: bool,
                    log_fn: Callable[[str], None]) -> List[Package]:
        '''
        get list of packages to run update process
        :param filter_packages: do not check every package just specified in the list
        :param no_aur: do not check for aur updates
        :param no_manual: do not check for manual updates
        :param no_vcs: do not check VCS packages
        :param log_fn: logger function to log updates
        :return: list of out-of-dated packages
        '''
        updates = []

        if not no_aur:
            updates.extend(self.repository.updates_aur(filter_packages, no_vcs))
        if not no_manual:
            updates.extend(self.repository.updates_manual())

        for package in updates:
            log_fn(f'{package.base} = {package.version}')

        return updates

    def add(self, names: Iterable[str], without_dependencies: bool) -> None:
        '''
        add packages for the next build
        :param names: list of package bases to add
        :param without_dependencies: if set, dependency check will be disabled
        '''
        known_packages = self._known_packages()

        def add_manual(name: str) -> str:
            package = Package.load(name, self.repository.pacman, self.config.get('alpm', 'aur_url'))
            path = os.path.join(self.repository.paths.manual, package.base)
            Task.fetch(path, package.git_url)
            return path

        def add_archive(src: str) -> None:
            dst = os.path.join(self.repository.paths.packages, os.path.basename(src))
            shutil.move(src, dst)

        def process_dependencies(path: str) -> None:
            if without_dependencies:
                return
            dependencies = Package.dependencies(path)
            self.add(dependencies.difference(known_packages), without_dependencies)

        def process_single(name: str) -> None:
            if not os.path.isfile(name):
                path = add_manual(name)
                process_dependencies(path)
            else:
                add_archive(name)

        for name in names:
            process_single(name)

    def clean(self) -> None:
        '''
        run all clean methods
        '''
        self.repository._clear_build()
        self.repository._clear_cache()
        self.repository._clear_chroot()
        self.repository._clear_manual()
        self.repository._clear_packages()

    def remove(self, names: Iterable[str]) -> None:
        '''
        remove packages from repository
        :param names: list of packages (either base or name) to remove
        '''
        self.repository.process_remove(names)
        self._finalize()

    def report(self, target: Optional[Iterable[str]] = None) -> None:
        '''
        generate report
        :param target: list of targets to run (e.g. html)
        '''
        targets = target or None
        self.repository.process_report(targets)

    def sync(self, target: Optional[Iterable[str]] = None) -> None:
        '''
        sync to remote server
        :param target: list of targets to run (e.g. s3)
        '''
        targets = target or None
        self.repository.process_sync(targets)

    def update(self, updates: Iterable[Package]) -> None:
        '''
        run package updates
        :param updates: list of packages to update
        '''
        def process_update(paths: Iterable[str]) -> None:
            self.repository.process_update(paths)
            self._finalize()

        # process built packages
        packages = self.repository.packages_built()
        process_update(packages)

        # process manual packages
        tree = Tree()
        tree.load(updates)
        for num, level in enumerate(tree.levels()):
            self.logger.info(f'processing level #{num} {[package.base for package in level]}')
            packages = self.repository.process_build(level)
            process_update(packages)
