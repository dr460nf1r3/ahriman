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
import re

from aiohttp.web import AccessLogger, BaseRequest, StreamResponse


class FilteredAccessLogger(AccessLogger):
    """
    access logger implementation with log filter enabled

    Attributes:
        LOG_PATH_REGEX(re.Pattern): (class attribute) regex for logs uri
    """

    # official packages have only ``[A-Za-z0-9_.+-]`` regex
    LOG_PATH_REGEX = re.compile(r"^/api/v1/packages/[A-Za-z0-9_.+%-]+/logs$")

    @staticmethod
    def is_logs_post(request: BaseRequest) -> bool:
        """
        check if request looks lie logs posting

        Args:
            request(BaseRequest): http reqeust descriptor

        Returns:
            bool: True in case if request looks like logs positing and False otherwise
        """
        return request.method == "POST" and FilteredAccessLogger.LOG_PATH_REGEX.match(request.path) is not None

    def log(self, request: BaseRequest, response: StreamResponse, time: float) -> None:
        """
        access log with enabled filter by request path

        Args:
            request(BaseRequest): http reqeust descriptor
            response(StreamResponse): streaming response object
            time(float):
        """
        if self.is_logs_post(request):
            return
        AccessLogger.log(self, request, response, time)
