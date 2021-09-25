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
from aiohttp.web import HTTPNoContent, HTTPNotFound, Response, json_response

from ahriman.core.exceptions import UnknownPackage
from ahriman.models.build_status import BuildStatusEnum
from ahriman.models.package import Package
from ahriman.models.user_access import UserAccess
from ahriman.web.views.base import BaseView


class PackageView(BaseView):
    """
    package base specific web view
    :cvar DELETE_PERMISSION: delete permissions of self
    :cvar GET_PERMISSION: get permissions of self
    :cvar HEAD_PERMISSION: head permissions of self
    :cvar POST_PERMISSION: post permissions of self
    """

    DELETE_PERMISSION = POST_PERMISSION = UserAccess.Write
    GET_PERMISSION = HEAD_PERMISSION = UserAccess.Read

    async def get(self) -> Response:
        """
        get current package base status
        :return: 200 with package description on success
        """
        base = self.request.match_info["package"]

        try:
            package, status = self.service.get(base)
        except UnknownPackage:
            raise HTTPNotFound()

        response = [
            {
                "package": package.view(),
                "status": status.view()
            }
        ]
        return json_response(response)

    async def delete(self) -> Response:
        """
        delete package base from status page
        :return: 204 on success
        """
        base = self.request.match_info["package"]
        self.service.remove(base)

        raise HTTPNoContent()

    async def post(self) -> Response:
        """
        update package build status

        JSON body must be supplied, the following model is used:
        {
            "status": "unknown",   # package build status string, must be valid `BuildStatusEnum`
            "package": {}  # package body (use `dataclasses.asdict` to generate one), optional.
                           # Must be supplied in case if package base is unknown
        }

        :return: 204 on success
        """
        base = self.request.match_info["package"]
        data = await self.extract_data()

        try:
            package = Package.from_json(data["package"]) if "package" in data else None
            status = BuildStatusEnum(data["status"])
        except Exception as e:
            return json_response(data=str(e), status=400)

        try:
            self.service.update(base, status, package)
        except UnknownPackage:
            return json_response(data=f"Package {base} is unknown, but no package body set", status=400)

        raise HTTPNoContent()
