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
import logging

from typing import Self

from ahriman.core.configuration import Configuration


class HttpLogHandler(logging.Handler):
    """
    handler for the http logging. Because default ``logging.handlers.HTTPHandler`` does not support cookies
    authorization, we have to implement own handler which overrides the ``logging.handlers.HTTPHandler.emit`` method

    Attributes:
        reporter(Client): build status reporter instance
        suppress_errors(bool): suppress logging errors (e.g. if no web server available)
    """

    def __init__(self, configuration: Configuration, *, report: bool, suppress_errors: bool) -> None:
        """
        default constructor

        Args:
            configuration(Configuration): configuration instance
            report(bool): force enable or disable reporting
            suppress_errors(bool): suppress logging errors (e.g. if no web server available)
        """
        # we don't really care about those parameters because they will be handled by the reporter
        logging.Handler.__init__(self)

        # client has to be imported here because of circular imports
        from ahriman.core.status.client import Client
        self.reporter = Client.load(configuration, report=report)
        self.suppress_errors = suppress_errors

    @classmethod
    def load(cls, configuration: Configuration, *, report: bool) -> Self:
        """
        install logger. This function creates handler instance and adds it to the handler list in case if no other
        http handler found

        Args:
            configuration(Configuration): configuration instance
            report(bool): force enable or disable reporting

        Returns:
            Self: logger instance with loaded settings
        """
        root = logging.getLogger()
        if (handler := next((handler for handler in root.handlers if isinstance(handler, cls)), None)) is not None:
            return handler  # there is already registered instance

        suppress_errors = configuration.getboolean("settings", "suppress_http_log_errors", fallback=False)
        handler = cls(configuration, report=report, suppress_errors=suppress_errors)
        root.addHandler(handler)

        return handler

    def emit(self, record: logging.LogRecord) -> None:
        """
        emit log records using reporter client

        Args:
            record(logging.LogRecord): log record to log
        """
        package_base = getattr(record, "package_base", None)
        if package_base is None:
            return  # in case if no package base supplied we need just skip log message

        try:
            self.reporter.logs(package_base, record)
        except Exception:
            if self.suppress_errors:
                return
            self.handleError(record)
