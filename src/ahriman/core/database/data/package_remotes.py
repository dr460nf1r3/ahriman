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
from sqlite3 import Connection

from ahriman.models.package_source import PackageSource
from ahriman.models.remote_source import RemoteSource
from ahriman.models.repository_paths import RepositoryPaths


__all__ = ["migrate_package_remotes"]


# pylint: disable=protected-access
def migrate_package_remotes(connection: Connection, paths: RepositoryPaths) -> None:
    """
    perform migration for package remote sources

    Args:
        connection(Connection): database connection
        paths(RepositoryPaths): repository paths instance
    """
    from ahriman.core.database.operations.package_operations import PackageOperations

    def insert_remote(base: str, remote: RemoteSource) -> None:
        connection.execute(
            """
            update package_bases set
            branch = :branch, git_url = :git_url, path = :path,
            web_url = :web_url, source = :source
            where package_base = :package_base
            """,
            dict(
                package_base=base,
                branch=remote.branch, git_url=remote.git_url, path=remote.path,
                web_url=remote.web_url, source=remote.source
            )
        )

    packages = PackageOperations._packages_get_select_package_bases(connection)
    for package_base, package in packages.items():
        local_cache = paths.cache_for(package_base)
        if local_cache.exists() and not package.is_vcs:
            continue  # skip packages which are not VCS and with local cache
        remote_source = RemoteSource.from_remote(PackageSource.AUR, package_base, "aur")
        if remote_source is None:
            continue  # should never happen
        insert_remote(package_base, remote_source)
