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
import aur  # type: ignore

from aiohttp.web import Response, json_response
from typing import Callable, Iterator

from ahriman.web.views.base import BaseView


class SearchView(BaseView):
    """
    AUR search web view
    """

    async def get(self) -> Response:
        """
        search packages in AUR

        search string (non empty) must be supplied as `for` parameter

        :return: 200 with found package bases and descriptions sorted by base
        """
        search: Iterator[str] = filter(lambda s: len(s) > 3, self.request.query.getall("for", default=[]))
        search_string = " ".join(search)

        if not search_string:
            return json_response(data="Search string must not be empty", status=400)
        packages = aur.search(search_string)

        comparator: Callable[[aur.Package], str] = lambda item: str(item.package_base)
        response = [
            {
                "package": package.package_base,
                "description": package.description,
            } for package in sorted(packages, key=comparator)
        ]
        return json_response(response)
