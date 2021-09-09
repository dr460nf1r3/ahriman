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
from aiohttp.web import HTTPFound, Response, json_response

from ahriman.web.views.base import BaseView


class AddView(BaseView):
    """
    add package web view
    """

    async def post(self) -> Response:
        """
        add new package

        JSON body must be supplied, the following model is used:
        {
            "packages": "ahriman",   # either list of packages or package name as in AUR
            "build_now": true       # optional flag which runs build
        }

        :return: redirect to main page on success
        """
        data = await self.extract_data(["packages"])

        try:
            now = data.get("build_now", True)
            packages = data["packages"]
        except Exception as e:
            return json_response(text=str(e), status=400)

        self.spawner.packages_add(packages, now)

        return HTTPFound("/")
