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
from __future__ import annotations

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules
from sqlite3 import Connection
from typing import List, Type

from ahriman.core.configuration import Configuration
from ahriman.core.database.data import migrate_data
from ahriman.core.lazy_logging import LazyLogging
from ahriman.models.migration import Migration
from ahriman.models.migration_result import MigrationResult


class Migrations(LazyLogging):
    """
    simple migration wrapper for the sqlite
    idea comes from https://www.ash.dev/blog/simple-migration-system-in-sqlite/

    Attributes:
        configuration(Configuration): configuration instance
        connection(Connection): database connection
    """

    def __init__(self, connection: Connection, configuration: Configuration) -> None:
        """
        default constructor

        Args:
            connection(Connection): database connection
            configuration(Configuration): configuration instance
        """
        self.connection = connection
        self.configuration = configuration

    @classmethod
    def migrate(cls: Type[Migrations], connection: Connection, configuration: Configuration) -> MigrationResult:
        """
        perform migrations implicitly

        Args:
            connection(Connection): database connection
            configuration(Configuration): configuration instance

        Returns:
            MigrationResult: current schema version
        """
        return cls(connection, configuration).run()

    def migrations(self) -> List[Migration]:
        """
        extract all migrations from the current package
        idea comes from https://julienharbulot.com/python-dynamical-import.html

        Returns:
            List[Migration]: list of found migrations
        """
        migrations: List[Migration] = []
        package_dir = Path(__file__).resolve().parent
        modules = [module_name for (_, module_name, _) in iter_modules([str(package_dir)])]

        for index, module_name in enumerate(sorted(modules)):
            module = import_module(f"{__name__}.{module_name}")
            steps: List[str] = getattr(module, "steps", [])
            self.logger.debug("found migration %s at index %s with steps count %s", module_name, index, len(steps))
            migrations.append(Migration(index, module_name, steps))

        return migrations

    def run(self) -> MigrationResult:
        """
        perform migrations

        Return:
            MigrationResult: current schema version
        """
        migrations = self.migrations()
        current_version = self.user_version()
        expected_version = len(migrations)
        result = MigrationResult(current_version, expected_version)

        if not result.is_outdated:
            self.logger.info("no migrations required")
            return result

        previous_isolation = self.connection.isolation_level
        try:
            self.connection.isolation_level = None
            cursor = self.connection.cursor()
            try:
                cursor.execute("begin exclusive")
                for migration in migrations[current_version:]:
                    self.logger.info("applying migration %s at index %s", migration.name, migration.index)
                    for statement in migration.steps:
                        cursor.execute(statement)
                    self.logger.info("migration %s at index %s has been applied", migration.name, migration.index)

                migrate_data(result, self.connection, self.configuration)

                cursor.execute(f"pragma user_version = {expected_version}")  # no support for ? placeholders
            except Exception:
                self.logger.exception("migration failed with exception")
                cursor.execute("rollback")
                raise
            else:
                cursor.execute("commit")
            finally:
                cursor.close()
        finally:
            self.connection.isolation_level = previous_isolation

        self.logger.info("migrations have been performed from version %s to %s", result.old_version, result.new_version)
        return result

    def user_version(self) -> int:
        """
        get schema version from sqlite database

        Returns:
            int: current schema version
        """
        cursor = self.connection.execute("pragma user_version")
        current_version: int = cursor.fetchone()["user_version"]
        return current_version
